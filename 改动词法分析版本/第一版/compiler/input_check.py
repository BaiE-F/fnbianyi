"""编译器内部：推断 input/getint 读入个数是否应校验。"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .ast_nodes import (
    AssignStmt,
    Block,
    CallExpr,
    Expr,
    ForStmt,
    IfStmt,
    IntLit,
    RelExpr,
    Stmt,
    VarExpr,
    WhileStmt,
)


def index_upper_bound(condition: Expr) -> Optional[Tuple[str, str]]:
    """while (j < x) → ('j', 'x')；while (j < 5) → ('j', '5')。"""
    if not isinstance(condition, RelExpr) or condition.op != "<":
        return None
    if not isinstance(condition.left, VarExpr):
        return None
    if isinstance(condition.right, VarExpr):
        return condition.left.name, condition.right.name
    if isinstance(condition.right, IntLit):
        return condition.left.name, str(condition.right.value)
    return None


def block_uses_getint(body: Block, line_var: str, index_var: str) -> bool:
    for stmt in body.statements:
        if _stmt_uses_getint(stmt, line_var, index_var):
            return True
    return False


def _stmt_uses_getint(stmt: Stmt, line_var: str, index_var: str) -> bool:
    if isinstance(stmt, AssignStmt) and isinstance(stmt.value, CallExpr):
        return _call_is_getint(stmt.value, line_var, index_var)
    if isinstance(stmt, Block):
        return block_uses_getint(stmt, line_var, index_var)
    if isinstance(stmt, IfStmt):
        if _block_uses_getint(stmt.then_block, line_var, index_var):
            return True
        if stmt.else_block and _block_uses_getint(stmt.else_block, line_var, index_var):
            return True
    if isinstance(stmt, WhileStmt):
        return block_uses_getint(stmt.body, line_var, index_var)
    if isinstance(stmt, ForStmt):
        return block_uses_getint(stmt.body, line_var, index_var)
    return False


def _block_uses_getint(block: Block, line_var: str, index_var: str) -> bool:
    return block_uses_getint(block, line_var, index_var)


def _call_is_getint(call: CallExpr, line_var: str, index_var: str) -> bool:
    if call.name != "getint" or len(call.args) != 2:
        return False
    line_ok = isinstance(call.args[0], VarExpr) and call.args[0].name == line_var
    idx_ok = isinstance(call.args[1], VarExpr) and call.args[1].name == index_var
    return line_ok and idx_ok


def infer_line_expected(line_var: str, following: List[Stmt]) -> Optional[str]:
    """input(line) 之后若存在 while (j < x) { ... getint(line, j) ... }，返回期望个数 x。"""
    for stmt in following:
        if isinstance(stmt, WhileStmt):
            bound = index_upper_bound(stmt.condition)
            if bound and block_uses_getint(stmt.body, line_var, bound[0]):
                return bound[1]
        if isinstance(stmt, Block):
            found = infer_line_expected(line_var, stmt.statements)
            if found:
                return found
        if isinstance(stmt, IfStmt):
            found = infer_line_expected(line_var, stmt.then_block.statements)
            if found:
                return found
            if stmt.else_block:
                found = infer_line_expected(line_var, stmt.else_block.statements)
                if found:
                    return found
    return None


def stmt_has_getint_index(stmts: List[Stmt], index_var: str) -> bool:
    for stmt in stmts:
        if _stmt_has_getint_index(stmt, index_var):
            return True
    return False


def _stmt_has_getint_index(stmt: Stmt, index_var: str) -> bool:
    if isinstance(stmt, AssignStmt) and isinstance(stmt.value, CallExpr):
        call = stmt.value
        if call.name == "getint" and len(call.args) == 2:
            return isinstance(call.args[1], VarExpr) and call.args[1].name == index_var
    if isinstance(stmt, Block):
        return stmt_has_getint_index(stmt.statements, index_var)
    if isinstance(stmt, IfStmt):
        if stmt_has_getint_index(stmt.then_block.statements, index_var):
            return True
        if stmt.else_block and stmt_has_getint_index(stmt.else_block.statements, index_var):
            return True
    if isinstance(stmt, WhileStmt):
        return stmt_has_getint_index(stmt.body.statements, index_var)
    if isinstance(stmt, ForStmt):
        return stmt_has_getint_index(stmt.body.statements, index_var)
    return False


def while_getint_bound(condition: Expr, body: Block) -> Optional[Tuple[str, str]]:
    """while (j < x) 且循环体内有 getint(..., j) 时返回 ('j', 'x')。"""
    bound = index_upper_bound(condition)
    if not bound:
        return None
    if stmt_has_getint_index(body.statements, bound[0]):
        return bound
    return None
