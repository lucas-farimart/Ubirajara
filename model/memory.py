#===============================================================
# Modelo de memoria simples para cargas e stores contiguos.
# Enderecamento em bytes, little-endian.
#---------------------------------------------------------------
# Author: Lucas Farias Martins
# Email:  lucas.martins@ee.ufcg.edu.br
# Date:   09/09/2026
# Update: 09/09/2026
#===============================================================

class Memory:
    def __init__(self, size_bytes: int = 1 << 20):
        self.size = size_bytes
        self.data = bytearray(size_bytes)

    def load_word(self, addr: int) -> int:
        self._check_bounds(addr, 4)
        return int.from_bytes(self.data[addr:addr + 4], byteorder="little")

    def store_word(self, addr: int, value: int):
        self._check_bounds(addr, 4)
        value &= (1 << 32) - 1
        self.data[addr:addr + 4] = value.to_bytes(4, byteorder="little")

    def load_bytes(self, addr: int, length: int) -> bytes:
        self._check_bounds(addr, length)
        return bytes(self.data[addr:addr + length])

    def store_bytes(self, addr: int, payload: bytes):
        self._check_bounds(addr, len(payload))
        self.data[addr:addr + len(payload)] = payload

    def _check_bounds(self, addr: int, length: int):
        if addr < 0 or addr + length > self.size:
            raise MemoryError(
                f"Acesso fora dos limites: addr={addr}, length={length}, "
                f"size={self.size}"
            )