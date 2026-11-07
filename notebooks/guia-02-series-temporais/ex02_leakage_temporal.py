"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 2, Exercício 2                                  ║
║  Arquivo : ex02_leakage_temporal.py                                          ║
║  Tema    : Identificar e corrigir Data Leakage em Séries Temporais          ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Demonstrar os 3 tipos clássicos de Data Leakage Temporal — mostrar o código
ERRADO, explicar por que está errado e apresentar a correção.

O QUE É DATA LEAKAGE?
---------------------
Leakage ("vazamento") acontece quando o modelo recebe informação do FUTURO
durante o treino. O resultado:
  → Métricas excelentes no notebook (MAE baixo, R² alto)
  → Previsões péssimas em produção (o modelo nunca viu dados assim)
  → Embaraço em entrevista quando perguntam "como você validou?"

ANALOGIA COM ORACLE
-------------------
Imagine que você tem uma procedure que calcula o faturamento de JANEIRO
usando dados de DEZEMBRO do mesmo ano — que ainda não existem quando
você roda em janeiro. O resultado estaria "certo" no teste com dados
históricos, mas quebraria em produção.

OS 3 BUGS DESTE EXERCÍCIO
--------------------------
  Bug 1 — rolling() sem shift(1)      → média inclui o mês que quer prever
  Bug 2 — train_test_split aleatório  → futuro cai no treino
  Bug 3 — MinMaxScaler global         → scaler usa min/max do futuro

CONCEITOS PANDAS/SKLEARN USADOS
--------------------------------
  .shift(n)             → desloca a série n períodos para o passado (= LAG no Oracle)
  .rolling(n).mean()    → média móvel de n períodos
  train_test_split()    → split aleatório (ERRADO para séries)
  MinMaxScaler          → normaliza entre 0 e 1
  .fit() / .transform() → fit = aprende os parâmetros; transform = aplica
  TimeSeriesSplit       → validação cruzada respeitando a ordem do tempo

COMO RODAR
----------
  source .venv/Scripts/activate
  python ex02_leakage_temporal.py
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
import pandas  as pd
import numpy   as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing   import MinMaxScaler
from sklearn.metrics         import mean_absolute_error

# ─────────────────────────────────────────────────────────────────────────────
# DADOS — faturamento mensal simulado do GATE4 (24 meses)
# ─────────────────────────────────────────────────────────────────────────────
rng   = np.random.default_rng(seed=42)
meses = pd.date_range('2024-01-01', periods=24, freq='MS')

# Sazonalidade: julho e dezembro têm pico (cavalos em férias / temporada de shows)
sazon = np.array([.9, .8, .9, 1.0, 1.1, 1.2, 1.5, 1.3, 1.0, 1.1, 1.2, 1.4] * 2)
fat   = rng.normal(28_000, 1_500, 24) * sazon   # faturamento em R$

t = pd.DataFrame({'fat': fat}, index=meses)   # DataFrame com índice DatetimeIndex

print("=" * 65)
print("GATE4 — Exercício 2: Data Leakage Temporal — Encontre os Bugs")
print("=" * 65)
print(f"\nDataFrame base: {len(t)} meses de faturamento")
print(t.head())


# ═════════════════════════════════════════════════════════════════════════════
# BUG 1 — rolling() SEM shift(1)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 65)
print("BUG 1 — rolling() sem shift(1)  [LEAKAGE DE FEATURE]")
print("═" * 65)

# ❌ CÓDIGO ERRADO ───────────────────────────────────────────────────────────
print("\n❌ ERRADO:")
print("   t['media_3m'] = t.fat.rolling(3).mean()")
print()
print("   Por quê está errado?")
print("   A rolling(3) usa: [mês -2], [mês -1] e [mês ATUAL]")
print("   Mas o mês atual É o que queremos prever!")
print("   O modelo vê a 'resposta certa' durante o treino — cola na prova.")
print()

# Demonstração numérica do problema
t_bug1 = t.copy()
t_bug1['media_3m_ERRADA'] = t_bug1.fat.rolling(3).mean()

# A coluna errada inclui o próprio valor de 'fat' na média
# Veja: em março/2024, a média inclui jan + fev + MAR (que é o valor previsto!)
print("   Comparação — linha de março/2024:")
print(f"   fat (valor real)         : R$ {t_bug1.iloc[2]['fat']:,.0f}")
print(f"   media_3m ERRADA (jan+fev+MAR): R$ {t_bug1.iloc[2]['media_3m_ERRADA']:,.0f}")
print(f"   → A feature já 'sabe' o valor que está tentando prever!\n")

# ✅ CÓDIGO CORRETO ──────────────────────────────────────────────────────────
print("✅ CORRETO:")
print("   t['media_3m'] = t.fat.shift(1).rolling(3).mean()")
print()
print("   Como funciona o shift(1)?")
print("   shift(1) desloca a série 1 período para frente:")
print("     → a linha de MARÇO recebe o valor de FEVEREIRO")
print("     → a linha de FEVEREIRO recebe o valor de JANEIRO")
print("   Então rolling(3) calcula: [mês -3], [mês -2], [mês -1]  ✓")
print()
print("   Analogia Oracle:")
print("   AVG(fat) OVER (ORDER BY mes ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING)")
print()

t['media_3m_CORRETA'] = t.fat.shift(1).rolling(3).mean()

print("   Comparação — linha de março/2024:")
print(f"   fat (valor real)          : R$ {t.iloc[2]['fat']:,.0f}")
print(f"   media_3m CORRETA (jan+fev): R$ {t.iloc[2]['media_3m_CORRETA']:,.2f}")
print(f"   → A feature usa apenas dados ANTERIORES a março  ✓")


