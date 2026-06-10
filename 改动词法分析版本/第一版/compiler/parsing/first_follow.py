"""First / Follow 集计算。"""

from __future__ import annotations

from typing import Dict, Set

from .cfg import EPS, Grammar


def compute_first(grammar: Grammar) -> Dict[str, Set[str]]:
    first: Dict[str, Set[str]] = {t: {t} for t in grammar.terminals if t != EPS}
    for nt in grammar.nonterminals:
        first[nt] = set()

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            head_first = first[prod.head]
            before = len(head_first)
            if prod.is_epsilon:
                head_first.add(EPS)
            else:
                seq_first = _first_of_sequence(prod.body, first)
                head_first.update(seq_first)
            if len(head_first) != before:
                changed = True
    return first


def compute_follow(grammar: Grammar, first: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    follow: Dict[str, Set[str]] = {nt: set() for nt in grammar.nonterminals}
    follow[grammar.start].add("$")

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            body = list(prod.body)
            for i, sym in enumerate(body):
                if sym not in grammar.nonterminals:
                    continue
                trailer = body[i + 1 :]
                add = _first_of_sequence(tuple(trailer), first) - {EPS}
                if not trailer or EPS in _first_of_sequence(tuple(trailer), first):
                    add |= follow[prod.head]
                before = len(follow[sym])
                follow[sym].update(add)
                if len(follow[sym]) != before:
                    changed = True
    return follow


def _first_of_sequence(symbols: tuple, first: Dict[str, Set[str]]) -> Set[str]:
    result: Set[str] = set()
    for sym in symbols:
        if sym == EPS:
            result.add(EPS)
            break
        if sym in first:
            result.update(first[sym] - {EPS})
            if EPS not in first[sym]:
                break
        else:
            result.add(sym)
            break
    else:
        result.add(EPS)
    return result
