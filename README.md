# Ubirajara

O Ubirajara é um projeto em desenvolvimento para criar um coprocessador vetorial inspirado na arquitetura RISCV. O foco atual está em um modelo funcional executável em Python, que servirá como referência para futuras implementações em SystemC e SystemVerilog.

## Estado atual

O projeto possui um modelo Python com suporte a:

- **VLEN de 128 bits** e **ELEN de 32 bits**;
- Elementos inteiros com **SEW de 8, 16 e 32 bits**;
- **LMUL de 1, 2, 4 e 8**;
- Grupos de registradores físicos para LMUL > 1;
- Operações vetoriais: ADD, SUB, AND, OR e XOR;
- Loads/Stores contíguos;
- `vsetvli` com cálculo de VLMAX e saturação de `vl`;
- Políticas tail-undisturbed e mask-undisturbed;
- Execução sequencial de programas representados por instruções;
- Trace serializável em JSON;
- Programas strip-mined para processar vetores maiores que VLMAX.

A fórmula usada para calcular o número máximo de elementos é:

$$ VLMAX = \frac{VLEN}{SEW} \times LMUL $$

Por exemplo, com `VLEN=128`, `SEW=32` e `LMUL=1`, `VLMAX=4`. Vetores maiores são processados em blocos, incluindo uma última iteração residual quando necessário.

## Organização do projeto

```text
.
├── docs/
│   └── specification/
│       ├── main.tex
│       ├── preamble.tex
│       ├── references.bib
│       └── sections/
├── model/
│   ├── executor.py
│   ├── golden_model.py
│   ├── instruction.py
│   ├── memory.py
│   ├── strip_mining.py
│   ├── trace.py
│   ├── vector_isa.py
│   ├── vector_state.py
│   └── tests/
└── README.md
```

A estrutura de documentação em LaTeX separa o arquivo principal, o preâmbulo e as seções do documento. A implementação SystemC e o RTL ainda são etapas futuras.

## Verificação

Os testes automatizados são executados a partir da raiz do repositório:

```bash
pytest -v
```

Na última execução registrada, **31 testes passaram e 7 falharam**. Todas as falhas têm a mesma causa: o handler de `vsetvli` em `model/executor.py` referencia `SEW`, mas esse nome não está definido no arquivo. Os testes unitários do modelo e a geração dos programas strip-mined passaram; as falhas ocorrem nos testes que executam programas pelo `Executor`.

A suíte precisa ser executada novamente após corrigir esse import. Portanto, o modelo ainda não está validado integralmente de ponta a ponta.

## Como inspecionar um trace

A partir da raiz do repositório:

```bash
python -m model.inspect_trace
```

O script executa um exemplo strip-mined e apresenta um resumo das instruções e dos efeitos observados.

## Documentação em LaTeX

A especificação do projeto está sendo organizada em arquivos LaTeX separados sob `docs/specification/`. O arquivo `main.tex` reúne as seções e o preâmbulo contém os pacotes e configurações comuns.

A compilação pode ser feita a partir do diretório da especificação:

```bash
cd docs/specification
pdflatex main.tex
pdflatex main.tex
```

## Próximas etapas

- Corrigir a referência não definida a `SEW` no executor e repetir toda a suíte de testes.
- Generalizar o strip-mining para trabalhar com diferentes valores de SEW e LMUL.
- Consolidar a semântica e a nomenclatura das instruções de memória, distinguindo SEW de EEW quando necessário.
- Ampliar os testes de execução end-to-end para combinações variadas de SEW e LMUL.
- Avançar para uma implementação de referência em SystemC.
- Desenvolver uma implementação sintetizável em SystemVerilog e iniciar a verificação com as ferramentas Cadence.

## Ferramentas previstas

- **Xcelium** e **SimVision** para simulação e depuração;
- **Genus** para síntese lógica;
- **LaTeX** para a documentação da especificação.
