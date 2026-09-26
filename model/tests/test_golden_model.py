#===============================================================
# Testes para o modelo de referencia.
# Use pytest: pytest tests/test_golden_model.py -v
#         ou: pytest -v
#---------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   09/09/2026
# Update: 25/09/2026
#===============================================================

import struct
import pytest
import random
from model.golden_model import GoldenModel
from model.vector_state import SEW

#===============================================================
#  CONSTRUCT
#===============================================================

def make_model_with_vl(vl: int) -> GoldenModel:
    gm = GoldenModel()
    gm.vsetvli(vl, sew=SEW.SEW32, lmul=1)
    return gm

def test_vl_zero_does_not_modify_destination():
    gm = make_model_with_vl(0)

    gm.load_reg_direct(1, [1, 2, 3, 4])
    gm.load_reg_direct(2, [10, 20, 30, 40])
    gm.load_reg_direct(3, [99, 99, 99, 99])

    gm.vadd_vv(vd=3, vs1=1, vs2=2)

    assert gm.read_reg_direct(3) == [99, 99, 99, 99]

#===============================================================
#  ADD/SUB/LOGIC INSTRUCTIONS TESTS
#===============================================================

def test_vadd_vv_full_vl():
    gm = make_model_with_vl(4)  # VLMAX = 128/32 = 4
    gm.load_reg_direct(1, [1, 2, 3, 4])
    gm.load_reg_direct(2, [10, 20, 30, 40])
    gm.vadd_vv(vd=3, vs1=1, vs2=2)
    assert gm.read_reg_direct(3) == [11, 22, 33, 44]


def test_vadd_vv_partial_vl_tail_undisturbed():
    gm = make_model_with_vl(2)  # vl=2, VLMAX=4
    gm.load_reg_direct(1, [1, 2, 3, 4])
    gm.load_reg_direct(2, [10, 20, 30, 40])
    gm.load_reg_direct(3, [99, 99, 99, 99])  # valor previo de vd
    gm.vadd_vv(vd=3, vs1=1, vs2=2)
    # elementos 0 e 1 atualizados, 2 e 3 mantem valor antigo (99)
    assert gm.read_reg_direct(3) == [11, 22, 99, 99]


def test_vadd_vv_with_mask():
    gm = make_model_with_vl(4)
    gm.load_reg_direct(1, [1, 2, 3, 4])
    gm.load_reg_direct(2, [10, 20, 30, 40])
    gm.load_reg_direct(3, [0, 0, 0, 0])
    mask = [True, False, True, False]
    gm.vadd_vv(vd=3, vs1=1, vs2=2, mask=mask)
    # elementos mascarados (indices 1 e 3) mantem valor antigo (0)
    assert gm.read_reg_direct(3) == [11, 0, 33, 0]


def test_vsub_vv_overflow_wraps_mod_2_32():
    gm = make_model_with_vl(4)
    gm.load_reg_direct(1, [0, 0, 0, 0])
    gm.load_reg_direct(2, [1, 1, 1, 1])
    gm.vsub_vv(vd=3, vs1=1, vs2=2)
    expected = (0 - 1) & 0xFFFFFFFF
    assert gm.read_reg_direct(3) == [expected] * 4


def test_vand_vor_vxor():
    gm = make_model_with_vl(4)
    gm.load_reg_direct(1, [0xFF00FF00] * 4)
    gm.load_reg_direct(2, [0x0F0F0F0F] * 4)
    gm.vand_vv(vd=3, vs1=1, vs2=2)
    assert gm.read_reg_direct(3) == [0x0F000F00] * 4
    gm.vor_vv(vd=4, vs1=1, vs2=2)
    assert gm.read_reg_direct(4) == [0xFF0FFF0F] * 4
    gm.vxor_vv(vd=5, vs1=1, vs2=2)
    assert gm.read_reg_direct(5) == [0xF00FF00F] * 4


def test_vadd_vv_randomized():
    gm = make_model_with_vl(4)
    a = [random.getrandbits(32) for _ in range(4)]
    b = [random.getrandbits(32) for _ in range(4)]
    gm.load_reg_direct(1, a)
    gm.load_reg_direct(2, b)
    gm.vadd_vv(vd=3, vs1=1, vs2=2)
    expected = [(x + y) & 0xFFFFFFFF for x, y in zip(a, b)]
    assert gm.read_reg_direct(3) == expected


#===============================================================
#  LENGHT-AGNOSTIC INSTRUCTIONS TESTS
#===============================================================

def test_vle32_v_contiguous_load():
    gm = make_model_with_vl(4)
    base = 0x1000
    values = [10, 20, 30, 40]
    payload = b"".join(struct.pack("<I", v) for v in values)
    gm.write_mem_bytes(base, payload)

    gm.vle32_v(vd=6, base_addr=base)
    assert gm.read_reg_direct(6) == values


def test_vse32_v_contiguous_store():
    gm = make_model_with_vl(3)  # vl=3, apenas 3 elementos escritos na memoria
    gm.load_reg_direct(7, [111, 222, 333, 444])
    base = 0x2000

    gm.vse32_v(vs3=7, base_addr=base)

    raw = gm.read_mem_bytes(base, 16)  # le os 4 slots, mas só 3 foram escritos
    stored = struct.unpack("<4I", raw)
    assert stored[0] == 111
    assert stored[1] == 222
    assert stored[2] == 333
    # o 4º slot nao foi tocado (ainda zero, pois memoria e inicializada zerada)
    assert stored[3] == 0


def test_vsetvli_clamps_to_vlmax():
    gm = GoldenModel()
    effective_vl = gm.vsetvli(requested_vl=100, sew=SEW.SEW32, lmul=1)
    assert effective_vl == 4  # VLMAX = 128/32 = 4


def test_vle32_v_partial_vl_tail_undisturbed():
    gm = make_model_with_vl(2)
    base = 0x3000
    payload = b"".join(struct.pack("<I", v) for v in [1, 2, 3, 4])
    gm.write_mem_bytes(base, payload)

    gm.load_reg_direct(8, [77, 77, 77, 77])  # valor previo
    gm.vle32_v(vd=8, base_addr=base)

    # apenas 2 elementos carregados, resto mantem valor antigo
    assert gm.read_reg_direct(8) == [1, 2, 77, 77]

#=====================================================
#              __  __   _   ___ _  _ 
#             |  \/  | /_\ |_ _| \| |
#             | |\/| |/ _ \ | || .` |
#             |_|  |_/_/ \_\___|_|\_|
#=====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])