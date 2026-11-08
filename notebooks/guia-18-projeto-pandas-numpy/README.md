# 🏗️ Guia 18 — Projeto Pandas/NumPy com ER do GATE4

> **Trilha:** Fundamentos & Data Science · **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)

---

## 🎯 Objetivo

Aplicar Pandas e NumPy sobre o **ER real do GATE4** (17 tabelas, arquitetura
multi-empresa) — geração de dados sintéticos, limpeza, regras de negócio e
análise exploratória. É o laboratório onde os módulos M0–M8 foram construídos.

---

## 📁 Arquivos

| Arquivo | Tema |
|---|---|
| `01_teste_pandas.py` | Primeiros passos: Series, DataFrame, leitura e filtros |
| `02_series_temporais_pandas.py` | resample, rolling, shift — faturamento mensal |
| `03_numpy_eda_visualizacao.py` | NumPy, EDA completa e 7 gráficos do GATE4 |
| `04_machine_learning_churn.py` | Scikit-Learn: ABT, pipeline, ROC-AUC e Lift |

---

## ▶️ Como rodar

```bash
source .venv/Scripts/activate
pip install pandas numpy matplotlib seaborn scikit-learn

python 01_teste_pandas.py
python 02_series_temporais_pandas.py
python 03_numpy_eda_visualizacao.py   # gera saidas/*.png
python 04_machine_learning_churn.py
```

---

## 🗺️ Relação com os módulos de produção

Estes scripts são os **cadernos de estudo** que geraram os módulos de produção
em `src/gate4/`. Cada descoberta aqui virou um módulo testado e orquestrado:

| Script de estudo | Módulo de produção |
|---|---|
| `01_teste_pandas.py` | `src/gate4/g18_m0_gerador.py` |
| `03_numpy_eda_visualizacao.py` | `src/gate4/g18_m1_qualidade.py` + `g18_m2_limpeza.py` |
| `04_machine_learning_churn.py` | `src/gate4/g18_guia1_churn.py` |

---

## 🗺️ Trilha de estudos

Guia 19 — Setup VS Code/Python ✅ Concluído
Guia 18 — Projeto Pandas/NumPy ✅ Este módulo
Guia 1 — SQL → Pandas → ML ✅ Concluído
Guia 10 — Churn do GATE4 ✅ Concluído
Guia 2 — Séries Temporais ✅ Concluído
Guia 3 — FastAPI + Docker ✅ Concluído