# ═════════════════════════════════════════════════════════════════════════════
# BUG 2 — train_test_split ALEATÓRIO
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 65)
print("BUG 2 — train_test_split aleatório  [LEAKAGE DE SPLIT]")
print("═" * 65)

# Monta features completas para o exemplo
t['lag_1']   = t.fat.shift(1)
t['lag_12']  = t.fat.shift(12)
t = t.dropna()

X = t.drop(columns='fat')
y = t['fat']

# ❌ CÓDIGO ERRADO ───────────────────────────────────────────────────────────
print("\n❌ ERRADO:")
print("   X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2)")
print()

X_tr_bug, X_te_bug, y_tr_bug, y_te_bug = train_test_split(
    X, y, test_size=0.2, random_state=42
)
# Mostra as datas que caíram no teste — algumas são anteriores a datas do treino!
datas_teste_bug = sorted(X_te_bug.index.tolist())
datas_treino_bug = sorted(X_tr_bug.index.tolist())

print(f"   Datas no TREINO (5 exemplos): {[d.strftime('%Y-%m') for d in datas_treino_bug[:5]]}")
print(f"   Datas no TESTE  (5 exemplos): {[d.strftime('%Y-%m') for d in datas_teste_bug[:5]]}")
print()
print("   Por quê está errado?")
print("   Veja se alguma data do TREINO é POSTERIOR a alguma data do TESTE:")
max_teste  = max(datas_teste_bug)
min_treino_apos = [d for d in datas_treino_bug if d > max_teste]
print(f"   Data mais recente no TESTE : {max_teste.strftime('%Y-%m')}")
print(f"   Datas do TREINO > que o TESTE: {len(min_treino_apos)} meses")
print(f"   → O modelo treinou com dados mais recentes do que o 'teste'!")
print(f"     É como estudar com a prova já respondida.\n")

# ✅ CÓDIGO CORRETO ──────────────────────────────────────────────────────────
print("✅ CORRETO — corte por data:")
print("   corte    = '2025-07-01'")
print("   X_tr, y_tr = X.loc[:corte], y.loc[:corte]   # passado")
print("   X_te, y_te = X.loc[corte:], y.loc[corte:]   # futuro")
print()

corte = '2025-07-01'
X_tr = X.loc[:corte];  y_tr = y.loc[:corte]
X_te = X.loc[corte:];  y_te = y.loc[corte:]

print(f"   Treino: {X_tr.index.min().strftime('%Y-%m')} → {X_tr.index.max().strftime('%Y-%m')}  ({len(X_tr)} meses)")
print(f"   Teste : {X_te.index.min().strftime('%Y-%m')} → {X_te.index.max().strftime('%Y-%m')}  ({len(X_te)} meses)")
print(f"   → Todo o passado treina. O futuro testa. Sem cruzamento.  ✓")


# ═════════════════════════════════════════════════════════════════════════════
# BUG 3 — MinMaxScaler GLOBAL
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 65)
print("BUG 3 — MinMaxScaler global  [LEAKAGE DE NORMALIZAÇÃO]")
print("═" * 65)

# ❌ CÓDIGO ERRADO ───────────────────────────────────────────────────────────
print("\n❌ ERRADO:")
print("   scaler = MinMaxScaler().fit(X)   # usa TODA a série, incluindo o futuro")
print()
print("   Por quê está errado?")

scaler_bug = MinMaxScaler()
scaler_bug.fit(X)   # o .fit() olha para min e max de TODA a série
print(f"   O scaler aprendeu: min={scaler_bug.data_min_[0]:,.0f}, max={scaler_bug.data_max_[0]:,.0f}")
print(f"   Esses valores incluem meses do FUTURO que o modelo não deveria ver.")
print(f"   Em produção, você nunca sabe qual será o valor máximo futuro.")
print()

# ✅ CÓDIGO CORRETO ──────────────────────────────────────────────────────────
print("✅ CORRETO:")
print("   scaler = MinMaxScaler()")
print("   scaler.fit(X_tr)              # aprende apenas com o TREINO")
print("   X_tr_s = scaler.transform(X_tr)   # aplica ao treino")
print("   X_te_s = scaler.transform(X_te)   # aplica ao teste com os parâmetros do treino")
print()

scaler_ok = MinMaxScaler()
scaler_ok.fit(X_tr)   # .fit() APENAS com dados de treino
X_tr_s = scaler_ok.transform(X_tr)
X_te_s = scaler_ok.transform(X_te)

print(f"   Scaler correto: min={scaler_ok.data_min_[0]:,.0f}, max={scaler_ok.data_max_[0]:,.0f}")
print(f"   → Aprendido apenas com os {len(X_tr)} meses de treino.  ✓")


# ═════════════════════════════════════════════════════════════════════════════
# RESUMO FINAL
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 65)
print("RESUMO — Checklist Anti-Leakage")
print("═" * 65)
checklist = [
    ("✅", "rolling() sempre precedido de .shift(1) em features de ML"),
    ("✅", "Split por data (corte fixo) ou TimeSeriesSplit — nunca aleatório"),
    ("✅", "MinMaxScaler / StandardScaler: .fit() SOMENTE no treino"),
    ("✅", "Nenhuma feature usa dado que só existiria 'depois' (ex: total do mês)"),
    ("✅", "Se MAE no treino é muito melhor que no teste → suspeite de leakage"),
]
for emoji, item in checklist:
    print(f"  {emoji}  {item}")

print("\n✅ Exercício 2 concluído.")
print("   Próximo: ex03_previsao_faturamento_gate4.py\n")
