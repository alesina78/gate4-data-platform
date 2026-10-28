"""
=============================================================================
PROJETO: GATE4 - Transição de SQL para Pandas (Análise de Dados)
AUTOR: Alessandro Lesina Giordano
DESCRIÇÃO: Este script demonstra operações fundamentais em Pandas (DataFrame,
           Merge, Groupby e NumPy), fazendo o paralelo direto com comandos SQL.

           OBS: Para rodar este script no terminal do VS Code (Git Bash),
           execute antes:
               source .venv/Scripts/activate
               python 01_teste_pandas.py
=============================================================================
"""

# =============================================================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# =============================================================================
# PANDAS: Motor principal para manipulação, transformação e análise de dados tabulares.
import pandas as pd

# NUMPY: Biblioteca de computação numérica de alta performance.
# O Pandas é construído por cima do NumPy. Aqui usamos o np.select (seção 2.4),
# que faz o papel do CASE WHEN do SQL.
import numpy as np

# Só afeta a EXIBIÇÃO dos números decimais (2 casas); os dados não mudam.
pd.options.display.float_format = '{:.2f}'.format


# =============================================================================
# 1. CRIAÇÃO DE DADOS SIMULADOS (Tabelas do Sistema GATE4)
# =============================================================================
# No mundo relacional (Oracle/PostgreSQL), estes dados estariam armazenados
# em tabelas físicas. Aqui, simulamos tabelas utilizando dicionários do Python.

# Tabela de Alunos (Dimensão)
dados_alunos = {
    'aluno_id': [1, 2, 3, 4, 5],
    'nome': ['Alessandro', 'Mariana', 'Carlos', 'Beatriz', 'Lucas'],
    'plano': ['Mensal', 'Anual', 'Mensal', 'Semestral', 'Mensal'],
    'status': ['Ativo', 'Ativo', 'Inativo', 'Ativo', 'Inativo']
}

# Tabela de Faturas (Fato / Transacional)
dados_faturas = {
    'fatura_id': [101, 102, 103, 104, 105, 106],
    'aluno_id': [1, 1, 2, 2, 3, 4],
    'valor': [250.00, 250.00, 1200.00, 1200.00, 250.00, 600.00],
    'status_pagamento': ['Pago', 'Pago', 'Pago', 'Pendente', 'Cancelado', 'Pago']
}

# PANDAS - Criação de DataFrames:
# Transformamos os dicionários em estruturas tabulares na memória (DataFrames).
# O DataFrame é o equivalente direto a uma tabela de banco de dados ou result set.
df_alunos = pd.DataFrame(dados_alunos)
df_faturas = pd.DataFrame(dados_faturas)

# HÁBITO DE ANALISTA: sempre olhar os dados ANTES de transformar.
print("--- df_alunos ---")                       # SQL: SELECT * FROM alunos
print(df_alunos)
print("\n--- df_faturas ---")                    # SQL: SELECT * FROM faturas
print(df_faturas)
print("\nTipos das colunas (df_faturas):")       # SQL: DESCRIBE faturas
print(df_faturas.dtypes)
print("\nLinhas x colunas (df_faturas):", df_faturas.shape)


# =============================================================================
# 2. TRADUÇÃO SQL -> PANDAS (JOIN, FILTRO, AGREGAÇÃO E ORDENAÇÃO)
# =============================================================================

# -----------------------------------------------------------------------------
# 2.1 JOIN
# -----------------------------------------------------------------------------
# EQUIVALENTE EM SQL:
# SELECT a.nome, f.valor, f.status_pagamento
# FROM alunos a
# LEFT JOIN faturas f ON a.aluno_id = f.aluno_id;

# PANDAS - Método .merge():
# Realiza o cruzamento das tabelas (equivalente ao LEFT JOIN) usando 'aluno_id' como chave.
df_merged = df_alunos.merge(
    df_faturas,
    on='aluno_id',
    how='left',
    validate='one_to_many'   # 1 aluno : N faturas. Dá ERRO se aluno_id repetir em df_alunos
                             # (funciona como uma constraint: evita multiplicar linhas em silêncio)
)

