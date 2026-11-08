"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 4, Exercício 9                                  ║
║  Arquivo : ex09_visualizacoes_avancadas.py                                   ║
║  Tema    : Os 5 gráficos explicados + heatmap de correlação                 ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Recriar e explicar cada um dos 7 gráficos do seu saidas/ com comentários
detalhados sobre QUANDO usar cada tipo e O QUE ele revela.

OS 7 GRÁFICOS
-------------
  01 · Histograma     → distribuição de dias de atraso
  02 · Boxplot        → mensalidade por plano (outliers visíveis)
  03 · Barras         → média de atraso por plano (GROUP BY visual)
  04 · Dispersão      → aulas × atraso (relação entre 2 variáveis)
  05 · Heatmap corr   → correlação entre todas as variáveis numéricas
  06 · Matriz confusão → desempenho do modelo de churn (ML)
  07 · Precision-Recall → trade-off do modelo de churn (ML)

COMO RODAR
----------
  source .venv/Scripts/activate
  pip install numpy pandas matplotlib seaborn scikit-learn
  python ex09_visualizacoes_avancadas.py
  # Todos os gráficos salvos em saidas/
"""

from pathlib import Path
import numpy  as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay,
                              precision_recall_curve, average_precision_score)
import warnings
warnings.filterwarnings('ignore')

sns.set_theme(style='whitegrid')
PASTA = Path('saidas')
PASTA.mkdir(exist_ok=True)

def salvar(nome, titulo=''):
    if titulo: print(f"  Salvando: {nome} ({titulo})")
    plt.tight_layout()
    plt.savefig(PASTA / nome, dpi=120)
    plt.close()

print("=" * 65)
print("GATE4 — Exercício 9: Os 7 Gráficos Explicados")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────────────────
# DADOS — mesmo gerador do script original
# ─────────────────────────────────────────────────────────────────────────────
rng = np.random.default_rng(seed=42)
N   = 150
plano             = rng.choice(['Mensal','Semestral','Anual'], size=N, p=[.6,.25,.15])
base              = np.select([plano=='Mensal',plano=='Semestral'],[450.,420.],default=380.)
valor_mensalidade = np.round(base + rng.normal(0, 30, N), 2)
aulas_90d         = rng.poisson(lam=np.where(plano=='Mensal', 14, 10))
em_dia            = rng.random(N) > (0.15 + 0.30*(aulas_90d < 8))
dias_atraso       = np.where(em_dia, 0, np.round(rng.lognormal(2.3, 0.8, N)))
idade             = rng.integers(8, 65, N).astype(float)

df = pd.DataFrame({'aluno_id': np.arange(1,N+1), 'plano': plano, 'idade': idade,
                   'aulas_90d': aulas_90d, 'valor_mensalidade': valor_mensalidade,
                   'dias_atraso': dias_atraso})

df.loc[rng.choice(N, 6, replace=False), 'idade'] = np.nan
df.loc[[10,77], 'valor_mensalidade'] *= 10

# IQR por plano para detectar outliers de mensalidade
q1p = df.groupby('plano')['valor_mensalidade'].transform(lambda s: s.quantile(.25))
q3p = df.groupby('plano')['valor_mensalidade'].transform(lambda s: s.quantile(.75))
outlier = (df['valor_mensalidade'] < q1p - 1.5*(q3p-q1p)) | \
          (df['valor_mensalidade'] > q3p + 1.5*(q3p-q1p))
df['valor_limpo']  = df['valor_mensalidade'].where(~outlier)
df['idade_limpa']  = df['idade'].fillna(df['idade'].median())

# Churn para gráficos 06 e 07
df['churn'] = ((df['dias_atraso'] > 15) | (df['aulas_90d'] < 5)).astype(int)
df['prob_churn'] = (0.1 + 0.5*(df['dias_atraso']/90) +
                    0.3*((10-df['aulas_90d'])/10)).clip(0,1)
df['prob_churn'] += rng.normal(0, 0.05, N)
df['prob_churn']  = df['prob_churn'].clip(0,1)
df['pred_churn']  = (df['prob_churn'] >= 0.35).astype(int)

print(f"Dados: {N} alunos | Churns reais: {df['churn'].sum()} ({df['churn'].mean():.0%})")


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 01 — HISTOGRAMA
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 Gráfico 01 — Histograma: distribuição de dias de atraso")
print("   QUANDO USAR: quer ver COMO os valores se distribuem")
print("   REVELA: se há cauda longa, bimodalidade, onde está a concentração")
print("   SQL próximo: GROUP BY faixa para ver contagem por intervalo")

plt.figure(figsize=(8, 4))
sns.histplot(
    df['dias_atraso'],
    bins=20,
    kde=True,          # kde=True: adiciona a curva de densidade estimada
    color='navy',
    edgecolor='#30363d'
)
# Linha vertical da mediana (mais honesta que a média para dados assimétricos)
med = df['dias_atraso'].median()
med_m = df['dias_atraso'].mean()
plt.axvline(med,  color='#3fb950', linestyle='--', linewidth=2,
            label=f'Mediana ({med:.0f}d)')
plt.axvline(med_m, color='#f85149', linestyle='--', linewidth=2,
            label=f'Média ({med_m:.1f}d)')
plt.legend(fontsize=10)
plt.title('Distribuição dos dias de atraso\n(cauda longa → mediana melhor que média)')
plt.xlabel('Dias de atraso')
plt.ylabel('Quantidade de alunos')
salvar('01_hist_dias_atraso.png', 'histograma atualizado com mediana/média')


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 02 — BOXPLOT
# ─────────────────────────────────────────────────────────────────────────────
print("\n📦 Gráfico 02 — Boxplot: mensalidade por plano")
print("   QUANDO USAR: comparar distribuições entre grupos")
print("   REVELA: mediana, quartis (Q1-Q3), outliers (pontos isolados)")
print("   SQL: PERCENTILE_CONT(0.25/0.5/0.75) OVER (PARTITION BY plano)")
print("   Pontos isolados = candidatos a outlier (erros de digitação aqui!)")

plt.figure(figsize=(8, 4))
sns.boxplot(
    data=df,
    x='plano',
    y='valor_mensalidade',
    hue='plano',
    order=['Mensal', 'Semestral', 'Anual'],
    legend=False,
    palette=['#1f6feb', '#12805c', '#7b3fe4']
)
plt.title('Mensalidade por plano\n(pontos isolados acima = erros de digitação detectados)')
plt.xlabel('Plano')
plt.ylabel('Valor da mensalidade (R$)')
salvar('02_boxplot_mensalidade_plano.png', 'boxplot mensalidade')


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 03 — BARRAS
# ─────────────────────────────────────────────────────────────────────────────
print("\n📈 Gráfico 03 — Barras: média de atraso por plano")
print("   QUANDO USAR: comparar um valor agregado entre categorias")
print("   REVELA: qual grupo tem maior/menor métrica")
print("   SQL: SELECT plano, AVG(dias_atraso) FROM alunos GROUP BY plano")

media_atraso = (df.groupby('plano')['dias_atraso']
                  .mean()
                  .reindex(['Mensal', 'Semestral', 'Anual']))

plt.figure(figsize=(6, 4))
bars = plt.bar(
    media_atraso.index,
    media_atraso.values,
    color=['#1f6feb', '#12805c', '#7b3fe4'],
    edgecolor='#30363d'
)
for bar, val in zip(bars, media_atraso.values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
             f'{val:.1f}d', ha='center', fontsize=11, color='white')
plt.title('Média de dias de atraso por plano')
plt.ylabel('Dias de atraso (média)')
plt.xlabel('Plano')
salvar('03_barras_atraso_plano.png', 'barras média de atraso')


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 04 — DISPERSÃO (SCATTER)
# ─────────────────────────────────────────────────────────────────────────────
print("\n🔵 Gráfico 04 — Dispersão: aulas × dias de atraso")
print("   QUANDO USAR: relação entre DUAS variáveis numéricas")
print("   REVELA: tendência, clusters, outliers bidimensionais")
print("   SQL próximo: SELECT aulas_90d, AVG(dias_atraso) GROUP BY aulas_90d")

plt.figure(figsize=(7, 5))
sns.scatterplot(
    data=df,
    x='aulas_90d',
    y='dias_atraso',
    hue='plano',
    palette={'Mensal':'#1f6feb', 'Semestral':'#12805c', 'Anual':'#7b3fe4'},
    alpha=0.7,
    s=60
)
plt.title('Aulas nos últimos 90 dias × dias de atraso\n'
          '(pontos à esquerda = poucas aulas → tendência a maior atraso)')
plt.xlabel('Aulas nos últimos 90 dias')
plt.ylabel('Dias de atraso')
salvar('04_dispersao_aulas_atraso.png', 'scatter aulas vs atraso')


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 05 — HEATMAP DE CORRELAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
print("\n🔥 Gráfico 05 — Heatmap: correlação entre variáveis")
print("   QUANDO USAR: ver TODAS as correlações de uma vez (seleção de features)")
print("   REVELA: quais variáveis se relacionam (positiva ou negativamente)")
print("   SQL: SELECT CORR(a, b) FROM alunos (para cada par)")
print("   CUIDADO: correlação NÃO prova causa — é uma hipótese!")

colunas_num = ['idade_limpa', 'aulas_90d', 'valor_limpo', 'dias_atraso']
correlacao  = df[colunas_num].corr()

plt.figure(figsize=(7, 5))
sns.heatmap(
    correlacao,
    annot=True,         # mostra o valor numérico em cada célula
    cmap='coolwarm',    # azul = negativo, vermelho = positivo
    fmt='.2f',          # 2 casas decimais
    vmin=-1, vmax=1,    # escala fixa de -1 a 1
    linewidths=0.5,
    square=True
)
plt.title('Correlação entre variáveis numéricas\n'
          '(azul = negativa, vermelho = positiva, diagonal = 1.0)')
salvar('05_mapa_correlacao.png', 'heatmap correlação')

print(f"\n   Correlação aulas_90d × dias_atraso: "
      f"{correlacao.loc['aulas_90d','dias_atraso']:.2f}")
print(f"   → Negativa fraca: quem faz menos aulas tende a atrasar mais")
print(f"      (mas NÃO significa causalidade)")


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 06 — MATRIZ DE CONFUSÃO
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 Gráfico 06 — Matriz de confusão: desempenho do modelo de churn")
print("   QUANDO USAR: avaliar modelo de classificação (churn: sim/não)")
print("   REVELA: acertos e erros por tipo (VP, VN, FP, FN)")
print("   VN=acertou 'não churn' | VP=acertou 'churn'")
print("   FP=falso alarme        | FN=perdeu um churn real (pior erro!)")

cm = confusion_matrix(df['churn'], df['pred_churn'])
fig, ax = plt.subplots(figsize=(5, 4))
disp = ConfusionMatrixDisplay(confusion_matrix=cm,
                               display_labels=['Não Churn', 'Churn'])
disp.plot(ax=ax, colorbar=False, cmap='Blues')
ax.set_title('Matriz de Confusão — Modelo de Churn GATE4\n'
             '(FN = alunos que cancelaram sem alerta = pior erro)')

# Anotação explicando cada quadrante
fig.text(0.02, 0.01,
         'VN: corretamente identificados como ativos | '
         'VP: corretamente alertados como churn\n'
         'FP: falso alarme (ligação desnecessária) | '
         'FN: churn não detectado (perda de aluno)',
         fontsize=7, color='gray')
salvar('06_matriz_confusao.png', 'matriz de confusão')


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 07 — CURVA PRECISION-RECALL
# ─────────────────────────────────────────────────────────────────────────────
print("\n📉 Gráfico 07 — Curva Precision-Recall: trade-off do modelo")
print("   QUANDO USAR: modelo com classes desbalanceadas (poucos churns)")
print("   Precision: dos que alertei, quantos realmente cancelaram?")
print("   Recall:    dos que cancelaram, quantos eu alertei?")
print("   Trade-off: aumentar recall (capturar mais churns) →")
print("              reduz precision (mais falsos alarmes)")

prec, rec, thresholds = precision_recall_curve(df['churn'], df['prob_churn'])
ap = average_precision_score(df['churn'], df['prob_churn'])

plt.figure(figsize=(7, 5))
plt.plot(rec, prec, color='#1f6feb', linewidth=2.5, label=f'AP = {ap:.2f}')
plt.fill_between(rec, prec, alpha=0.1, color='#1f6feb')

# Marca o limiar atual (0.35)
idx_lim = np.argmin(np.abs(thresholds - 0.35))
plt.scatter(rec[idx_lim], prec[idx_lim], color='#f85149', s=120, zorder=5,
            label=f'Limiar 0.35 → Prec={prec[idx_lim]:.2f} Rec={rec[idx_lim]:.2f}')

plt.xlabel('Recall (% dos churns reais detectados)')
plt.ylabel('Precision (% dos alertas que são churns reais)')
plt.title(f'Curva Precision-Recall — Churn GATE4\n'
          f'AP={ap:.2f} | Mova o limiar conforme o custo do erro')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
salvar('07_curva_precision_recall.png', 'curva precision-recall')

print(f"\n   AP (Average Precision): {ap:.2f}")
print(f"   Com limiar 0.35: Precision={prec[idx_lim]:.0%} | Recall={rec[idx_lim]:.0%}")


# ─────────────────────────────────────────────────────────────────────────────
# GUIA DE ESCOLHA — qual gráfico usar quando
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("📋 GUIA: Qual gráfico usar quando?")
print("=" * 65)
guia = [
    ("Histograma",       "Distribuição de 1 variável numérica",         "sns.histplot()"),
    ("Boxplot",          "Comparar distribuições entre grupos",          "sns.boxplot()"),
    ("Barras",           "Comparar valor agregado entre categorias",     "plt.bar() / sns.barplot()"),
    ("Dispersão",        "Relação entre 2 variáveis numéricas",          "sns.scatterplot()"),
    ("Heatmap corr",     "Todas as correlações de uma vez",              "sns.heatmap(df.corr())"),
    ("Matriz confusão",  "Acertos/erros de modelo classificador",        "ConfusionMatrixDisplay"),
    ("Precision-Recall", "Trade-off limiar em classes desbalanceadas",   "precision_recall_curve()"),
]
for tipo, quando, como in guia:
    print(f"\n  {tipo:<20} → {quando}")
    print(f"  {'':20}   Código: {como}")

print("\n" + "=" * 65)
print("✅ Exercício 9 concluído — 7 gráficos recriados e explicados!")
print(f"   Verifique a pasta: {PASTA.resolve()}")
print("=" * 65 + "\n")
