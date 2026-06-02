const editor = CodeMirror.fromTextArea(document.getElementById("sourceEditor"), {
  mode: "text/x-csrc",
  theme: "material-darker",
  lineNumbers: true,
  indentUnit: 4,
  tabSize: 4,
  lineWrapping: true,
});

const exampleSelect = document.getElementById("exampleSelect");
const compileBtn = document.getElementById("compileBtn");
const runBtn = document.getElementById("runBtn");
const saveBtn = document.getElementById("saveBtn");
const newBtn = document.getElementById("newBtn");
const errorList = document.getElementById("errorList");
const outputArea = document.getElementById("outputArea");
const diagSummary = document.getElementById("diagSummary");
const cursorPos = document.getElementById("cursorPos");
const stdinInput = document.getElementById("stdinInput");

let lastResult = null;
let activeTab = "run";
let outputFiles = null;

const tabDataKeys = {
  tokens: (r) => formatTokens(r.tokens),
  ast: (r) => r.ast || "(无 AST)",
  tac: (r) => formatLines(r.tac, "(无中间代码)"),
  opt: (r) => formatLines(r.optimized_tac, "(无优化结果)"),
  code: (r) => r.target_code || "(未生成目标代码)",
  run: (r) => r.run_output || (r.success ? "(无输出)" : "(编译失败，无法运行)"),
  stages: (r) => formatStages(r),
  files: () => formatOutputFiles(),
};

function formatTokens(tokens) {
  if (!tokens || !tokens.length) return "(无 Token)";
  return tokens
    .map((t) => `${String(t.line).padStart(3)}:${String(t.col).padStart(3)}  ${t.kind.padEnd(10)} ${t.value}`)
    .join("\n");
}

function formatLines(lines, empty) {
  if (!lines || !lines.length) return empty;
  return lines.map((l, i) => `${String(i + 1).padStart(3)}. ${l}`).join("\n");
}

function formatStages(r) {
  const lines = [
    `编译${r.success ? "成功" : "失败"} — ${r.error_count} 错误, ${r.warning_count} 警告`,
    "",
    "已完成阶段:",
    ...(r.stages_completed || []).map((s) => `  ✓ ${s}`),
  ];
  return lines.join("\n");
}

function formatOutputFiles() {
  if (!outputFiles) return "加载中…";
  if (!outputFiles.files.length) return `(目录为空)\n${outputFiles.dir}`;
  return outputFiles.files
    .map((f) => `--- ${f.name} ---\n${f.content}`)
    .join("\n\n");
}

function parseStdinLines() {
  return stdinInput.value.split(/\r?\n/).filter((l) => l.length > 0);
}

function renderDiagnostics(errors, warnings) {
  errorList.innerHTML = "";
  const all = [
    ...(errors || []).map((e) => ({ ...e, kind: "error" })),
    ...(warnings || []).map((w) => ({ ...w, kind: "warning" })),
  ].sort((a, b) => (a.line - b.line) || (a.col - b.col));

  if (!all.length) {
    errorList.innerHTML =
      '<div class="diag-item" style="border-left-color:var(--ok);background:rgba(63,185,80,.1)">未发现错误或警告</div>';
    return;
  }

  all.forEach((d) => {
    const el = document.createElement("div");
    el.className = `diag-item ${d.kind}`;
    const loc = d.line ? `L${d.line}${d.col ? `:C${d.col}` : ""}` : "—";
    el.innerHTML = `
      <div class="diag-meta">
        <span class="badge ${d.kind === "error" ? "error" : "warn"}">${d.kind === "error" ? "错误" : "警告"}</span>
        <span class="badge stage">${escapeHtml(d.stage)}</span>
        ${d.code ? `<span class="badge code">${escapeHtml(d.code)}</span>` : ""}
        <span class="muted">${loc}</span>
      </div>
      <div class="diag-msg">${escapeHtml(d.message)}</div>`;
    if (d.line) {
      el.addEventListener("click", () => {
        editor.setCursor(d.line - 1, Math.max(0, (d.col || 1) - 1));
        editor.focus();
      });
    }
    errorList.appendChild(el);
  });
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function showTab(name) {
  activeTab = name;
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === name);
  });
  if (name === "files") {
    loadOutputFiles().then(() => {
      outputArea.textContent = formatOutputFiles();
    });
    return;
  }
  if (lastResult && tabDataKeys[name]) {
    outputArea.textContent = tabDataKeys[name](lastResult);
  }
}

async function loadWorkspace() {
  const res = await fetch("/api/workspace");
  const data = await res.json();
  editor.setValue(data.source || "");
}

async function saveWorkspace() {
  await fetch("/api/workspace", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: editor.getValue() }),
  });
}

async function loadExamples() {
  const res = await fetch("/api/examples");
  const examples = await res.json();
  examples.forEach((ex) => {
    const opt = document.createElement("option");
    opt.value = ex.source;
    opt.textContent = ex.name;
    exampleSelect.appendChild(opt);
  });
}

async function loadOutputFiles() {
  const res = await fetch("/api/output-dir");
  outputFiles = await res.json();
}

async function compile(run) {
  const btn = run ? runBtn : compileBtn;
  btn.disabled = true;
  const oldText = btn.textContent;
  btn.textContent = run ? "运行中…" : "编译中…";
  try {
    await saveWorkspace();
    const res = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: editor.getValue(),
        optimize: document.getElementById("optCheck").checked,
        run,
        inputs: run ? parseStdinLines() : [],
      }),
    });
    lastResult = await res.json();
    diagSummary.textContent = `${lastResult.error_count} 错误 / ${lastResult.warning_count} 警告`;
    diagSummary.className = "muted " + (lastResult.success ? "status-ok" : "status-fail");
    renderDiagnostics(lastResult.errors, lastResult.warnings);
    if (run) {
      activeTab = "run";
      document.querySelectorAll(".tab").forEach((t) => {
        t.classList.toggle("active", t.dataset.tab === "run");
      });
    }
    showTab(activeTab);
    if (run) await loadOutputFiles();
  } catch (e) {
    errorList.innerHTML = `<div class="diag-item error"><div class="diag-msg">请求失败: ${escapeHtml(e)}</div></div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = oldText;
  }
}

newBtn.addEventListener("click", () => {
  if (confirm("清空当前代码？")) {
    editor.setValue("");
    errorList.innerHTML = "";
    outputArea.textContent = "";
  }
});

saveBtn.addEventListener("click", () => saveWorkspace().then(() => {
  diagSummary.textContent = "已保存 workspace/main.ml";
  diagSummary.className = "muted status-ok";
}));

exampleSelect.addEventListener("change", () => {
  if (exampleSelect.value !== "" && confirm("加载示例将覆盖当前代码，继续？")) {
    editor.setValue(exampleSelect.value);
  }
  exampleSelect.selectedIndex = 0;
});

compileBtn.addEventListener("click", () => compile(false));
runBtn.addEventListener("click", () => compile(true));

document.getElementById("outputTabs").addEventListener("click", (e) => {
  if (e.target.classList.contains("tab")) showTab(e.target.dataset.tab);
});

editor.on("cursorActivity", () => {
  const cur = editor.getCursor();
  cursorPos.textContent = `L${cur.line + 1}:C${cur.ch + 1}`;
});

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    compile(true);
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault();
    saveWorkspace();
  }
});

Promise.all([loadWorkspace(), loadExamples()]).then(() => {
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === "run");
  });
  outputArea.textContent = "编写代码后点击「编译并运行」。使用 input 的程序请在下方输入框填写（每行一次）。";
});
