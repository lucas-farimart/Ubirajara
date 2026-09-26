"""
=========================================================================
Script de inspecao visual do trace JSON para um caso de strip-mining
com residual. Executa o kernel de soma vetorial sobre um vetor de 10
elementos (vlmax=4), o que produz duas iteracoes cheias e uma residual
de 2 elementos.
    Uso: python -m model.inspect_trace
-------------------------------------------------------------------------
Author: Lucas Farias Martins
Email:  lucas.martins@ee.ufcg.edu.br
Date:   26/09/2026
Update: 26/09/2026
=========================================================================
"""

import json

from model.golden_model import GoldenModel
from model.strip_mining import run_strip_mined_vadd


def main():
    gm = GoldenModel()

    a_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    b_values = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]

    trace, c_values = run_strip_mined_vadd(
        gm,
        a_values,
        b_values,
        base_a=0x1000,
        base_b=0x2000,
        base_c=0x3000,
    )

    print("=" * 70)
    print("valores de entrada")
    print("=" * 70)
    print(f"a_values: {a_values}")
    print(f"b_values: {b_values}")
    print()

    print("=" * 70)
    print("resultado final (lido da memoria)")
    print("=" * 70)
    print(f"c_values: {c_values}")
    print()

    # print("=" * 70)
    # print("trace completo (json)")
    # print("=" * 70)
    # print(trace.to_json())
    # print()

    print("=" * 70)
    print("resumo por instrucao")
    print("=" * 70)
    for entry in trace.entries():
        summary = _format_entry_summary(entry)
        print(summary)


def _format_entry_summary(entry) -> str:
    base = f"[{entry.index:02d}] {entry.mnemonic:10s} vl={entry.vl_at_execution}"

    if entry.result_regs:
        regs_str = ", ".join(
            f"v{idx}={values}" for idx, values in entry.result_regs.items()
        )
        base += f"  regs: {regs_str}"

    if entry.mem_writes:
        addrs = sorted(entry.mem_writes.keys())
        addr_range = f"{addrs[0]}..{addrs[-1]}" if addrs else "none"
        base += f"  mem_writes: {len(entry.mem_writes)} enderecos ({addr_range})"

    return base

if __name__ == "__main__":
    main()