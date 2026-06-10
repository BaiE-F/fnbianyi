"""LL(1) 与 LR 分析驱动器（含错误恢复）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ..errors import CompileDiagnostic, Stage, diagnostic
from ..lexer import Token
from .cfg import EPS, Grammar, Production
from .ll1 import LL1Table
from .lr import ParseTableSet
from .parse_tree import PTNode

def _token_symbol(tok: Token) -> str:
    return "$" if tok.kind == "EOF" else tok.kind


SYNC_TOKENS = frozenset({
    "SEMI", "RBRACE", "EOF", "IF", "WHILE", "FOR", "PRINT", "PRINTN",
    "INPUT", "WRITE", "RETURN", "BREAK", "CONTINUE", "INT", "FLOAT", "STRING", "VOID",
})


@dataclass
class DriverResult:
    tree: Optional[PTNode] = None
    errors: List[CompileDiagnostic] = field(default_factory=list)


def parse_ll1(
    tokens: List[Token],
    grammar: Grammar,
    table: LL1Table,
) -> DriverResult:
    return _parse_ll1_std(tokens, grammar, table)


def _parse_ll1_std(tokens: List[Token], grammar: Grammar, table: LL1Table) -> DriverResult:
    errors: List[CompileDiagnostic] = []
    stack: List[str] = ["$", grammar.start]
    node_stack: List[PTNode] = []
    pos = 0
    steps = 0
    limit = len(tokens) * 30 + 100

    while stack and steps < limit:
        steps += 1
        top = stack[-1]
        cur = tokens[pos] if pos < len(tokens) else tokens[-1]
        a = _token_symbol(cur)

        if top in grammar.terminals or top == "$":
            if top == a:
                if top != "$":
                    node_stack.append(PTNode(top, token=cur))
                    if a != "EOF":
                        pos += 1
                stack.pop()
            else:
                _add_err(errors, f"期望 {top}，实际为 {a} ({cur.value!r})", cur)
                pos = _sync(tokens, pos, errors)
                if stack:
                    stack.pop()
            continue

        key = (top, a)
        if key not in table.table:
            _add_err(errors, f"无法应用 LL(1) 预测 ({top}, {a})", cur)
            pos = _sync(tokens, pos, errors)
            stack.pop()
            continue

        prod = grammar.productions[table.table[key]]
        stack.pop()
        rhs = [] if prod.is_epsilon else list(prod.body)
        children: List[PTNode] = []
        for _ in rhs:
            if node_stack:
                children.insert(0, node_stack.pop())
        parent = PTNode(prod.head, children, prod_index=prod.index)
        node_stack.append(parent)
        for sym in reversed(rhs):
            stack.append(sym)

    if node_stack:
        return DriverResult(node_stack[-1], errors)
    return DriverResult(None, errors)


def parse_lr(
    tokens: List[Token],
    grammar: Grammar,
    table: ParseTableSet,
) -> DriverResult:
    errors: List[CompileDiagnostic] = []
    state_stack = [0]
    node_stack: List[PTNode] = []
    pos = 0
    steps = 0
    limit = len(tokens) * 40 + 200

    while steps < limit:
        steps += 1
        cur = tokens[pos] if pos < len(tokens) else tokens[-1]
        a = _token_symbol(cur)
        state = state_stack[-1]
        action = table.action.get((state, a))

        if not action:
            _add_err(errors, f"语法分析动作缺失 (状态{state}, {a})", cur)
            pos = _sync(tokens, pos, errors)
            if len(state_stack) > 1:
                state_stack.pop()
                if node_stack:
                    node_stack.pop()
            else:
                pos += 1 if pos < len(tokens) - 1 else 0
            continue

        kind, arg = action
        if kind == "shift":
            leaf = PTNode(a, token=cur)
            node_stack.append(leaf)
            state_stack.append(arg)
            if a != "EOF":
                pos += 1
            continue

        if kind == "reduce":
            prod = grammar.productions[arg]
            rhs = [] if prod.is_epsilon else list(prod.body)
            children: List[PTNode] = []
            for _ in rhs:
                if state_stack:
                    state_stack.pop()
                if node_stack:
                    children.insert(0, node_stack.pop())
            parent = PTNode(prod.head, children, prod_index=prod.index)
            node_stack.append(parent)
            goto_state = table.goto.get((state_stack[-1], prod.head))
            if goto_state is None:
                _add_err(errors, f"GOTO 缺失 ({state_stack[-1]}, {prod.head})", cur)
                break
            state_stack.append(goto_state)
            continue

        if kind == "accept":
            if node_stack:
                return DriverResult(node_stack[-1], errors)
            return DriverResult(None, errors)

    _add_err(errors, "语法分析错误恢复停滞，已中止", tokens[min(pos, len(tokens) - 1)], "E298")
    root = node_stack[-1] if node_stack else None
    return DriverResult(root, errors)


def _sync(tokens: List[Token], pos: int, errors: List[CompileDiagnostic]) -> int:
    if pos >= len(tokens):
        return pos
    start = pos
    while pos < len(tokens) - 1 and tokens[pos].kind not in SYNC_TOKENS:
        pos += 1
    if pos == start and pos < len(tokens) - 1:
        pos += 1
    if tokens[pos].kind == "SEMI":
        pos += 1
    return pos


def _add_err(
    errors: List[CompileDiagnostic],
    msg: str,
    tok: Token,
    code: str = "E201",
) -> None:
    if len(errors) >= 50:
        return
    errors.append(diagnostic(Stage.SYNTAX, msg, line=tok.line, col=tok.col, code=code))
