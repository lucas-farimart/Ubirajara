#===============================================================
# Execucao das instrucoes vetoriais parametrizadas por SEW e 
# LMUL ativos no vtype corrente do VectorState:
#   - VADD.VV
#   - VSUB.VV
#   - VAND.VV / VOR.VV / VXOR.VV
#   - VLE32.V   (load unit-stride, 32 bits)
#   - VSE32.V   (store unit-stride, 32 bits)
# Politica de cauda: tail-undisturbed
# Politica de mascara: mask-undisturbed
# Mascaramento: Vetor de bits (lista de bool)
#               None = sem mascara (todos ativos)
#---------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   09/09/2026
# Update: 26/09/2026
#===============================================================

from .vector_state import VectorState, element_mask
from .memory import Memory

#===============================================================
# POLITICA DE TAIL/MASK UNDISTURBED:
# Indice >= vl OU mascarados mantem o valor antigo
#===============================================================

def _apply_mask_and_tail(vd_old: list, vd_new: list, vl: int, sew: int, mask: list = None) -> list:
    mask_bits = element_mask(sew)
    result = list(vd_old)
    for i in range(len(vd_new)):
        if i >= vl:
            continue
        if mask is not None and not mask[i]:
            continue
        result[i] = vd_new[i] & mask_bits
    return result


def _binop(state: VectorState, vd: int, vs1: int, vs2: int, op, mask: list = None):
    a   = state.read_elements(vs1)
    b   = state.read_elements(vs2)
    old = state.read_elements(vd)
    sew = state.vtype.sew
    new = [op(a[i], b[i]) for i in range(len(a))]

    state.write_elements(vd, _apply_mask_and_tail(old, new, state.vl, sew, mask))


def vadd_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    _binop(state, vd, vs1, vs2, lambda x, y: x + y, mask)


def vsub_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    _binop(state, vd, vs1, vs2, lambda x, y: x - y, mask)


def vand_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    _binop(state, vd, vs1, vs2, lambda x, y: x & y, mask)


def vor_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    _binop(state, vd, vs1, vs2, lambda x, y: x | y, mask)


def vxor_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    _binop(state, vd, vs1, vs2, lambda x, y: x ^ y, mask)


#===============================================================
# LOAD UNIT-STRIDE 
# Contiguo, com largura de elemento igual ao SEW ativo
#===============================================================
def vle_v(state: VectorState, mem: Memory, vd: int, base_addr: int, mask: list = None):
    sew = state.vtype.sew
    elem_bytes = sew // 8
    old = state.read_elements(vd)
    new = list(old)

    for i in range(state.vl):
        if mask is not None and not mask[i]:
            continue
        addr = base_addr + i * elem_bytes
        raw = mem.load_bytes(addr, elem_bytes)
        new[i] = int.from_bytes(raw, byteorder="little")

    state.write_elements(vd, _apply_mask_and_tail(old, new, state.vl, sew, mask))


#===============================================================
# STORE UNIT-STRIDE 
# Contiguo, com largura de elemento igual ao sew ativo.
#===============================================================
def vse_v(state: VectorState, mem: Memory, vs3: int, base_addr: int, mask: list = None):
    sew = state.vtype.sew
    elem_bytes = sew // 8
    data = state.read_elements(vs3)

    for i in range(state.vl):
        if mask is not None and not mask[i]:
            continue
        addr = base_addr + i * elem_bytes
        value = data[i] & element_mask(sew)
        mem.store_bytes(addr, value.to_bytes(elem_bytes, byteorder="little"))