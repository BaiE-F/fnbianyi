"""语法分析器 — 表驱动 LL(1)/LR 系，自动选法，构建 AST。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .ast_nodes import Program
from .errors import CompileDiagnostic
from .lexer import Token
from .parsing.ast_builder import build_program
from .parsing.parse_tree import PTNode
from .parsing.cfg import load_grammar
from .parsing.driver import parse_ll1, parse_lr
from .parser_rd import RecursiveDescentParser
from .parsing.selector import SelectedParser, select_parse_method


@dataclass
class ParseResult:
    program: Optional[Program] = None
    errors: List[CompileDiagnostic] = field(default_factory=list)
    parse_method: str = ""


class Parser:
    """表驱动语法分析器：LL(1) → LR(0) → SLR(1) → LALR(1) → LR(1) 自动选法。"""

    _cached: Optional[SelectedParser] = None
    _grammar_path: Optional[Path] = None

    def __init__(
        self,
        tokens: List[Token],
        grammar_path: Optional[Path] = None,
        method: str = "auto",
    ):
        self.tokens = tokens
        self.grammar_path = grammar_path or Path(__file__).parent.parent / "grammar" / "grammar.json"
        self.method_pref = method
        self.errors: List[CompileDiagnostic] = []
        self.parse_method = ""

    @classmethod
    def _get_selected(cls, grammar_path: Path, method: str) -> SelectedParser:
        if cls._cached is None or cls._grammar_path != grammar_path:
            cls._cached = select_parse_method(grammar_path, method)
            cls._grammar_path = grammar_path
        elif method != "auto" and cls._cached.method != method:
            cls._cached = select_parse_method(grammar_path, method)
        return cls._cached

    def parse(self) -> ParseResult:
        selected = self._get_selected(self.grammar_path, self.method_pref)
        self.parse_method = selected.method
        grammar = load_grammar(self.grammar_path)

        if selected.method == "LL1" and selected.ll1:
            drv = parse_ll1(self.tokens, grammar, selected.ll1)
        elif selected.lr:
            drv = parse_lr(self.tokens, grammar, selected.lr)
        else:
            self.errors.append(
                CompileDiagnostic(
                    stage="语法分析",
                    message="无法加载语法分析表",
                    code="E200",
                )
            )
            return ParseResult(None, list(self.errors), selected.method)

        self.errors.extend(drv.errors)
        program: Optional[Program] = None
        if drv.tree:
            root = drv.tree
            if root.symbol == "TopList":
                root = PTNode("Program", [root])
            if root.symbol == grammar.start:
                try:
                    program = build_program(root)
                except Exception as exc:
                    self.errors.append(
                        CompileDiagnostic(
                            stage="语法分析",
                            message=f"语法树构建失败: {exc}",
                            code="E202",
                        )
                    )
        elif not self.errors:
            self.errors.append(
                CompileDiagnostic(
                    stage="语法分析",
                    message="未能生成有效的语法树",
                    code="E299",
                )
            )

        if program is None and not any(e.code == "E298" for e in self.errors):
            fb = RecursiveDescentParser(self.tokens).parse()
            if fb.program and (fb.program.functions or fb.program.statements):
                program = fb.program
                self.errors.extend(fb.errors)
                self.parse_method = f"{selected.method}+RD"

        return ParseResult(program, list(self.errors), self.parse_method)
