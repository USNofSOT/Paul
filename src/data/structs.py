from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Award:
    role_id: int = 0
    embed_id: int = 0
    ranks_responsible: str = ""
    threshold: int = 0
    streak: bool = True
