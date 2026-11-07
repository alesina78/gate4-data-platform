"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 2, Exercício 3  (projeto)                       ║
║  Arquivo : ex03_previsao_faturamento_gate4.py                                ║
║  Tema    : Pipeline completo — Baseline × Random Forest com TimeSeriesSplit ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Implementar o pipeline completo de previsão de faturamento do GATE4:
  1. Montar a série temporal corretamente (resample + asfreq)
  2. Calcular o Baseline Sazonal (mês igual do ano passado)
  3. Criar features de ML sem Data Leakage
  4. Treinar Random Forest com TimeSeriesSplit
  5. Comparar o modelo com o baseline e decidir qual apresentar

ENTREGÁVEL DO EXERCÍCIO
-----------------------
Responda no terminal:
  → Qual o MAE do Baseline?
  → Qual o MAE médio do Random Forest?
  → Qual você apresentaria à dona do haras e POR QUÊ?

CONCEITOS USADOS
----------------
  resample('MS').sum()      → faturamento mensal  (= GROUP BY TRUNC(data,'MM'))
  asfreq(fill_value=0)      → preenche meses sem venda (= LEFT JOIN com calendário)
  .shift(1)                 → LAG de 1 mês
  .shift(12)                → LAG de 12 meses (mesmo mês ano passado = baseline sazonal)
  .rolling(n).mean()        → média móvel (= AVG OVER ROWS BETWEEN)
  .pct_change()             → variação percentual (= (v - LAG) / LAG)
  TimeSeriesSplit           → validação cruzada que respeita a ordem do tempo
  RandomForestRegressor     → modelo de árvores de decisão combinadas
  mean_absolute_error       → MAE: erro médio em R$ (fácil de explicar ao cliente)

COMO RODAR
----------
  source .venv/Scripts/activate
  python ex03_previsao_faturamento_gate4.py

SUBSTITUA OS DADOS SIMULADOS
-----------------------------
  df = pd.read_csv('faturamento_gate4.csv', parse_dates=['data'])
  # A query Oracle para gerar o CSV:
  #   SELECT TRUNC(data_pagamento, 'MM') data, SUM(valor) valor
  #   FROM   pagamentos
  #   WHERE  status = 'PAGO'
  #   GROUP  BY TRUNC(data_pagamento, 'MM')
  #   ORDER  BY 1
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
import pandas  as pd
import numpy   as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble        import RandomForestRegressor
from sklearn.metrics         import mean_absolute_error
import warnings
warnings.filterwarnings('ignore')   # suprime avisos de versão do sklearn


# ─────────────────────────────────────────────────────────────────────────────
# SEÇÃO 1 — DADOS SIMULADOS (substitua por dados reais do GATE4)
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("GATE4 — Exercício 3: Pipeline Completo de Previsão")
print("=" * 65)
print("\n📂 SEÇÃO 1 — Carregando dados...")

rng = np.random.default_rng(seed=42)   # semente fixa → reprodutibilidade

# 36 meses de dados (3 anos: 2023–2025) — mínimo recomendado para série com
# sazonalidade anual (precisa de pelo menos 2 ciclos completos)
meses = pd.date_range('2023-01-01', periods=36, freq='MS')

# Sazonalidade anual do haras (jul e dez = temporada alta)
# Cada valor é um multiplicador da receita base
sazon = np.array([
    .88, .82, .90, .95, 1.05, 1.15,   # jan–jun
    1.50, 1.35, 1.00, 1.08, 1.20, 1.42  # jul–dez
] * 3)   # repete 3 anos

# Receita base + ruído aleatório + sazonalidade
fat_simulado = rng.normal(28_000, 1_800, 36) * sazon

# Simula DataFrame como viria de um CSV ou query Oracle
# (data de pagamento + valor pago)
pagamentos = pd.DataFrame({
    'data' : meses,
    'valor': fat_simulado
})

