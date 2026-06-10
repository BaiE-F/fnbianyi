"""表驱动语法分析：LL(1)、LR(0)、SLR(1)、LALR(1)、LR(1) 及自动选法。"""

from .cfg import Grammar, Production, load_grammar
from .selector import ParseMethod, select_parse_method, get_parse_tables

__all__ = [
    "Grammar",
    "Production",
    "load_grammar",
    "ParseMethod",
    "select_parse_method",
    "get_parse_tables",
]
