"""
=========================================================================
Registro de execucao arquitetural (golden trace).
  Cada entrada representa o efeito observavel de uma instrucao:
  estado de entrada relevante, operandos e estado de saida.
-------------------------------------------------------------------------
Author: Lucas Farias Martins
Email:  lucas.martins@ee.ufcg.edu.br
Date:   25/09/2026
Update: 25/09/2026
=========================================================================
"""

from dataclasses import dataclass, field
from typing import Any
import json

#=======================================================================
#  Trace Entry
#=======================================================================
@dataclass
class TraceEntry:
    index: int
    mnemonic: str
    operands: dict
    vl_at_execution: int
    result_regs: dict           # {reg_idx: [elementos]} apenas dos regs escritos
    mem_writes: dict = field(default_factory=dict)  # {addr: valor} apenas se houver store

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "mnemonic": self.mnemonic,
            "operands": self.operands,
            "vl_at_execution": self.vl_at_execution,
            "result_regs": self.result_regs,
            "mem_writes": self.mem_writes,
        }
                     
class Trace:
    """Colecao ordenada de TraceEntry, com serializacao para comparacao externa."""

    def __init__(self):
        self._entries: list = []

    def add(self, entry: TraceEntry):
        self._entries.append(entry)

    def clear(self):
        self._entries.clear()

    def entries(self) -> list:
        return list(self._entries)

    def to_json(self) -> str:
        return json.dumps([e.to_dict() for e in self._entries], indent=2)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    def __len__(self) -> int:
        return len(self._entries)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Trace):
            return NotImplemented
        return [e.to_dict() for e in self._entries] == [e.to_dict() for e in other.entries()]