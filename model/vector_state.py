#===============================================================
# Estado arquitetural do processador vetorial Ubirajara
# VLEN = 128 bits, ELEN = 32 bits, apenas inteiros.
#---------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   09/09/2026
# Update: 09/09/2026
#===============================================================

from dataclasses import dataclass, field
from enum import IntEnum

VLEN = 128          # largura do registrador vetorial em bits
ELEN = 32           # largura maxima de elemento em bits
NUM_VREGS = 32      # quantidade de registradores vetoriais
ELEMENT_MASK32 = (1 << 32) - 1


class SEW(IntEnum):
    """Selected Element Width suportado nesta versão."""
    SEW32 = 32
    # SEW8 = 8    # reservado para versões futuras
    # SEW16 = 16  # reservado para versões futuras


@dataclass
class VType:
    """Registrador vtype simplificado (sem vma/vta explícitos por ora)."""
    sew: SEW = SEW.SEW32
    lmul: int = 1  # fixo em 1 nesta primeira versão

    def vlmax(self) -> int:
        return (VLEN // self.sew) * self.lmul


@dataclass
class VectorState:
    """
    Estado completo do banco de registradores vetoriais e
    registradores de controle (vl, vtype).
    """
    # cada registrador vetorial é representado como lista de elementos de 32 bits
    vregs: list = field(default_factory=lambda: [
        [0] * (VLEN // 32) for _ in range(NUM_VREGS)
    ])
    vl: int = 0
    vtype: VType = field(default_factory=VType)

    def elements_per_reg(self) -> int:
        return VLEN // self.vtype.sew

    def set_vl(self, requested_vl: int) -> int:
        """
        Emula vsetvli: retorna o vl efetivo, limitado por VLMAX.
        """
        vlmax = self.vtype.vlmax()
        self.vl = min(requested_vl, vlmax)
        return self.vl

    def read_reg(self, idx: int) -> list:
        self._check_idx(idx)
        return list(self.vregs[idx])  # cópia defensiva

    def write_reg(self, idx: int, values: list):
        self._check_idx(idx)
        if len(values) != len(self.vregs[idx]):
            raise ValueError(
                f"Tamanho invalido: esperado {len(self.vregs[idx])}, "
                f"recebido {len(values)}"
            )
        self.vregs[idx] = [v & ELEMENT_MASK32 for v in values]

    @staticmethod
    def _check_idx(idx: int):
        if not (0 <= idx < NUM_VREGS):
            raise IndexError(f"Índice de registrador vetorial invalido: {idx}")