"""语法分析树节点。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..lexer import Token


@dataclass
class PTNode:
    symbol: str
    children: List["PTNode"] = field(default_factory=list)
    token: Optional[Token] = None
    prod_index: int = -1

    def child(self, index: int) -> Optional["PTNode"]:
        if 0 <= index < len(self.children):
            return self.children[index]
        return None

    def text(self) -> str:
        if self.token:
            return self.token.value
        return self.symbol

    def line(self) -> int:
        if self.token:
            return self.token.line
        for c in self.children:
            if c.token:
                return c.token.line
        return 0