# Olhe a saída: Lucas aparece com NaN (o NULL do Pandas) porque não tem fatura.
# Repare também que fatura_id passou a aparecer como 101.00 (decimal): um inteiro
# comum não aceita NaN, então o Pandas converte a coluna inteira para decimal.
print("\n--- Resultado do LEFT JOIN ---")
print(df_merged)


# -----------------------------------------------------------------------------
# 2.2 FILTRO + AGRUPAMENTO + ORDENAÇÃO
# -----------------------------------------------------------------------------
# EQUIVALENTE EM SQL:
# SELECT nome, SUM(valor) AS total_pago, COUNT(fatura_id) AS qtd_faturas
# FROM (tabela unida acima)
# WHERE status_pagamento = 'Pago'
# GROUP BY nome
# ORDER BY total_pago DESC;

faturamento_por_aluno = (
    # PANDAS - Filtragem de Dados (equivalente ao WHERE do SQL):
    # Seleciona apenas as linhas onde o status de pagamento é estritamente 'Pago'.
    # ATENÇÃO: o filtro vem DEPOIS do LEFT JOIN, como um WHERE. Por isso Carlos
    # (fatura cancelada) e Lucas (sem fatura) NÃO aparecem no resultado.
    df_merged[df_merged['status_pagamento'] == 'Pago']

    # PANDAS - Agrupamento (equivalente ao GROUP BY):
    # Agrupa os dados por 'nome'. O parâmetro as_index=False mantém 'nome'
    # como coluna normal do DataFrame, evitando que vire o índice da tabela.
    .groupby('nome', as_index=False)

    # PANDAS - Funções de Agregação (.agg() equivalente a SUM e COUNT):
    # Aplica operações matemáticas nas colunas especificadas.
    .agg(
        total_pago=('valor', 'sum'),       # Equivalente a SUM(valor) AS total_pago
        qtd_faturas=('fatura_id', 'count') # Equivalente a COUNT(fatura_id) AS qtd_faturas
    )

    # PANDAS - Ordenação (equivalente ao ORDER BY ... DESC):
    # Ordena o resultado de forma decrescente com base no valor total pago.
    .sort_values('total_pago', ascending=False)

    # Renumera as linhas 0,1,2... (sem isso, os números do índice ficam "embaralhados"
    # depois da ordenação, pois guardam a posição original do groupby).
    .reset_index(drop=True)
)


# -----------------------------------------------------------------------------
# 2.3 MANTENDO TODOS OS ALUNOS (filtro ANTES do join)
# -----------------------------------------------------------------------------
# Filtrar as faturas ANTES do join equivale a colocar a condição no ON, não no WHERE:
# SQL: ... FROM alunos a LEFT JOIN faturas f
#          ON a.aluno_id = f.aluno_id AND f.status_pagamento = 'Pago'
faturas_pagas = df_faturas[df_faturas['status_pagamento'] == 'Pago']

faturamento_todos = (
    df_alunos.merge(faturas_pagas, on='aluno_id', how='left')
    .groupby('nome', as_index=False)
    # A soma de NaN dá 0 e o count ignora NaN: quem não pagou nada fica com 0.
    .agg(total_pago=('valor', 'sum'), qtd_faturas=('fatura_id', 'count'))
    .sort_values('total_pago', ascending=False)
    .reset_index(drop=True)
)


# -----------------------------------------------------------------------------
# 2.4 NUMPY COMO CASE WHEN
# -----------------------------------------------------------------------------
# SQL: CASE WHEN valor >= 1000 THEN 'Alto'
#           WHEN valor >= 500  THEN 'Médio'
#           ELSE 'Baixo' END
df_faturas['faixa'] = np.select(
    [df_faturas['valor'] >= 1000, df_faturas['valor'] >= 500],  # condições, na ordem
    ['Alto', 'Médio'],                                          # resultado de cada condição
    default='Baixo'                                             # ELSE
)


# =============================================================================
# 3. EXIBIÇÃO DOS RESULTADOS
# =============================================================================
print("\n--- FATURAMENTO POR ALUNO (GATE4) ---")
print(faturamento_por_aluno)

print("\n--- TODOS OS ALUNOS (Carlos e Lucas com zero) ---")
print(faturamento_todos)

print("\n--- Faixa de valor por fatura ---")
print(df_faturas[['fatura_id', 'valor', 'faixa']])