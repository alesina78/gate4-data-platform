"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 4, Exercício 8                                  ║
║  Arquivo : ex08_eda_completo_gate4.py                                        ║
║  Tema    : EDA completa — nulos, outliers, IQR por grupo, groupby           ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Implementar a EDA (Análise Exploratória de Dados) completa do script
03_numpy_eda_visualizacao.py — com todos os 4 exercícios propostos
e comentários SQL→Pandas em cada passo.

EXERCÍCIOS IMPLEMENTADOS
------------------------
  Ex 1: Alunos com mais de 30 dias de atraso + percentual
  Ex 2: Coluna faixa_atraso com np.select (Em dia / Até 15 / Mais de 15)
  Ex 3: Boxplot de atraso por plano + qual tem maior mediana
  Ex 4: Faixas de idade com pd.cut + média de atraso por faixa

COMO RODAR
----------
  source .venv/Scripts/activate
  pip install numpy pandas matplotlib seaborn
  python ex08_eda_completo_gate4.py
  # Gráficos salvos em saidas/ex8_*.png
"""

from pathlib import Path
import numpy  as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.options.display.float_format = '{:.2f}'.format
sns.set_theme(style='whitegrid')

PASTA_SAIDA = Path('saidas')
PASTA_SAIDA.mkdir(exist_ok=True)

def salvar(nome):
    """Salva o gráfico atual em saidas/ com dpi=120."""
    caminho = PASTA_SAIDA / nome
    plt.tight_layout()
    plt.savefig(caminho, dpi=120)
    print(f"  → Gráfico salvo: {caminho}")
    plt.close()

print("=" * 65)
print("GATE4 — Exercício 8: EDA Completa com Exercícios")
print("=" * 65)


# ─────────────────────────────────────────────────────────────────────────────
# DADOS — igual ao 03_numpy_eda_visualizacao.py
# ─────────────────────────────────────────────────────────────────────────────
print("\n📂 Gerando dados simulados (igual ao script original)...")

rng = np.random.default_rng(seed=42)
N   = 150

plano = rng.choice(['Mensal', 'Semestral', 'Anual'], size=N, p=[0.60, 0.25, 0.15])
base  = np.select(
    [plano == 'Mensal', plano == 'Semestral'],
    [450.0, 420.0],
    default=380.0
)
valor_mensalidade = np.round(base + rng.normal(0, 30, size=N), 2)
aulas_90d         = rng.poisson(lam=np.where(plano == 'Mensal', 14, 10))
prob_atraso       = 0.15 + 0.30 * (aulas_90d < 8)
em_dia            = rng.random(N) > prob_atraso
dias_atraso       = np.where(em_dia, 0,
                        np.round(rng.lognormal(mean=2.3, sigma=0.8, size=N)))
idade             = rng.integers(8, 65, size=N).astype(float)

df = pd.DataFrame({
    'aluno_id':          np.arange(1, N + 1),
    'plano':             plano,
    'idade':             idade,
    'aulas_90d':         aulas_90d,
    'valor_mensalidade': valor_mensalidade,
    'dias_atraso':       dias_atraso,
})

# Injeta sujeira proposital (como no script original)
df.loc[rng.choice(N, size=6, replace=False), 'idade'] = np.nan   # 6 idades NULL
df.loc[[10, 77], 'valor_mensalidade'] *= 10                      # 2 erros de digitação

print(f"   Alunos: {N} | Colunas: {list(df.columns)}")


# ─────────────────────────────────────────────────────────────────────────────
# EDA BÁSICA — as 6 perguntas obrigatórias
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 EDA BÁSICA")
print("─" * 65)

# 1. Tamanho — SQL: SELECT COUNT(*) FROM alunos
print(f"\n1. Tamanho da tabela (df.shape): {df.shape}")
print(f"   {df.shape[0]} alunos × {df.shape[1]} colunas")

# 2. Tipos — SQL: DESCRIBE alunos
print("\n2. Tipos das colunas (df.dtypes):")
print(df.dtypes.to_string())

# 3. Resumo estatístico — SQL: SELECT COUNT, AVG, STDDEV, MIN, MAX FROM alunos
print("\n3. Resumo estatístico (df.describe()):")
print(df.describe().round(2).to_string())

# 4. Valores nulos — SQL: COUNT(*) - COUNT(col)
print("\n4. Valores nulos (df.isna().sum()):")
nulos = pd.DataFrame({
    'quantidade': df.isna().sum(),
    'percentual': (df.isna().mean() * 100).round(1)
})
print(nulos[nulos['quantidade'] > 0].to_string())

# 5. Distribuição por plano — SQL: GROUP BY plano
print("\n5. Distribuição por plano (value_counts):")
print(df['plano'].value_counts().to_string())

# 6. Estatística por grupo — SQL: GROUP BY plano com AVG, MEDIAN, MAX
print("\n6. Dias de atraso por plano (groupby + agg):")
resumo_grupo = df.groupby('plano')['dias_atraso'].agg(
    media='mean',
    mediana='median',
    maximo='max',
    pct_atrasam=lambda s: (s > 0).mean() * 100
).round(1)
print(resumo_grupo.to_string())


# ─────────────────────────────────────────────────────────────────────────────
# OUTLIERS — IQR dentro do próprio plano
# ─────────────────────────────────────────────────────────────────────────────
print("\n🔍 DETECÇÃO DE OUTLIERS — IQR por grupo")
print("─" * 65)
print("Analogia Oracle: PERCENTILE_CONT OVER (PARTITION BY plano)")

# IQR dentro de cada plano (groupby + transform = OVER PARTITION BY)
q1_plano = df.groupby('plano')['valor_mensalidade'].transform(
    lambda s: s.quantile(0.25)   # Q1 de cada plano
)
q3_plano = df.groupby('plano')['valor_mensalidade'].transform(
    lambda s: s.quantile(0.75)   # Q3 de cada plano
)
iqr_plano = q3_plano - q1_plano

fora_do_plano = (
    (df['valor_mensalidade'] < q1_plano - 1.5 * iqr_plano) |
    (df['valor_mensalidade'] > q3_plano + 1.5 * iqr_plano)
)

print(f"\nOutliers detectados (dentro do plano): {fora_do_plano.sum()}")
print(df.loc[fora_do_plano, ['aluno_id', 'plano', 'valor_mensalidade']].to_string())

# Tratar: marcar como nulo (não deletar)
df['valor_limpo'] = df['valor_mensalidade'].where(~fora_do_plano)
# NVL(idade, mediana) — preencher nulos com mediana
df['idade_limpa'] = df['idade'].fillna(df['idade'].median())

print(f"\nTratamento:")
print(f"  valor_limpo : outliers → NaN (mantém o aluno, invalida só o valor)")
print(f"  idade_limpa : NaN → mediana ({df['idade'].median():.0f} anos)")


# ─────────────────────────────────────────────────────────────────────────────
# EXERCÍCIO 1 — Alunos com mais de 30 dias de atraso
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("✏️  EXERCÍCIO 1 — Alunos com mais de 30 dias de atraso")
print("=" * 65)
print("SQL: SELECT COUNT(*) FROM alunos WHERE dias_atraso > 30")

# Filtro booleano — equivale ao WHERE do SQL
atrasados_30 = df[df['dias_atraso'] > 30]
qtd = len(atrasados_30)
pct = qtd / len(df) * 100

print(f"\nAlunos com atraso > 30 dias : {qtd} ({pct:.1f}% do total)")
print("\nTop 5 maiores atrasos:")
print(atrasados_30[['aluno_id', 'plano', 'dias_atraso', 'valor_mensalidade']]
      .sort_values('dias_atraso', ascending=False)
      .head(5)
      .to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# EXERCÍCIO 2 — Coluna faixa_atraso com np.select
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("✏️  EXERCÍCIO 2 — faixa_atraso com np.select")
print("=" * 65)
print("""SQL:
  CASE WHEN dias_atraso = 0   THEN 'Em dia'
       WHEN dias_atraso <= 15 THEN 'Até 15 dias'
       ELSE                        'Mais de 15 dias'
  END AS faixa_atraso""")

# A ORDEM IMPORTA: primeira condição verdadeira vence (igual ao CASE WHEN Oracle)
condicoes = [
    df['dias_atraso'] == 0,     # WHEN dias_atraso = 0
    df['dias_atraso'] <= 15,    # WHEN dias_atraso <= 15
]
rotulos = [
    'Em dia',                   # THEN 'Em dia'
    'Até 15 dias',              # THEN 'Até 15 dias'
]
df['faixa_atraso'] = np.select(condicoes, rotulos, default='Mais de 15 dias')

print("\nDistribuição das faixas de atraso:")
dist = df['faixa_atraso'].value_counts()
for faixa, qtd in dist.items():
    pct = qtd / len(df) * 100
    barra = '█' * int(pct / 2)
    print(f"  {faixa:<20} {qtd:>4} alunos  ({pct:>5.1f}%)  {barra}")


# ─────────────────────────────────────────────────────────────────────────────
# EXERCÍCIO 3 — Boxplot de atraso por plano
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("✏️  EXERCÍCIO 3 — Boxplot de atraso por plano")
print("=" * 65)

# Qual plano tem maior mediana?
medianas = df.groupby('plano')['dias_atraso'].median().sort_values(ascending=False)
print("\nMediana de atraso por plano:")
for plano, med in medianas.items():
    print(f"  {plano:<12} : {med:.0f} dias")
print(f"\nPlano com maior mediana: {medianas.idxmax()}")

# Gráfico
plt.figure(figsize=(8, 5))
sns.boxplot(
    data=df,
    x='plano',
    y='dias_atraso',
    hue='plano',
    order=['Mensal', 'Semestral', 'Anual'],
    legend=False,
    palette=['#1f6feb', '#12805c', '#7b3fe4']
)
plt.title('Dias de atraso por plano\n(linha central = mediana | pontos = outliers)')
plt.xlabel('Plano')
plt.ylabel('Dias de atraso')
salvar('ex8_boxplot_atraso_por_plano.png')


# ─────────────────────────────────────────────────────────────────────────────
# EXERCÍCIO 4 — Faixas de idade com pd.cut + média de atraso por faixa
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("✏️  EXERCÍCIO 4 — Faixas de idade com pd.cut")
print("=" * 65)
print("""SQL:
  SELECT CASE WHEN idade <= 12 THEN 'Infantil (≤12)'
              WHEN idade <= 17 THEN 'Adolescente (13-17)'
              WHEN idade <= 30 THEN 'Adulto (18-30)'
              ELSE                  'Sênior (31+)'
         END faixa,
         COUNT(*) alunos,
         AVG(dias_atraso) media_atraso
  FROM alunos
  GROUP BY 1
  ORDER BY 1""")

# pd.cut = CASE WHEN com ranges numéricos
df['faixa_idade'] = pd.cut(
    df['idade_limpa'],                              # coluna sem nulos
    bins=[0, 12, 17, 30, 100],                     # limites dos intervalos
    labels=['Infantil (≤12)', 'Adolescente (13-17)', 'Adulto (18-30)', 'Sênior (31+)']
)

# GROUP BY faixa com múltiplas agregações
resultado_faixa = df.groupby('faixa_idade', observed=True).agg(
    alunos       = ('aluno_id',   'count'),
    media_atraso = ('dias_atraso', 'mean'),
    mediana      = ('dias_atraso', 'median'),
    pct_atrasam  = ('dias_atraso', lambda s: (s > 0).mean() * 100)
).round(1)

print("\nMédia de atraso por faixa de idade:")
print(resultado_faixa.to_string())

# Gráfico de barras por faixa de idade
plt.figure(figsize=(9, 5))
cores = ['#58a6ff', '#3fb950', '#f97316', '#bc8cff']
bars = plt.bar(
    resultado_faixa.index,
    resultado_faixa['media_atraso'],
    color=cores,
    edgecolor='#30363d',
    linewidth=0.8
)
# Rótulo com o valor em cima de cada barra
for bar, val in zip(bars, resultado_faixa['media_atraso']):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{val:.1f}d', ha='center', va='bottom', fontsize=10, color='white')
plt.title('Média de dias de atraso por faixa etária (GATE4)')
plt.xlabel('Faixa de Idade')
plt.ylabel('Média de dias de atraso')
plt.xticks(rotation=15)
salvar('ex8_atraso_por_faixa_idade.png')


# ─────────────────────────────────────────────────────────────────────────────
# CONCLUSÕES — como apresentar ao dono do haras
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("📋 CONCLUSÕES — O que apresentar ao dono do haras")
print("=" * 65)

pct_em_dia = (df['dias_atraso'] == 0).mean() * 100
plano_pior = medianas.idxmax()
pct_30     = len(df[df['dias_atraso'] > 30]) / len(df) * 100

print(f"""
  ✅ {pct_em_dia:.0f}% dos alunos pagam em dia — situação saudável.
  
  ⚠️  {pct_30:.0f}% dos alunos têm atraso superior a 30 dias —
     estes devem ser priorizados no contato de cobrança.
  
  📊 Plano {plano_pior} tem a maior mediana de atraso —
     pode indicar perfil de cliente diferente ou instabilidade financeira.
  
  🔍 2 mensalidades com valores ×10 acima do normal detectadas —
     verificar cadastro e corrigir na fonte.
  
  💡 CUIDADO: estas são correlações, não causas.
     Próximo passo: modelo de churn para prever quem cancelará.
""")

print("=" * 65)
print("✅ Exercício 8 concluído — EDA completa com 4 exercícios!")
print("   Gráficos salvos em saidas/ex8_*.png")
print("   Próximo: ex09_visualizacoes_avancadas.py")
print("=" * 65 + "\n")
