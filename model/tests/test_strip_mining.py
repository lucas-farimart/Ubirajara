#=========================================================================
# TESTES DE STRIP-MINING: 
#  Vetores logicos maiores, iguais e menores que VLMAX, incluindo o caso 
#  de tamanho residual.
#-------------------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   26/09/2026
# Update: 26/09/2026
#=========================================================================

import pytest
from model.golden_model import GoldenModel
from model.strip_mining import (
    build_strip_mined_vadd_program,
    run_strip_mined_vadd,
    vlmax_for_sew32,
)


def test_vlmax_is_four_for_current_config():
    assert vlmax_for_sew32() == 4


def test_program_exact_multiple_of_vlmax():
    # 8 elementos, vlmax=4 -> exatamente duas iteracoes, sem residual
    program = build_strip_mined_vadd_program(
        total_elements=8, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )

    vsetvli_instructions = [i for i in program if i[0] == "vsetvli"]
    assert len(vsetvli_instructions) == 2
    assert vsetvli_instructions[0][1]["vl"] == 4
    assert vsetvli_instructions[1][1]["vl"] == 4


def test_program_with_residual_tail():
    # 10 elementos, vlmax=4 -> duas iteracoes cheias e uma residual de 2
    program = build_strip_mined_vadd_program(
        total_elements=10, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )

    vsetvli_instructions = [i for i in program if i[0] == "vsetvli"]
    assert len(vsetvli_instructions) == 3
    assert vsetvli_instructions[0][1]["vl"] == 4
    assert vsetvli_instructions[1][1]["vl"] == 4
    assert vsetvli_instructions[2][1]["vl"] == 2  # residual


def test_program_smaller_than_vlmax():
    # 3 elementos, vlmax=4 -> uma unica iteracao, residual desde o inicio
    program = build_strip_mined_vadd_program(
        total_elements=3, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )

    vsetvli_instructions = [i for i in program if i[0] == "vsetvli"]
    assert len(vsetvli_instructions) == 1
    assert vsetvli_instructions[0][1]["vl"] == 3


def test_program_zero_elements_produces_empty_program():
    program = build_strip_mined_vadd_program(
        total_elements=0, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )
    assert program == []


def test_addresses_advance_correctly_between_iterations():
    program = build_strip_mined_vadd_program(
        total_elements=10, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )

    load_a_instructions = [
        i for i in program if i[0] == "vle32.v" and i[1]["base"] >= 0x1000 and i[1]["base"] < 0x2000
    ]

    # tres iteracoes -> tres loads do vetor a, com enderecos crescentes
    addresses = [i[1]["base"] for i in load_a_instructions]
    assert addresses == [0x1000, 0x1010, 0x1020]  # +4 elementos * 4 bytes cada passo


def test_end_to_end_exact_multiple():
    gm = GoldenModel()
    a_values = [1, 2, 3, 4, 5, 6, 7, 8]
    b_values = [10, 20, 30, 40, 50, 60, 70, 80]

    trace, c_values = run_strip_mined_vadd(
        gm, a_values, b_values, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )

    expected = [(a + b) for a, b in zip(a_values, b_values)]
    assert c_values == expected


def test_end_to_end_with_residual_tail():
    gm = GoldenModel()
    a_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    b_values = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    trace, c_values = run_strip_mined_vadd(
        gm, a_values, b_values, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )

    expected = [a + 1 for a in a_values]
    assert c_values == expected

    # verifica que o trace contem tres passagens de vsetvli
    vsetvli_entries = [e for e in trace.entries() if e.mnemonic == "vsetvli"]
    assert len(vsetvli_entries) == 3
    assert vsetvli_entries[-1].vl_at_execution == 2  # residual


def test_end_to_end_single_residual_iteration():
    gm = GoldenModel()
    a_values = [100, 200, 300]
    b_values = [1, 2, 3]

    trace, c_values = run_strip_mined_vadd(
        gm, a_values, b_values, base_a=0x1000, base_b=0x2000, base_c=0x3000
    )

    assert c_values == [101, 202, 303]


def test_end_to_end_mismatched_lengths_raises():
    gm = GoldenModel()
    with pytest.raises(ValueError):
        run_strip_mined_vadd(
            gm, [1, 2, 3], [1, 2], base_a=0x1000, base_b=0x2000, base_c=0x3000
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])