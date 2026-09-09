#===============================================================
# Execucao das instrucoes vetoriais suportadas na v0:
#   - VADD.VV
#   - VSUB.VV
#   - VAND.VV / VOR.VV / VXOR.VV
#   - VLE32.V   (load unit-stride, 32 bits)
#   - VSE32.V   (store unit-stride, 32 bits)
# Politica de cauda: tail-undisturbed
# Politica de máscara: mask-undisturbed
# Mascaramento: vetor de bits (lista de bool)
#               None = sem máscara (todos ativos)
#---------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   09/09/2026
# Update: 09/09/2026
#===============================================================

from .vector_state import VectorState, ELEMENT_MASK32
from .memory import Memory


def _apply_mask_and_tail(vd_old: list, vd_new: list, vl: int, mask: list = None) -> list:
    """
    Aplica politica de tail-undisturbed e mask-undisturbed.
    Elementos com índice >= vl OU mascarados mantêm o valor antigo.
    """
    result = list(vd_old)
    for i in range(len(vd_new)):
        if i >= vl:
            continue  # tail-undisturbed: mantém vd_old[i]
        if mask is not None and not mask[i]:
            continue  # mask-undisturbed: mantém vd_old[i]
        result[i] = vd_new[i] & ELEMENT_MASK32
    return result


def vadd_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    a = state.read_reg(vs1)
    b = state.read_reg(vs2)
    old = state.read_reg(vd)
    new = [(a[i] + b[i]) & ELEMENT_MASK32 for i in range(len(a))]
    state.write_reg(vd, _apply_mask_and_tail(old, new, state.vl, mask))


def vsub_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    a = state.read_reg(vs1)
    b = state.read_reg(vs2)
    old = state.read_reg(vd)
    new = [(a[i] - b[i]) & ELEMENT_MASK32 for i in range(len(a))]
    state.write_reg(vd, _apply_mask_and_tail(old, new, state.vl, mask))


def vand_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    a = state.read_reg(vs1)
    b = state.read_reg(vs2)
    old = state.read_reg(vd)
    new = [(a[i] & b[i]) for i in range(len(a))]
    state.write_reg(vd, _apply_mask_and_tail(old, new, state.vl, mask))


def vor_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    a = state.read_reg(vs1)
    b = state.read_reg(vs2)
    old = state.read_reg(vd)
    new = [(a[i] | b[i]) for i in range(len(a))]
    state.write_reg(vd, _apply_mask_and_tail(old, new, state.vl, mask))


def vxor_vv(state: VectorState, vd: int, vs1: int, vs2: int, mask: list = None):
    a = state.read_reg(vs1)
    b = state.read_reg(vs2)
    old = state.read_reg(vd)
    new = [(a[i] ^ b[i]) for i in range(len(a))]
    state.write_reg(vd, _apply_mask_and_tail(old, new, state.vl, mask))


def vle32_v(state: VectorState, mem: Memory, vd: int, base_addr: int, mask: list = None):
    """Load unit-stride, elementos de 32 bits, contíguos."""
    old = state.read_reg(vd)
    new = list(old)
    for i in range(state.vl):
        if mask is not None and not mask[i]:
            continue
        addr = base_addr + i * 4
        new[i] = mem.load_word(addr)
    state.write_reg(vd, _apply_mask_and_tail(old, new, state.vl, mask))


def vse32_v(state: VectorState, mem: Memory, vs3: int, base_addr: int, mask: list = None):
    """Store unit-stride, elementos de 32 bits, contíguos."""
    data = state.read_reg(vs3)
    for i in range(state.vl):
        if mask is not None and not mask[i]:
            continue
        addr = base_addr + i * 4
        mem.store_word(addr, data[i])