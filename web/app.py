"""MiniLang 编译器 Web 服务。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, render_template, request

from compiler import Compiler
from compiler.runtime import OUTPUT_DIR, WORKSPACE, ensure_dirs, reset_handlers, set_input_handler, set_write_handler

EXAMPLES_DIR = ROOT / "examples"
WORKSPACE_FILE = WORKSPACE / "main.ml"

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
# 开发时始终从磁盘读取模板/静态文件，避免旧进程缓存旧页面
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/workspace", methods=["GET", "POST"])
def workspace_api():
    ensure_dirs()
    if request.method == "GET":
        source = WORKSPACE_FILE.read_text(encoding="utf-8") if WORKSPACE_FILE.exists() else ""
        return jsonify({"source": source, "path": str(WORKSPACE_FILE)})
    data = request.get_json(force=True) or {}
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    WORKSPACE_FILE.write_text(data.get("source", ""), encoding="utf-8")
    return jsonify({"ok": True, "path": str(WORKSPACE_FILE)})


@app.route("/api/examples")
def list_examples():
    examples = [{"name": "（空白）", "source": ""}]
    if EXAMPLES_DIR.exists():
        for p in sorted(EXAMPLES_DIR.glob("*.ml")):
            examples.append({"name": p.stem, "source": p.read_text(encoding="utf-8")})
    return jsonify(examples)


def _run_with_inputs(code: str, inputs: list[str]) -> str:
    import io

    queue = list(inputs)
    write_log: list[str] = []

    def input_handler(prompt: str) -> str:
        if queue:
            return queue.pop(0)
        return ""

    def write_handler(path, content: str) -> None:
        write_log.append(f"[已写入] {path}\n  内容: {content}")

    reset_handlers()
    set_input_handler(input_handler)
    set_write_handler(write_handler)
    try:
        output = Compiler._run_target(code)
        if write_log:
            output += "\n" + "\n".join(write_log)
        return output
    finally:
        reset_handlers()


@app.route("/api/compile", methods=["POST"])
def compile_source():
    data = request.get_json(force=True) or {}
    source = data.get("source", "")
    optimize = data.get("optimize", True)
    run = data.get("run", False)
    inputs = data.get("inputs") or []

    result = Compiler().compile(source, optimize=optimize, run=False)
    if run and result.success and result.target_code:
        result.run_output = _run_with_inputs(result.target_code, inputs)
        py_path = WORKSPACE_FILE.with_suffix(".py")
        ensure_dirs()
        py_path.write_text(result.target_code, encoding="utf-8")

    return jsonify(result.to_dict())


@app.route("/api/output-dir")
def output_dir():
    ensure_dirs()
    files = []
    if OUTPUT_DIR.exists():
        for p in sorted(OUTPUT_DIR.iterdir()):
            if p.is_file():
                files.append({"name": p.name, "content": p.read_text(encoding="utf-8")})
    return jsonify({"dir": str(OUTPUT_DIR), "files": files})


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MiniLang 编译器 Web 界面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    ensure_dirs()
    print(f"MiniLang IDE Web: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
