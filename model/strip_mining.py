"""
=========================================================================
Suporte a strip-mining: geracao de programas que processam vetores
logicos maiores que VLMAX, iterando com tamanho residual.
-------------------------------------------------------------------------
Author: Lucas Farias Martins
Email:  lucas.martins@ee.ufcg.edu.br
Date:   26/09/2026
Update: 26/09/2026
=========================================================================
"""

from .executor import Executor
from .golden_model import GoldenModel
from .vector_state import VLEN

ELEMENT_SIZE_BYTES = 4  # SEW = 32 bits nesta versao


def vlmax_for_sew32() -> int:
    """Retorna VLMAX para SEW=32, LMUL=1."""
    return VLEN // 32


def build_strip_mined_vadd_program(
    total_elements: int,
    base_a: int,
    base_b: int,
    base_c: int,
    work_vd: int = 1,
    work_vs1: int = 2,
    work_vs2: int = 3,
) -> list:
    """
    Constroi um programa que calcula c[i] = a[i] + b[i] para
    total_elements elementos, usando strip-mining com tamanho
    residual na ultima iteracao.

    Os enderecos base_a, base_b, base_c avancam a cada iteracao
    de acordo com o numero de elementos processados naquela passada.

    Parametros:
        total_elements: tamanho logico do vetor, pode ser maior que VLMAX
        base_a: endereco base do vetor de entrada a
        base_b: endereco base do vetor de entrada b
        base_c: endereco base do vetor de saida c
        work_vd, work_vs1, work_vs2: registradores vetoriais usados
            como area de trabalho, reutilizados a cada iteracao

    Retorna:
        lista de tuplas (mnemonic, operandos) pronta para o Executor
    """
    if total_elements < 0:
        raise ValueError("total_elements nao pode ser negativo")

    vlmax = vlmax_for_sew32()
    program = []

    remaining = total_elements
    offset_elements = 0

    while remaining > 0:
        # o hardware satura automaticamente em vlmax; aqui deixamos
        # explicito para o trace ficar didaticamente claro
        current_vl = min(remaining, vlmax)

        addr_a = base_a + offset_elements * ELEMENT_SIZE_BYTES
        addr_b = base_b + offset_elements * ELEMENT_SIZE_BYTES
        addr_c = base_c + offset_elements * ELEMENT_SIZE_BYTES

        program.append(("vsetvli", {"vl": current_vl}))
        program.append(("vle32.v", {"vd": work_vs1, "base": addr_a}))
        program.append(("vle32.v", {"vd": work_vs2, "base": addr_b}))
        program.append(("vadd.vv", {"vd": work_vd, "vs1": work_vs1, "vs2": work_vs2}))
        program.append(("vse32.v", {"vs3": work_vd, "base": addr_c}))

        offset_elements += current_vl
        remaining -= current_vl

    return program


def run_strip_mined_vadd(
    model: GoldenModel,
    a_values: list,
    b_values: list,
    base_a: int,
    base_b: int,
    base_c: int,
):
    """
    Funcao de conveniencia: escreve a_values e b_values na memoria do
    modelo, executa o kernel de soma vetorial com strip-mining, e
    retorna (trace, c_values) onde c_values e a lista de resultados
    lidos de volta da memoria.

    len(a_values) deve ser igual a len(b_values).
    """
    import struct

    if len(a_values) != len(b_values):
        raise ValueError("a_values e b_values devem ter o mesmo tamanho")

    total_elements = len(a_values)

    payload_a = b"".join(struct.pack("<I", v & 0xFFFFFFFF) for v in a_values)
    payload_b = b"".join(struct.pack("<I", v & 0xFFFFFFFF) for v in b_values)

    model.write_mem_bytes(base_a, payload_a)
    model.write_mem_bytes(base_b, payload_b)

    program = build_strip_mined_vadd_program(
        total_elements=total_elements,
        base_a=base_a,
        base_b=base_b,
        base_c=base_c,
    )

    executor = Executor(model)
    trace = executor.run(program)

    raw_c = model.read_mem_bytes(base_c, total_elements * ELEMENT_SIZE_BYTES)
    c_values = list(struct.unpack(f"<{total_elements}I", raw_c)) if total_elements > 0 else []

    return trace, c_values