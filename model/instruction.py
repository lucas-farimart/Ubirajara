"""
=========================================================================
Representacao formal de uma instrucao vetorial.
  Cada instrucao e uma tupla imutavel (mnemonic, operandos), validada
  contra um esquema minimo antes da execucao. Isso evita erros silenciosos
  de chave incorreta ou operando faltando.
-------------------------------------------------------------------------
Author: Lucas Farias Martins
Email:  lucas.martins@ee.ufcg.edu.br
Date:   25/09/2026
Update: 25/09/2026
=========================================================================
"""

from dataclasses import dataclass, field
from typing import Any

#=======================================================================
#  Mnemonico -> Conjunto de campos obrigatorios
#=======================================================================
INSTRUCTION_SCHEMA = {
    "vsetvli":  {"vl"},
    "vadd.vv":  {"vd",  "vs1", "vs2"},
    "vsub.vv":  {"vd",  "vs1", "vs2"},
    "vand.vv":  {"vd",  "vs1", "vs2"},
    "vor.vv":   {"vd",  "vs1", "vs2"},
    "vxor.vv":  {"vd",  "vs1", "vs2"},
    "vle32.v":  {"vd",  "base"},
    "vse32.v":  {"vs3", "base"},
}

#=======================================================================
#  Campos opcionais permitidos por instrucao
#=======================================================================
OPTIONAL_FIELDS = {
    "vadd.vv":  {"mask"},
    "vsub.vv":  {"mask"},
    "vand.vv":  {"mask"},
    "vor.vv":   {"mask"},
    "vxor.vv":  {"mask"},
    "vle32.v":  {"mask"},
    "vse32.v":  {"mask"},
}

#=======================================================================
#       ___ _  _ ___ _____ ___ _   _  ___ _____ ___ ___  _  _ 
#      |_ _| \| / __|_   _| _ \ | | |/ __|_   _|_ _/ _ \| \| |
#       | || .` \__ \ | | |   / |_| | (__  | |  | | (_) | .` |
#      |___|_|\_|___/ |_| |_|_\\___/ \___| |_| |___\___/|_|\_|
#=======================================================================                                                      

@dataclass(frozen=True)
class Instruction:
    """
    Instrucao imutavel do programa.
        mnemonic: nome da instrucao, ex: "vadd.vv"
        operands: dicionario de operandos nomeados
    """
    mnemonic: str
    operands: dict = field(default_factory=dict)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if self.mnemonic not in INSTRUCTION_SCHEMA:
            raise ValueError(
                f"Instrucao desconhecida: '{self.mnemonic}'"
            )

        required = INSTRUCTION_SCHEMA[self.mnemonic]
        optional = OPTIONAL_FIELDS.get(self.mnemonic, set())
        allowed  = required | optional
        provided = set(self.operands.keys())

        missing = required - provided
        if missing:
            raise ValueError(
                f"Operandos faltando em '{self.mnemonic}': {missing}"
            )

        unknown = provided - allowed
        if unknown:
            raise ValueError(
                f"Operandos desconhecidos em '{self.mnemonic}': {unknown}"
            )

    def __repr__(self) -> str:
        ops = ", ".join(f"{k}={v}" for k, v in self.operands.items())
        return f"{self.mnemonic}({ops})"


def program_from_tuples(raw_program: list) -> list:
    """
    Converte uma lista de tuplas (mnemonic, dict) em uma lista de
    objetos Instruction validados.

    Exemplo de entrada:
        [
            ("vsetvli", {"vl": 4}),
            ("vadd.vv", {"vd": 3, "vs1": 1, "vs2": 2}),
        ]
    """
    return [Instruction(mnemonic, operands) for mnemonic, operands in raw_program]