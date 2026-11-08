# 🔧 Scripts — Utilitários e Experimentos

> **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)

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

---

## ⚠️ Atenção

Estes scripts são **experimentais** — podem depender de dados locais ou
configurações específicas. O código de produção validado está em `src/gate4/`.
