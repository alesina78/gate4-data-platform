# 📈 Guia 2 — Séries Temporais com Pandas

> **Trilha:** Fundamentos & Data Science · **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)

---

## 🎯 Objetivo

Implementar os conceitos de **séries temporais** em Python/Pandas usando dados
reais do GATE4 — com ênfase em **tradução SQL → Pandas** e eliminação de
**Data Leakage temporal**.

---

## 📁 Arquivos

| Arquivo | Conceito principal | Dificuldade |
|---|---|---|
| `ex01_sql_para_pandas.py` | `resample` + `rolling` = `GROUP BY` + `AVG OVER` | ⭐ Iniciante |
| `ex02_leakage_temporal.py` | 3 tipos de leakage e como corrigir | ⭐⭐ Intermediário |
| `ex03_previsao_faturamento_gate4.py` | Pipeline completo: Baseline × Random Forest | ⭐⭐⭐ Avançado |

---

## ▶️ Como rodar

```bash
source .venv/Scripts/activate
pip install pandas numpy scikit-learn

python ex01_sql_para_pandas.py
python ex02_leakage_temporal.py
python ex03_previsao_faturamento_gate4.py
```

---

## 🔵 SQL → Pandas (referência rápida)

| Oracle SQL | Pandas |
|---|---|
| `GROUP BY TRUNC(data,'MM')` | `df.resample('MS').sum()` |
| `LAG(v,1) OVER (ORDER BY mes)` | `s.shift(1)` |
| `AVG(v) OVER (ROWS BETWEEN 2 PRECEDING...)` | `s.rolling(3).mean()` |
| `(v - LAG(v)) / LAG(v)` | `s.pct_change()` |
| `CONNECT BY LEVEL` (calendário) | `pd.date_range(...)` |
| `NVL(col, 0)` em LEFT JOIN com datas | `.asfreq('MS', fill_value=0)` |

---

## ⚠️ Data Leakage — os 3 erros clássicos

```python
# ❌ ERRADO — rolling inclui o mês previsto
t['media_3m'] = t.fat.rolling(3).mean()

# ✅ CORRETO — shift(1) garante apenas dados do passado
t['media_3m'] = t.fat.shift(1).rolling(3).mean()
```

```python
# ❌ ERRADO — split aleatório mistura futuro no treino
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2)

# ✅ CORRETO — corte temporal
X_tr, y_tr = X.loc[:'2025-06-01'], y.loc[:'2025-06-01']
X_te, y_te = X.loc['2025-07-01':], y.loc['2025-07-01':]
```

---

## 🗺️ Trilha de estudos
