# 🔧 Scripts — Utilitários e Experimentos

> **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Lesina Giordano · [://github.com](https://://github.com)

---

## 🎯 O que é esta pasta

Scripts auxiliares, experimentos e geradores que **não fazem parte do pipeline
de produção** (`src/gate4/`) mas documentam o processo de desenvolvimento.

---

## 📁 Arquivos

| Arquivo | Descrição |
|---|---|
| `g10_churn_project.py` | Protótipo inicial do modelo de churn (versão anterior ao pipeline) |
| `g16_performance.py` | Benchmarks de performance: Pandas vs vetorização vs DuckDB |
| `generators_G18_1.py` | Gerador auxiliar usado durante o desenvolvimento do M0 |
| `Guia 16C benchmark_pandas.py` | Engine de benchmark real para transição de lógicas SQL para Pandas |

---

## 📊 Guia 16C — Benchmark Pandas

O script `Guia 16C benchmark_pandas.py` analisa a eficiência de processamento e armazenamento simulando a volumetria real do GATE4 e MEDE.

### 🧪 O que ele avalia:
1. **Abordagens de Loop**: Comparativo de tempo entre `loop (iterrows)`, `apply` e vetorização.
2. **Tipagem de Memória**: Otimização por tipos de coluna (`object` x `category` x `int32`).
3. **Persistência de Dados**: Comparativo de tamanho e tempo entre CSV x Parquet.
4. **Motores de Execução**: Performance de Pandas x DuckDB lendo o mesmo arquivo Parquet.

### 🚀 Como Executar
Antes de rodar, instale as dependências adicionais no seu ambiente virtual (`.venv`):
```bash
pip install pyarrow duckdb
```

Para executar no Git Bash/Windows sem erros de argumento por conta dos espaços no nome, utilize aspas duplas:
```bash
python "Guia 16C benchmark_pandas.py"
```

As saídas geradas serão exibidas diretamente no terminal e consolidadas no arquivo local `benchmark_resultado.json`.

---

## ⚠️ Atenção

Estes scripts são **experimentais** — podem depender de dados locais ou
configurações específicas. O código de produção validado está em `src/gate4/`.