print(f"   Período: {pagamentos['data'].min().strftime('%b/%Y')} "
      f"→ {pagamentos['data'].max().strftime('%b/%Y')}  ({len(pagamentos)} meses)")
print(f"   Receita total simulada: R$ {pagamentos['valor'].sum():,.0f}")


# ─────────────────────────────────────────────────────────────────────────────
# SEÇÃO 2 — SÉRIE TEMPORAL COM CALENDÁRIO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────
print("\n📅 SEÇÃO 2 — Montando série temporal com calendário completo...")

# Converte a coluna 'data' para tipo datetime (caso venha como string do CSV)
pagamentos['data'] = pd.to_datetime(pagamentos['data'])

fat = (
    pagamentos
    .set_index('data')       # a data vira o índice — necessário para resample
    ['valor']                # seleciona só a coluna de valor
    .resample('MS')          # agrupa por mês  (= GROUP BY TRUNC(data,'MM'))
    .sum()                   # soma os pagamentos do mês
    .asfreq('MS',            # garante que TODOS os meses aparecem
            fill_value=0)    # mês sem venda → 0  (= NVL no Oracle)
)

# fat agora é uma Series com DatetimeIndex e um valor por mês
print(f"   Série com {len(fat)} meses, sem lacunas no calendário")
print(f"   Meses com zero faturamento: {(fat == 0).sum()}")


# ─────────────────────────────────────────────────────────────────────────────
# SEÇÃO 3 — FEATURES (SEM DATA LEAKAGE)
# ─────────────────────────────────────────────────────────────────────────────
print("\n🔧 SEÇÃO 3 — Criando features para o modelo...")

t = fat.to_frame('fat')    # transforma Series em DataFrame para adicionar colunas

# ── Features de LAG (passado) ─────────────────────────────────────────────
# shift(n) = LAG(fat, n) OVER (ORDER BY mes) no Oracle
# O shift POSITIVO desloca para "atrás": a linha atual recebe o valor de n períodos antes
t['lag_1']  = t.fat.shift(1)    # faturamento do mês anterior
t['lag_3']  = t.fat.shift(3)    # faturamento de 3 meses atrás
t['lag_12'] = t.fat.shift(12)   # faturamento do mesmo mês do ANO PASSADO
                                 # → este lag_12 também será nosso BASELINE

# ── Feature de média móvel (janela de 3 meses) ───────────────────────────
# shift(1) ANTES do rolling → usa apenas meses passados (sem leakage)
# rolling(3) → AVG OVER (ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING)
t['media_3m'] = t.fat.shift(1).rolling(window=3, min_periods=1).mean()

# ── Feature de variação percentual ───────────────────────────────────────
# pct_change() = (fat - LAG(fat,1)) / LAG(fat,1)   (= variação mês a mês)
# shift(1) no pct_change evita incluir o mês atual na variação
t['var_pct'] = t.fat.shift(1).pct_change()

# ── Features de calendário (extraídas do índice datetime) ────────────────
# Equivalem a: TO_NUMBER(TO_CHAR(data,'MM')) e TO_CHAR(data,'Q') no Oracle
t['mes']      = t.index.month    # número do mês: 1–12
t['trimestre'] = t.index.quarter # trimestre: 1–4

# ── Remoção de NaN ────────────────────────────────────────────────────────
# Os primeiros meses ficam sem valor nos lags — dropna() elimina essas linhas
# (como no Oracle, onde LAG retorna NULL nas primeiras linhas sem IGNORE NULLS)
n_antes = len(t)
t = t.dropna()
print(f"   Features criadas: {list(t.columns)}")
print(f"   Linhas removidas por NaN: {n_antes - len(t)} (esperado: 12, por causa do lag_12)")
print(f"   Registros para modelagem: {len(t)} meses")


