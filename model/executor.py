"""
=========================================================================
Executor sequencial de programa vetorial.
  Interpreta uma lista de Instruction, aplica seus efeitos sobre o
  GoldenModel e registra cada passo no Trace. Apenas como referencia 
  funcional/comportamental da arquitetura.
-------------------------------------------------------------------------
Author: Lucas Farias Martins
Email:  lucas.martins@ee.ufcg.edu.br
Date:   25/09/2026
Update: 25/09/2026
=========================================================================
"""

from .instruction import Instruction, program_from_tuples
from .golden_model import GoldenModel
from .trace import Trace, TraceEntry

class Executor:
    def __init__(self, model: GoldenModel = None):
        self.model = model if model is not None else GoldenModel()
        self.trace = Trace()

    def run(self, raw_program: list) -> Trace:
        """
        Executa um programa dado como lista de tuplas (mnemonic, operandos)
        ou lista de objetos Instruction ja validados.
        """
        program = self._normalize_program(raw_program)
        self.trace.clear()

        for index, instr in enumerate(program):
            self._execute_one(index, instr)

        return self.trace

    def _normalize_program(self, raw_program: list) -> list:
        if not raw_program:
            return []
        if isinstance(raw_program[0], Instruction):
            return raw_program
        return program_from_tuples(raw_program)

    def _execute_one(self, index: int, instr: Instruction):
        handler = getattr(self, f"_handle_{self._safe_name(instr.mnemonic)}", None)
        if handler is None:
            raise UnknownInstructionError(
                f"Nenhum handler para a instrucao '{instr.mnemonic}'"
            )
        handler(index, instr)

    @staticmethod
    def _safe_name(mnemonic: str) -> str:
        # converte "vadd.vv" -> "vadd_vv", "vle32.v" -> "vle32_v"
        return mnemonic.replace(".", "_")

    # ------------------------------------------------------------------
    # Handlers por instrucao
    # ------------------------------------------------------------------

    def _handle_vsetvli(self, index: int, instr: Instruction):
        vl = instr.operands["vl"]
        effective_vl = self.model.vsetvli(requested_vl=vl)

        self.trace.add(TraceEntry(
            index=index,
            mnemonic=instr.mnemonic,
            operands=dict(instr.operands),
            vl_at_execution=effective_vl,
            result_regs={},
        ))

    def _handle_vadd_vv(self, index: int, instr: Instruction):
        self._execute_binop("vadd.vv", self.model.vadd_vv, index, instr)

    def _handle_vsub_vv(self, index: int, instr: Instruction):
        self._execute_binop("vsub.vv", self.model.vsub_vv, index, instr)

    def _handle_vand_vv(self, index: int, instr: Instruction):
        self._execute_binop("vand.vv", self.model.vand_vv, index, instr)

    def _handle_vor_vv(self, index: int, instr: Instruction):
        self._execute_binop("vor.vv", self.model.vor_vv, index, instr)

    def _handle_vxor_vv(self, index: int, instr: Instruction):
        self._execute_binop("vxor.vv", self.model.vxor_vv, index, instr)

    def _execute_binop(self, mnemonic: str, op_fn, index: int, instr: Instruction):
        vd = instr.operands["vd"]
        vs1 = instr.operands["vs1"]
        vs2 = instr.operands["vs2"]
        mask = instr.operands.get("mask")

        op_fn(vd=vd, vs1=vs1, vs2=vs2, mask=mask)

        self.trace.add(TraceEntry(
            index=index,
            mnemonic=mnemonic,
            operands=dict(instr.operands),
            vl_at_execution=self.model.state.vl,
            result_regs={vd: self.model.read_reg_direct(vd)},
        ))

    def _handle_vle32_v(self, index: int, instr: Instruction):
        vd = instr.operands["vd"]
        base = instr.operands["base"]
        mask = instr.operands.get("mask")

        self.model.vle32_v(vd=vd, base_addr=base, mask=mask)

        self.trace.add(TraceEntry(
            index=index,
            mnemonic="vle32.v",
            operands=dict(instr.operands),
            vl_at_execution=self.model.state.vl,
            result_regs={vd: self.model.read_reg_direct(vd)},
        ))

    def _handle_vse32_v(self, index: int, instr: Instruction):
        vs3 = instr.operands["vs3"]
        base = instr.operands["base"]
        mask = instr.operands.get("mask")

        self.model.vse32_v(vs3=vs3, base_addr=base, mask=mask)

        vl = self.model.state.vl
        mem_writes = {}

        for i in range(vl):
            if mask is not None and not mask[i]:
                continue

            addr = base + i * 4
            raw = self.model.read_mem_bytes(addr, 4)
            value = int.from_bytes(raw, byteorder="little")
            mem_writes[hex(addr)] = value
            
        # for i in range(vl):
        #     if mask is not None and not mask[i]:
        #         continue
        #     addr = base + i * 4
        #     mem_writes[addr] = self.model.read_mem_bytes(addr, 4)

        self.trace.add(TraceEntry(
            index=index,
            mnemonic="vse32.v",
            operands=dict(instr.operands),
            vl_at_execution=vl,
            result_regs={},
            mem_writes=mem_writes,
        ))

class UnknownInstructionError(Exception):
    pass
