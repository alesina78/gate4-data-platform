"""
=============================================================================
PROJETO: GATE4 - Transição de SQL para Pandas (Análise de Dados)
AULA 2: Séries Temporais e Análise de Tendências com Pandas
AUTOR: Alessandro Lesina Giordano
DESCRIÇÃO: Este script demonstra a manipulação de dados temporais no Pandas
           focando em faturamento mensal, cálculos de LAG, médias móveis
           e taxa de crescimento, conectando com funções analíticas SQL.

COMO EXECUTAR NO TERMINAL (Git Bash no VS Code):
    source .venv/Scripts/activate && python 02_series_temporais_pandas.py
=============================================================================
"""

import pandas as pd
import numpy as np

# Exibição: mostra TODAS as colunas na tela, sem cortar com "..." (só afeta o print).
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

# =============================================================================
# 1. GERANDO DADOS SIMULADOS DE VENDAS DIÁRIAS (GATE4)
# =============================================================================
# Em SQL, criaríamos uma sequência de datas usando CONNECT BY LEVEL (Oracle)
# ou generate_series() (PostgreSQL). No Pandas, usamos pd.date_range().

# Gerador moderno do NumPy. A seed (42) deixa os números iguais a cada execução.
rng = np.random.default_rng(42)

# Criando um calendário de 24 meses de vendas (2025 e 2026)
datas = pd.date_range(start='2025-01-01', end='2026-12-31', freq='D')

# Uma série temporal real tem 3 partes: TENDÊNCIA + SAZONALIDADE + RUÍDO.
# Montamos as três com NumPy para que a análise tenha algo a mostrar.
dia = np.arange(len(datas))                                            # 0, 1, 2... um número por dia
tendencia = 800 + 0.5 * dia                                            # sobe ~R$ 0,50 por dia
sazonal = 150 * np.sin(2 * np.pi * datas.dayofyear.to_numpy() / 365)   # sobe e desce ao longo do ano
ruido = rng.normal(0, 80, size=len(datas))                             # variação aleatória do dia a dia
vendas_diarias = np.clip(tendencia + sazonal + ruido, 0, None)         # nunca negativo

# Montando o DataFrame base
df_vendas = pd.DataFrame({
    'data_venda': datas,
    'valor': vendas_diarias
})

print("--- PRIMEIRAS 5 LINHAS DO HISTÓRICO DIÁRIO ---")
print(df_vendas.head())


# =============================================================================
# 2. AGRUPAMENTO TEMPORAL (RESAMPLE / GROUP BY MÊS)
# =============================================================================
# EQUIVALENTE EM SQL (Oracle):
# SELECT TRUNC(data_venda, 'MM') AS mes, SUM(valor) AS fat_mensal
# FROM df_vendas
# GROUP BY TRUNC(data_venda, 'MM')
# ORDER BY mes;

# No Pandas, transformamos a coluna de data em ÍNDICE para usar o .resample():
faturamento_mensal = (
    df_vendas
    .set_index('data_venda')              # Define a coluna de data como índice
    .resample('MS')['valor']              # 'MS' = Month Start (início do mês)
    .sum()                                # Agregação SUM
    .to_frame(name='fat_mensal')          # Converte a Series de volta para DataFrame
    .rename_axis('mes')                   # SQL: "AS mes" (o índice se chamava data_venda)
)

# Conferência (hábito de pipeline): 2025 e 2026 = 24 meses.
assert len(faturamento_mensal) == 24, "Esperava 24 meses (2025 e 2026)"
print("\nMeses no resultado:", len(faturamento_mensal))


# =============================================================================
# 3. ENGENHARIA DE FEATURES TEMPORAIS (ANÁLISE ANALÍTICA)
# =============================================================================

# A) LAG 1 MÊS (Faturamento do mês anterior)
# SQL: LAG(fat_mensal, 1) OVER (ORDER BY mes)
faturamento_mensal['fat_mes_anterior'] = faturamento_mensal['fat_mensal'].shift(1)

# B) VARIAÇÃO PERCENTUAL MÊS A MÊS (%)
# SQL: (fat_mensal - LAG(fat_mensal, 1) OVER (...)) / LAG(fat_mensal, 1) OVER (...)
faturamento_mensal['crescimento_pct'] = faturamento_mensal['fat_mensal'].pct_change() * 100

# C1) MÉDIA MÓVEL DE 3 MESES: INCLUI o mês atual (boa para relatórios)
# SQL: AVG(fat_mensal) OVER (ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
faturamento_mensal['media_movel_3m'] = faturamento_mensal['fat_mensal'].rolling(window=3).mean()

# C2) MÉDIA DOS 3 MESES ANTERIORES: NÃO inclui o mês atual.
# Necessária em Machine Learning: senão o modelo "vê" o valor que quer prever = LEAKAGE.
# SQL: AVG(fat_mensal) OVER (ORDER BY mes ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING)
faturamento_mensal['media_3m_anteriores'] = (
    faturamento_mensal['fat_mensal'].shift(1).rolling(window=3).mean()
)

# Os NaN iniciais são esperados: o Pandas só calcula com 3 meses completos
# (o SQL calcularia com menos linhas). Para mudar: rolling(3, min_periods=1).


# =============================================================================
# 4. EXIBIÇÃO E ARREDONDAMENTO
# =============================================================================
# Formatando valores numéricos para 2 casas decimais para visualização limpa
faturamento_formatado = faturamento_mensal.round(2)

print("\n--- RELATÓRIO DE SÉRIES TEMPORAIS - FATURAMENTO MENSAL (GATE4) ---")
print(faturamento_formatado)