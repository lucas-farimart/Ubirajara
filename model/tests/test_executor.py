#=========================================================================
# TESTES DO EXECUTOR DE PROGRAMA VETORIAL
#  Sequencias de instrucoes, simulando a compilacao de um programa
#-------------------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   25/09/2026
# Update: 25/09/2026
#=========================================================================

import pytest
from model.executor import Executor, UnknownInstructionError
from model.golden_model import GoldenModel


def test_simple_program_vadd():
    gm = GoldenModel()
    gm.load_reg_direct(1, [1, 2, 3, 4])
    gm.load_reg_direct(2, [10, 20, 30, 40])

    executor = Executor(gm)
    program = [
        ("vsetvli", {"vl": 4}),
        ("vadd.vv", {"vd": 3, "vs1": 1, "vs2": 2}),
    ]

    trace = executor.run(program)

    assert gm.read_reg_direct(3) == [11, 22, 33, 44]
    assert len(trace) == 2
    assert trace.entries()[1].mnemonic == "vadd.vv"
    assert trace.entries()[1].result_regs[3] == [11, 22, 33, 44]


def test_program_with_load_and_store():
    import struct

    gm = GoldenModel()
    base_in = 0x1000
    base_out = 0x2000

    values = [5, 6, 7, 8]
    payload = b"".join(struct.pack("<I", v) for v in values)
    gm.write_mem_bytes(base_in, payload)

    executor = Executor(gm)
    program = [
        ("vsetvli", {"vl": 4}),
        ("vle32.v", {"vd": 1, "base": base_in}),
        ("vadd.vv", {"vd": 2, "vs1": 1, "vs2": 1}),
        ("vse32.v", {"vs3": 2, "base": base_out}),
    ]

    trace = executor.run(program)

    expected = [(v * 2) & 0xFFFFFFFF for v in values]
    assert gm.read_reg_direct(2) == expected

    raw = gm.read_mem_bytes(base_out, 16)
    stored = struct.unpack("<4I", raw)
    assert list(stored) == expected

    assert len(trace) == 4


def test_unknown_instruction_raises():
    executor = Executor()
    with pytest.raises(ValueError):
        executor.run([("vmul.vv", {"vd": 1, "vs1": 2, "vs2": 3})])


def test_trace_is_reproducible_for_same_program():
    def build_and_run():
        gm = GoldenModel()
        gm.load_reg_direct(1, [1, 1, 1, 1])
        gm.load_reg_direct(2, [2, 2, 2, 2])
        executor = Executor(gm)
        program = [
            ("vsetvli", {"vl": 4}),
            ("vadd.vv", {"vd": 3, "vs1": 1, "vs2": 2}),
        ]
        return executor.run(program)

    trace_a = build_and_run()
    trace_b = build_and_run()

    assert trace_a == trace_b


def test_trace_serialization_to_json():
    gm = GoldenModel()
    gm.load_reg_direct(1, [1, 2, 3, 4])
    gm.load_reg_direct(2, [10, 20, 30, 40])

    executor = Executor(gm)
    program = [
        ("vsetvli", {"vl": 4}),
        ("vadd.vv", {"vd": 3, "vs1": 1, "vs2": 2}),
    ]

    trace = executor.run(program)
    json_str = trace.to_json()

    assert "vadd.vv" in json_str
    assert "result_regs" in json_str