#===============================================================
# Estado arquitetural do processador vetorial Ubirajara
# VLEN = 128 bits, ELEN = 32 bits, apenas inteiros.
#---------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   09/09/2026
# Update: 26/09/2026
#===============================================================

from dataclasses import dataclass, field
from enum import IntEnum

NUM_VREGS  = 32             # quantidade de registradores fisicos
VLEN       = 128            # largura fisica do registrador vetorial em bits
VLEN_BYTES = VLEN // 8      # 16 bytes por registrador fisico
SUP_LMUL   = (1, 2, 4, 8)   # valores de LMUL suportados


#===============================================================
#  Selected Element Width suportados nesta versao
#===============================================================
class SEW(IntEnum):
    SEW8 = 8
    SEW16 = 16
    SEW32 = 32

def element_mask(sew: int) -> int:
    """Mascara de bits para um elemento de largura sew."""
    return (1 << sew) - 1


#===============================================================
#  VTYPE: define SEW e LMUL ativos
#===============================================================
@dataclass
class VType:
    sew: SEW = SEW.SEW32
    lmul: int = 1

    def __post_init__(self):
        if self.lmul not in SUP_LMUL:
            raise ValueError(
                f"lmul nao suportado: {self.lmul}. "
                f"valores permitidos: {SUP_LMUL}"
            )

    def vlmax(self) -> int:
        """
        Numero maximo de elementos logicos operaveis por instrucao,
        dado o SEW e LMUL ativos.
        """
        return (VLEN // self.sew) * self.lmul

    def elements_per_physical_reg(self) -> int:
        """Quantos elementos de largura sew cabem em um registrador fisico."""
        return VLEN // self.sew

    def group_size(self) -> int:
        """
        Quantos registradores fisicos formam um grupo logico,
        dado o lmul ativo. Para lmul < 1 (fracionario) isto nao
        e suportado nesta versao.
        """
        return max(1, self.lmul)


#===============================================================
#  VECTOR STATE
#===============================================================
@dataclass
class VectorState:
    """
    Estado completo do banco de registradores vetoriais fisicos e
    registradores de controle (vl, vtype).
    """
    vregs: list = field(default_factory=lambda: [
        bytearray(VLEN_BYTES) for _ in range(NUM_VREGS)
    ])
    vl: int = 0
    vtype: VType = field(default_factory=VType)

    #------------------------------------------------------------------
    # controle de vl / vtype
    #------------------------------------------------------------------

    def set_vtype(self, sew: SEW, lmul: int):
        self.vtype = VType(sew=sew, lmul=lmul)

    def set_vl(self, requested_vl: int) -> int:
        """Emula vsetvli: satura requested_vl em VLMAX do vtype ativo."""
        vlmax = self.vtype.vlmax()
        self.vl = min(requested_vl, vlmax)
        return self.vl

    #------------------------------------------------------------------
    # acesso logico a elementos, respeitando sew e lmul ativos
    #------------------------------------------------------------------

    def _base_reg_and_check(self, logical_idx: int) -> int:
        """
        Valida que o indice de registrador logico e um multiplo valido
        de group_size, conforme exigido quando lmul > 1.
        """
        group_size = self.vtype.group_size()

        if logical_idx % group_size != 0:
            raise ValueError(
                f"indice de registrador vetorial {logical_idx} invalido "
                f"para lmul={self.vtype.lmul}: deve ser multiplo de {group_size}"
            )
        if logical_idx + group_size > NUM_VREGS:
            raise ValueError(
                f"grupo de registradores fora dos limites: base={logical_idx}, "
                f"group_size={group_size}, NUM_VREGS={NUM_VREGS}"
            )
        return logical_idx

    def read_elements(self, logical_idx: int) -> list:
        """
        Le todos os elementos logicos de um registrador (ou grupo de
        registradores, se lmul > 1), respeitando o sew ativo.

        Retorna uma lista de inteiros sem sinal, tamanho igual a vlmax.
        """
        base = self._base_reg_and_check(logical_idx)
        sew = self.vtype.sew
        elems_per_reg = self.vtype.elements_per_physical_reg()
        group_size = self.vtype.group_size()

        elements = []
        elem_bytes = sew // 8

        for reg_offset in range(group_size):
            phys_idx = base + reg_offset
            buf = self.vregs[phys_idx]
            for i in range(elems_per_reg):
                start = i * elem_bytes
                raw = buf[start:start + elem_bytes]
                value = int.from_bytes(raw, byteorder="little")
                elements.append(value)

        return elements

    def write_elements(self, logical_idx: int, values: list):
        """
        Escreve elementos logicos em um registrador (ou grupo), respeitando
        o sew ativo. len(values) deve ser igual a vlmax do vtype ativo.
        """
        base = self._base_reg_and_check(logical_idx)
        sew = self.vtype.sew
        elems_per_reg = self.vtype.elements_per_physical_reg()
        group_size = self.vtype.group_size()
        elem_bytes = sew // 8
        mask = element_mask(sew)

        expected_len = elems_per_reg * group_size
        if len(values) != expected_len:
            raise ValueError(
                f"tamanho invalido em write_elements: esperado {expected_len}, "
                f"recebido {len(values)}"
            )

        idx = 0
        for reg_offset in range(group_size):
            phys_idx = base + reg_offset
            buf = self.vregs[phys_idx]
            for i in range(elems_per_reg):
                start = i * elem_bytes
                value = values[idx] & mask
                buf[start:start + elem_bytes] = value.to_bytes(elem_bytes, byteorder="little")
                idx += 1

    #------------------------------------------------------------------
    # acesso bruto (bypass), usado em testes e setup direto
    #------------------------------------------------------------------

    def read_reg_raw_bytes(self, phys_idx: int) -> bytes:
        self._check_phys_idx(phys_idx)
        return bytes(self.vregs[phys_idx])

    def write_reg_raw_bytes(self, phys_idx: int, data: bytes):
        self._check_phys_idx(phys_idx)
        if len(data) != VLEN_BYTES:
            raise ValueError(
                f"tamanho invalido: esperado {VLEN_BYTES} bytes, recebido {len(data)}"
            )
        self.vregs[phys_idx] = bytearray(data)

    @staticmethod
    def _check_phys_idx(phys_idx: int):
        if not (0 <= phys_idx < NUM_VREGS):
            raise IndexError(f"indice de registrador fisico invalido: {phys_idx}")