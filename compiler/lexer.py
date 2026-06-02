"""词法分析器 — 从 grammar/tokens.json 加载规则，将源码切分为 Token 流。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from .errors import CompileDiagnostic, Stage, diagnostic


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, L{self.line})"

    def to_dict(self) -> dict:
        return {"kind": self.kind, "value": self.value, "line": self.line, "col": self.col}


class LexerError(Exception):
    pass


@dataclass
class LexResult:
    tokens: List[Token] = field(default_factory=list)
    errors: List[CompileDiagnostic] = field(default_factory=list)


class Lexer:
    MAX_ERRORS = 50

    def __init__(self, source: str, rules_path: Optional[Path] = None):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.errors: List[CompileDiagnostic] = []
        rules_path = rules_path or Path(__file__).parent.parent / "grammar" / "tokens.json"
        self.rules = self._load_rules(rules_path)

    @staticmethod
    def _load_rules(path: Path) -> dict:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _current(self) -> str:
        return self.source[self.pos : self.pos + 1] if self.pos < len(self.source) else ""

    def _advance(self, n: int = 1) -> None:
        for _ in range(n):
            if self.pos < len(self.source) and self.source[self.pos] == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1

    def _match_regex(self, pattern: str) -> Optional[str]:
        m = re.match(pattern, self.source[self.pos :], re.DOTALL)
        if m:
            text = m.group(0)
            self._advance(len(text))
            return text
        return None

    def _add_error(self, message: str, line: int, col: int, code: str = "E001") -> None:
        if len(self.errors) >= self.MAX_ERRORS:
            return
        self.errors.append(
            diagnostic(Stage.LEXER, message, line=line, col=col, code=code)
        )

    def _validate_number(self, text: str, line: int, col: int) -> bool:
        if text.count(".") > 1:
            self._add_error(f"非法数字格式 '{text}'（多个小数点）", line, col, "E003")
            return False
        if text.endswith("."):
            self._add_error(f"非法数字格式 '{text}'（小数点后缺少数字）", line, col, "E004")
            return False
        if text.startswith(".") and text != ".":
            pass  # .5 style - our regex may not match this
        try:
            float(text)
        except ValueError:
            self._add_error(f"非法数字格式 '{text}'", line, col, "E005")
            return False
        return True

    def next_token(self) -> Optional[Token]:
        while self.pos < len(self.source):
            start_line, start_col = self.line, self.col

            skipped = False
            for spec in self.rules.get("patterns", []):
                if not spec.get("skip"):
                    continue
                text = self._match_regex(spec["regex"])
                if text is not None:
                    skipped = True
                    break
            if skipped:
                continue

            for op, kind in sorted(
                self.rules.get("operators", {}).items(), key=lambda x: -len(x[0])
            ):
                if self.source.startswith(op, self.pos):
                    self._advance(len(op))
                    return Token(kind, op, start_line, start_col)

            for kw, kind in self.rules.get("keywords", {}).items():
                if re.match(rf"{re.escape(kw)}\b", self.source[self.pos :]):
                    self._advance(len(kw))
                    return Token(kind, kw, start_line, start_col)

            for spec in self.rules.get("patterns", []):
                if spec.get("skip"):
                    continue
                text = self._match_regex(spec["regex"])
                if text is not None:
                    if spec["name"] in ("INT_LIT", "FLOAT_LIT"):
                        self._validate_number(text, start_line, start_col)
                    if spec["name"] == "STRING_LIT":
                        text = self._decode_string(text)
                    if spec["name"] == "IDENT" and text[0].isdigit():
                        self._add_error(
                            f"标识符 '{text}' 不能以数字开头", start_line, start_col, "E006"
                        )
                        return Token("ERROR", text, start_line, start_col)
                    return Token(spec["name"], text, start_line, start_col)

            ch = self._current()
            if not ch:
                break
            self._add_error(f"无法识别的字符 {ch!r}", start_line, start_col, "E001")
            self._advance(1)
            return Token("ERROR", ch, start_line, start_col)
        return None

    @staticmethod
    def _decode_string(text: str) -> str:
        inner = text[1:-1]
        return inner.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')

    def tokenize(self) -> LexResult:
        tokens: List[Token] = []
        while True:
            tok = self.next_token()
            if tok is None:
                break
            tokens.append(tok)
        tokens.append(Token("EOF", "", self.line, self.col))
        return LexResult(tokens=tokens, errors=list(self.errors))

    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokenize().tokens)