# ─────────────────────────────────────────────────────────────────────────────
# SEÇÃO 4 — BASELINE SAZONAL (mês igual do ano passado)
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 SEÇÃO 4 — Calculando Baseline Sazonal...")
print()
print("   O BASELINE é a previsão mais simples possível:")
print("   'O faturamento deste mês será igual ao do mesmo mês do ano passado'")
print("   Em Oracle: SELECT fat FROM fat_mensal WHERE mes = TRUNC(SYSDATE,'MM') - INTERVAL '1' YEAR")
print()

# A feature lag_12 já é o valor do mesmo mês do ano passado — isso É o baseline
baseline_pred = t['lag_12']   # previsão = faturamento de 12 meses atrás
baseline_real = t['fat']      # valor real que queremos comparar

mae_baseline = mean_absolute_error(baseline_real, baseline_pred)
mape_baseline = np.mean(np.abs((baseline_real - baseline_pred) / baseline_real.replace(0, np.nan))) * 100

print(f"   Baseline Sazonal (lag-12):")
print(f"     MAE  = R$ {mae_baseline:,.0f}  (erro médio por mês em R$)")
print(f"     MAPE = {mape_baseline:.1f}%  (erro médio em %)")
print()
print("   💡 O que é MAE?")
print("      MAE (Mean Absolute Error) = média dos erros absolutos")
print("      Em R$: se MAE = 2.500, o modelo erra R$ 2.500 por mês em média")
print("      MAPE: o mesmo em percentual — mais fácil de explicar ao cliente")


# ─────────────────────────────────────────────────────────────────────────────
# SEÇÃO 5 — MODELO: Random Forest com TimeSeriesSplit
# ─────────────────────────────────────────────────────────────────────────────
print("\n🌲 SEÇÃO 5 — Treinando Random Forest com TimeSeriesSplit...")
print()
print("   TimeSeriesSplit divide o tempo em N 'folds' expansivos:")
print("   Fold 1: Treino [meses 1-5]  → Teste [meses 6-8]")
print("   Fold 2: Treino [meses 1-8]  → Teste [meses 9-11]")
print("   ... e assim por diante — o treino SEMPRE cresce para o futuro")
print()

# Separa features (X) do alvo (y)
# var_pct não entra: pode ter divisão por zero e é redundante com lag_1
X = t.drop(columns=['fat', 'var_pct'])
y = t['fat']

# TimeSeriesSplit — 4 divisões temporais
# Escolha de n_splits: com 24 meses e lag_12, sobram ~12 meses para modelar
# 4 splits gera ~3 meses de teste por fold — suficiente para avaliar sazonalidade
tss  = TimeSeriesSplit(n_splits=4)
maes = []   # vai guardar o MAE de cada fold

for fold, (idx_treino, idx_teste) in enumerate(tss.split(X), start=1):
    # Fatia os dados de treino e teste pelo ÍNDICE (posição, não data)
    X_tr, X_te = X.iloc[idx_treino], X.iloc[idx_teste]
    y_tr, y_te = y.iloc[idx_treino], y.iloc[idx_teste]

    # Treina o modelo — Random Forest cria várias árvores de decisão e combina
    # n_estimators=100 → 100 árvores (padrão razoável para começar)
    # random_state=42  → garante reprodutibilidade (= seed no Oracle DBMS_RANDOM)
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X_tr, y_tr)       # treina com o passado

    # Faz previsões no período de teste (futuro relativo ao treino)
    previsoes = modelo.predict(X_te)

    # Calcula o MAE deste fold
    mae_fold = mean_absolute_error(y_te, previsoes)
    maes.append(mae_fold)

    # Exibe as datas do fold para confirmar que não há leakage
    data_inicio_treino = X_tr.index.min().strftime('%b/%Y')
    data_fim_treino    = X_tr.index.max().strftime('%b/%Y')
    data_inicio_teste  = X_te.index.min().strftime('%b/%Y')
    data_fim_teste     = X_te.index.max().strftime('%b/%Y')

    print(f"   Fold {fold}:")
    print(f"     Treino: {data_inicio_treino} → {data_fim_treino}  ({len(X_tr)} meses)")
    print(f"     Teste : {data_inicio_teste}  → {data_fim_teste}   ({len(X_te)} meses)")
    print(f"     MAE   : R$ {mae_fold:,.0f}")
    print()

