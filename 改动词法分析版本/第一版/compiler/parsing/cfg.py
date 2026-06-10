"""上下文无关文法加载与规范化。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


EPS = "ε"


@dataclass(frozen=True)
class Production:
    index: int
    head: str
    body: Tuple[str, ...]

    @property
    def is_epsilon(self) -> bool:
        return len(self.body) == 0 or (len(self.body) == 1 and self.body[0] == EPS)


@dataclass
class PrecedenceRule:
    terminals: List[str]
    assoc: str  # left | right
    level: int


@dataclass
class Grammar:
    start: str
    productions: List[Production]
    terminals: Set[str]
    nonterminals: Set[str]
    precedence: List[PrecedenceRule] = field(default_factory=list)
    prod_by_head: Dict[str, List[Production]] = field(default_factory=dict)
    term_prec: Dict[str, Tuple[int, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.prod_by_head = {}
        for p in self.productions:
            self.prod_by_head.setdefault(p.head, []).append(p)
        self.term_prec = {}
        for rule in self.precedence:
            for t in rule.terminals:
                self.term_prec[t] = (rule.level, rule.assoc)


def load_grammar(path: Optional[Path] = None) -> Grammar:
    path = path or Path(__file__).parent.parent.parent / "grammar" / "grammar.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    start = data["start"]
    prods: List[Production] = []
    idx = 0
    nonterminals: Set[str] = set()
    for head, bodies in data["productions"].items():
        nonterminals.add(head)
        for body in bodies:
            norm = tuple() if not body else tuple(body)
            prods.append(Production(idx, head, norm))
            idx += 1

    # 终结符：出现在产生式体中且不是非终结符、不是 ε
    terminals: Set[str] = set()
    for p in prods:
        for sym in p.body:
            if sym != EPS and sym not in nonterminals:
                terminals.add(sym)
    terminals.add("$")

    precedence = [
        PrecedenceRule(r["terminals"], r["assoc"], r["level"])
        for r in data.get("precedence", [])
    ]
    if "MINUS" in terminals:
        # 一元负号在归约时用虚拟终结符比较优先级
        for rule in precedence:
            if "MINUS" in rule.terminals:
                terminals.add("UMINUS")
                break

    return Grammar(
        start=start,
        productions=prods,
        terminals=terminals,
        nonterminals=nonterminals,
        precedence=precedence,
    )
