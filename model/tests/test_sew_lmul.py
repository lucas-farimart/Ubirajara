#==================================================================
# Testes de comprimentos variados obtidos por combinacoes de 
# SEW e LMUL.
#------------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   06/10/2026
# Update: 06/10/2026
#==================================================================

import pytest
from model.golden_model import GoldenModel
from model.vector_state import SEW


def test_vlmax_sew8_lmul1():
    gm = GoldenModel()
    vl = gm.vsetvli(requested_vl=100, sew=SEW.SEW8, lmul=1)
    assert vl == 16  # 128 / 8 = 16


def test_vlmax_sew16_lmul1():
    gm = GoldenModel()
    vl = gm.vsetvli(requested_vl=100, sew=SEW.SEW16, lmul=1)
    assert vl == 8  # 128 / 16 = 8


def test_vlmax_sew32_lmul1():
    gm = GoldenModel()
    vl = gm.vsetvli(requested_vl=100, sew=SEW.SEW32, lmul=1)
    assert vl == 4  # 128 / 32 = 4


def test_vlmax_sew32_lmul2():
    gm = GoldenModel()
    vl = gm.vsetvli(requested_vl=100, sew=SEW.SEW32, lmul=2)
    assert vl == 8  # (128 / 32) * 2 = 8


def test_vlmax_sew8_lmul4():
    gm = GoldenModel()
    vl = gm.vsetvli(requested_vl=100, sew=SEW.SEW8, lmul=4)
    assert vl == 64  # (128 / 8) * 4 = 64


def test_vadd_vv_sew8():
    gm = GoldenModel()
    gm.vsetvli(requested_vl=16, sew=SEW.SEW8, lmul=1)

    a = list(range(16))
    b = [10] * 16
    gm.load_reg_direct(1, a)
    gm.load_reg_direct(2, b)

    gm.vadd_vv(vd=3, vs1=1, vs2=2)

    expected = [(x + 10) & 0xFF for x in a]
    assert gm.read_reg_direct(3) == expected


def test_vadd_vv_sew8_overflow_wraps_mod_256():
    gm = GoldenModel()
    gm.vsetvli(requested_vl=16, sew=SEW.SEW8, lmul=1)

    a = [250] * 16
    b = [10] * 16
    gm.load_reg_direct(1, a)
    gm.load_reg_direct(2, b)

    gm.vadd_vv(vd=3, vs1=1, vs2=2)

    expected = [(250 + 10) & 0xFF] * 16
    assert gm.read_reg_direct(3) == expected


def test_vadd_vv_sew32_lmul2_uses_register_group():
    gm = GoldenModel()
    gm.vsetvli(requested_vl=8, sew=SEW.SEW32, lmul=2)

    # com lmul=2, vd=0 ocupa fisicamente os registradores 0 e 1
    a = [1, 2, 3, 4, 5, 6, 7, 8]
    b = [10, 20, 30, 40, 50, 60, 70, 80]
    gm.load_reg_direct(0, a)
    gm.load_reg_direct(2, b)

    gm.vadd_vv(vd=4, vs1=0, vs2=2)

    expected = [(x + y) for x, y in zip(a, b)]
    assert gm.read_reg_direct(4) == expected


def test_vadd_vv_invalid_base_reg_for_lmul_raises():
    gm = GoldenModel()
    gm.vsetvli(requested_vl=8, sew=SEW.SEW32, lmul=2)

    with pytest.raises(ValueError):
        # vd=1 nao e multiplo de group_size=2, deve falhar
        gm.load_reg_direct(1, [0] * 8)


def test_vle_vse_sew16_contiguous():
    gm = GoldenModel()
    gm.vsetvli(requested_vl=8, sew=SEW.SEW16, lmul=1)

    base = 0x1000
    values = list(range(100, 108))
    payload = b"".join(v.to_bytes(2, byteorder="little") for v in values)
    gm.write_mem_bytes(base, payload)

    gm.vle_v(vd=1, base_addr=base)
    assert gm.read_reg_direct(1) == values

    base_out = 0x2000
    gm.vse_v(vs3=1, base_addr=base_out)

    raw = gm.read_mem_bytes(base_out, 16)
    stored = [int.from_bytes(raw[i:i+2], byteorder="little") for i in range(0, 16, 2)]
    assert stored == values


def test_partial_vl_tail_undisturbed_sew16():
    gm = GoldenModel()
    gm.vsetvli(requested_vl=4, sew=SEW.SEW16, lmul=1)  # vlmax=8, vl=4

    gm.load_reg_direct(1, [1, 2, 3, 4, 5, 6, 7, 8])
    gm.load_reg_direct(2, [10, 10, 10, 10, 10, 10, 10, 10])
    gm.load_reg_direct(3, [99, 99, 99, 99, 99, 99, 99, 99])

    gm.vadd_vv(vd=3, vs1=1, vs2=2)

    # apenas 4 primeiros elementos atualizados, resto mantem 99
    assert gm.read_reg_direct(3) == [11, 12, 13, 14, 99, 99, 99, 99]


def test_switching_sew_between_instructions():
    """
    Verifica que mudar sew entre instrucoes reinterpreta corretamente
    o mesmo armazenamento fisico, sem misturar estado antigo.
    """
    gm = GoldenModel()

    gm.vsetvli(requested_vl=4, sew=SEW.SEW32, lmul=1)
    gm.load_reg_direct(1, [0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00])

    # muda para sew8: mesmo registrador fisico, agora visto como 16 bytes
    gm.vsetvli(requested_vl=16, sew=SEW.SEW8, lmul=1)
    reinterpreted = gm.read_reg_direct(1)

    assert len(reinterpreted) == 16
    # little-endian: primeiro byte do primeiro elemento sew32 e 0x44
    assert reinterpreted[0] == 0x44
    assert reinterpreted[1] == 0x33
    assert reinterpreted[2] == 0x22
    assert reinterpreted[3] == 0x11


if __name__ == "__main__":
    pytest.main([__file__, "-v"])