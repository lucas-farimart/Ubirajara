#==================================================================
# Wrapper de alto nivel: API estavel a ser usada pelo testbench
# (diretamente em Python agora, e futuramente como referencia
# para comparação com SystemC/RTL via DPI ou scoreboard externo).
# 
# vsetvli aceita SEW e LMUL explicitos, permitindo comprimentos
# de vetor logico variados dentro do mesmo VLEN fisico.
#------------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   09/09/2026
# Update: 26/09/2026
#==================================================================

from .vector_state import VectorState, VType, SEW
from .memory import Memory
from . import vector_isa as isa

class GoldenModel:
    def __init__(self, mem_size_bytes: int = 1 << 20):
        self.state = VectorState()
        self.mem = Memory(mem_size_bytes)

    def vsetvli(self, requested_vl: int, sew: SEW = SEW.SEW32, lmul: int = 1) -> int:
        self.state.set_vtype(sew=sew, lmul=lmul)
        return self.state.set_vl(requested_vl)

    def vadd_vv(self, vd, vs1, vs2, mask=None):
        isa.vadd_vv(self.state, vd, vs1, vs2, mask)

    def vsub_vv(self, vd, vs1, vs2, mask=None):
        isa.vsub_vv(self.state, vd, vs1, vs2, mask)

    def vand_vv(self, vd, vs1, vs2, mask=None):
        isa.vand_vv(self.state, vd, vs1, vs2, mask)

    def vor_vv(self, vd, vs1, vs2, mask=None):
        isa.vor_vv(self.state, vd, vs1, vs2, mask)

    def vxor_vv(self, vd, vs1, vs2, mask=None):
        isa.vxor_vv(self.state, vd, vs1, vs2, mask)

    def vle_v(self, vd, base_addr, mask=None):
        isa.vle_v(self.state, self.mem, vd, base_addr, mask)

    def vse_v(self, vs3, base_addr, mask=None):
        isa.vse_v(self.state, self.mem, vs3, base_addr, mask)

    #---------------------------------------------------------------------
    #  aliases de retrocompatibilidade com a versao sew32-only anterior
    #---------------------------------------------------------------------
    def vle32_v(self, vd, base_addr, mask=None):
        self.vle_v(vd, base_addr, mask)

    def vse32_v(self, vs3, base_addr, mask=None):
        self.vse_v(vs3, base_addr, mask)

    #---------------------------------------------------------------------
    #  utilitarios de teste (bypass)
    #---------------------------------------------------------------------
    def load_reg_direct(self, idx: int, values: list):
        """
        Escreve elementos logicos diretamente em um registrador,
        respeitando o sew/lmul ativos no momento da chamada.
        """
        self.state.write_elements(idx, values)

    def read_reg_direct(self, idx: int) -> list:
        return self.state.read_elements(idx)

    def write_mem_bytes(self, addr: int, payload: bytes):
        self.mem.store_bytes(addr, payload)

    def read_mem_bytes(self, addr: int, length: int) -> bytes:
        return self.mem.load_bytes(addr, length)