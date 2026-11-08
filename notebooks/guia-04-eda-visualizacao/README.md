# 📊 Guia 4 — EDA + Visualização com NumPy, Pandas & Seaborn

> **Trilha:** Fundamentos & Data Science · **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)  
> **Baseado em:** `notebooks/03_numpy_eda_visualizacao.py`

---

## 🎯 Objetivo

Dominar a **Análise Exploratória de Dados (EDA)** usando NumPy, Pandas e Seaborn —
com ênfase em tradução SQL→Python e nos 7 gráficos reais do projeto GATE4.

---

## 📁 Arquivos

| Arquivo | Tema | Dificuldade |
|---|---|---|
| `ex07_numpy_fundamentos.py` | Vetorização, estatísticas, np.where/select | ⭐⭐ |
| `ex08_eda_completo_gate4.py` | EDA completa: nulos, outliers IQR, groupby + 4 exercícios | ⭐⭐⭐ |
| `ex09_visualizacoes_avancadas.py` | Os 7 gráficos explicados e recriados | ⭐⭐⭐ |

---

## ▶️ Como rodar

```bash
source .venv/Scripts/activate
pip install numpy pandas matplotlib seaborn scikit-learn

python ex07_numpy_fundamentos.py    # NumPy fundamentos
python ex08_eda_completo_gate4.py   # EDA + 4 exercícios (gera saidas/ex8_*)
python ex09_visualizacoes_avancadas.py  # 7 gráficos (atualiza saidas/)
```

---

## 🔵 SQL → NumPy/Pandas (referência rápida)

| Oracle SQL | NumPy / Pandas | Observação |
|---|---|---|
| `AVG(col)` | `np.mean(arr)` | Média aritmética |
| `MEDIAN(col)` | `np.median(arr)` | Mais robusta em cauda longa |
| `STDDEV(col)` | `np.std(arr, ddof=1)` | **ddof=1** = amostral = Oracle |
| `PERCENTILE_CONT(0.9)` | `np.percentile(arr, 90)` | P90 |
| `CASE WHEN c THEN a ELSE b END` | `np.where(c, a, b)` | 2 saídas |
| `CASE WHEN c1 WHEN c2 ELSE END` | `np.select([c1,c2],[v1,v2],default)` | N saídas |
| `GROUP BY plano WITH AVG, MAX` | `df.groupby('plano').agg(...)` | Múltiplas agregações |
| `PERCENTILE_CONT OVER (PARTITION BY plano)` | `df.groupby('plano').transform(lambda s: s.quantile(.25))` | IQR por grupo |
| `CASE WHEN faixa BETWEEN...` | `pd.cut(col, bins, labels)` | Intervalos numéricos |

---

## 📊 Qual gráfico usar quando?

| Gráfico | Quando usar | Função |
|---|---|---|
| **Histograma** | Distribuição de 1 variável numérica | `sns.histplot()` |
| **Boxplot** | Comparar distribuições entre grupos | `sns.boxplot()` |
| **Barras** | Valor agregado por categoria | `plt.bar()` |
| **Dispersão** | Relação entre 2 variáveis numéricas | `sns.scatterplot()` |
| **Heatmap** | Todas as correlações de uma vez | `sns.heatmap(df.corr())` |
| **Matriz confusão** | Acertos/erros de classificador | `ConfusionMatrixDisplay` |
| **Precision-Recall** | Trade-off em classes desbalanceadas | `precision_recall_curve()` |

---

## ⚠️ Regras importantes

| Regra | Motivo |
|---|---|
| Use `np.std(ddof=1)` | Amostral = Oracle STDDEV. Sem ddof=1 usa N (populacional) |
| Use **mediana** com cauda longa | Atraso, faturamento: outliers puxam a média |
| IQR **dentro do grupo** (groupby+transform) | IQR na base toda gera falsos positivos entre planos |
| Marque outlier como NaN, não delete | Preserva o aluno; sinaliza o problema |
| Correlação ≠ causa | "Pistas a investigar", não certezas |

---

## 🗺️ Trilha de estudos

```
Guia 1 — Pandas Fundamentals          ✅ Concluído
Guia 2 — Séries Temporais             ✅ Concluído
Guia 3 — FastAPI + Docker             ✅ Concluído
Guia 4 — EDA + Visualização           ✅ Este módulo
Guia 5 — Feature Engineering + ML    🔜 Próximo
```