mae_rf_medio = np.mean(maes)
mae_rf_std   = np.std(maes)


# ─────────────────────────────────────────────────────────────────────────────
# SEÇÃO 6 — IMPORTÂNCIA DAS FEATURES (o que o modelo mais usou)
# ─────────────────────────────────────────────────────────────────────────────
print("─" * 65)
print("🔍 SEÇÃO 6 — Importância das Features (último fold)")
print("─" * 65)

# O Random Forest calcula automaticamente quais features foram mais úteis
# feature_importances_ retorna um valor entre 0 e 1 para cada feature
importancias = pd.Series(
    modelo.feature_importances_,   # importância de cada feature
    index=X.columns                # nome das features
).sort_values(ascending=False)

print()
for feat, imp in importancias.items():
    barra = "█" * int(imp * 40)   # barra visual proporcional
    print(f"   {feat:<15} {barra:<40} {imp:.1%}")

print()
print("   💡 Features com alta importância são as que mais explicam o faturamento.")
print("      Se lag_12 domina: a sazonalidade anual é o fator principal.")
print("      Se mes/trimestre domina: há forte padrão calendário.")


# ─────────────────────────────────────────────────────────────────────────────
# SEÇÃO 7 — COMPARAÇÃO FINAL: BASELINE × MODELO
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("🏆 SEÇÃO 7 — Resultado Final: Baseline × Random Forest")
print("=" * 65)
print()
print(f"   📊 Baseline Sazonal (lag-12) :")
print(f"      MAE  = R$ {mae_baseline:,.0f}  |  MAPE = {mape_baseline:.1f}%")
print()
print(f"   🌲 Random Forest (TimeSeriesSplit):")
print(f"      MAE médio = R$ {mae_rf_medio:,.0f}  ±  R$ {mae_rf_std:,.0f}")
print()

# Decisão automática baseada nos resultados
if mae_rf_medio < mae_baseline:
    melhora = ((mae_baseline - mae_rf_medio) / mae_baseline) * 100
    print(f"   ✅ O MODELO vence o Baseline por {melhora:.1f}% — vale usar em produção.")
    print()
    print("   Por que apresentar o Random Forest à dona do haras?")
    print("   → Ele aprende padrões além da simples repetição do ano passado")
    print("   → Incorpora tendência de crescimento (lag_1, lag_3)")
    print("   → Captura sazonalidade combinada (mes, trimestre + lag_12)")
else:
    diferenca = ((mae_rf_medio - mae_baseline) / mae_baseline) * 100
    print(f"   ⚠️  O BASELINE ainda vence o modelo por {diferenca:.1f}%.")
    print()
    print("   O que fazer quando o baseline vence?")
    print("   → Adicionar mais dados (mínimo 2–3 anos para séries mensais)")
    print("   → Adicionar features externas (feriados, eventos do haras)")
    print("   → Tentar statsmodels ETS ou SARIMAX (séries pequenas)")
    print("   → Nunca forçar um modelo complexo — o simples às vezes é o melhor")

print()
print("   📌 Regra de ouro para entrevista:")
print("      'Sempre compare com o baseline. Se o modelo não bate o simples,")
print("       o modelo não está pronto.' — essa frase impressiona recrutadores.")

print("\n" + "=" * 65)
print("✅ Exercício 3 concluído — Pipeline GATE4 completo!")
print()
print("   PRÓXIMOS PASSOS:")
print("   1. Substitua os dados simulados por um CSV real do GATE4")
print("   2. Salve o gráfico real × previsto para o README:")
print("      import matplotlib.pyplot as plt")
print("      (veja o Guia 3 — Visualização com Matplotlib/Seaborn)")
print("   3. Commite no GitHub e referencie no LinkedIn")
print("=" * 65 + "\n")
