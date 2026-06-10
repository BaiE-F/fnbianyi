"""LL(1) 预测分析表构造。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from .cfg import EPS, Grammar, Production
from .first_follow import _first_of_sequence, compute_first, compute_follow


@dataclass
class LL1Table:
    method: str = "LL1"
    table: Dict[Tuple[str, str], int] = field(default_factory=dict)
    conflicts: List[str] = field(default_factory=list)
    productions: List[Production] = field(default_factory=list)


def build_ll1_table(grammar: Grammar) -> LL1Table:
    first = compute_first(grammar)
    follow = compute_follow(grammar, first)
    table: Dict[Tuple[str, str], int] = {}
    conflicts: List[str] = []

    for prod in grammar.productions:
        seq_first = _first_of_sequence(prod.body, first)
        for t in seq_first - {EPS}:
            key = (prod.head, t)
            if key in table and table[key] != prod.index:
                conflicts.append(
                    f"LL1 冲突 ({prod.head}, {t}): 产生式 {table[key]} vs {prod.index}"
                )
            else:
                table[key] = prod.index
        if EPS in seq_first:
            for t in follow.get(prod.head, set()):
                key = (prod.head, t)
                if key in table and table[key] != prod.index:
                    conflicts.append(
                        f"LL1 冲突 ({prod.head}, {t}): 产生式 {table[key]} vs {prod.index}"
                    )
                else:
                    table[key] = prod.index

    return LL1Table("LL1", table, conflicts, grammar.productions)
