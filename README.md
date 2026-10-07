# Ubirajara

O Ubirajara é (ou será) um processador vetorial RISC-V, ainda em desenvolvimento. O modelo em alto nível está sendo testado em Python antes de ir para o HDL.

## Atualizações

Árvore de diretórios:

`
model/
├── vector_state.py       # reescrito: registrador fisico em bytes, SEW/LMUL dinamicos
├── vector_isa.py         # reescrito: leitura/escrita por elemento respeitando SEW/LMUL
├── memory.py               (sem mudancas)
├── golden_model.py       # atualizado: vsetvli aceita sew e lmul
├── executor.py           # atualizado: vsetvli propaga sew e lmul
└── tests/
    └── test_sew_lmul.py  # novo: casos de SEW/LMUL variados
`
