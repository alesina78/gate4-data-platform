"""
=============================================================================
PROJETO: GATE4 - Transição de SQL para Pandas (Análise de Dados)
AULA 3: NumPy + Análise Exploratória de Dados (EDA) + Gráficos
AUTOR: Alessandro Lesina Giordano
DESCRIÇÃO: Este script mostra como "conhecer" um conjunto de dados antes de
           modelar: estatísticas, valores nulos, outliers e gráficos,
           sempre fazendo o paralelo com SQL.'

ANTES DE RODAR (uma vez só, com o (.venv) ligado no terminal Git Bash):
    pip install seaborn

COMO EXECUTAR:
    source .venv/Scripts/activate && python 03_numpy_eda_visualizacao.py

SAÍDA: os gráficos são salvos como imagens PNG na pasta "saidas/".
       Abra os arquivos no VS Code (clique neles no Explorer) para vê-los.
=============================================================================
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt   # Matplotlib: a base dos gráficos (controle fino)
import seaborn as sns             # Seaborn: gráficos estatísticos prontos, por cima do Matplotlib

# Exibição: mostra todas as colunas e 2 casas decimais (só afeta o print).
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.options.display.float_format = '{:.2f}'.format

# Se True, abre uma janela para cada gráfico (o script pausa até você fechá-la).
# Se False, apenas salva os arquivos PNG.
MOSTRAR_JANELAS = False

PASTA_SAIDA = Path("saidas")
PASTA_SAIDA.mkdir(exist_ok=True)   # cria a pasta se não existir (como CREATE ... IF NOT EXISTS)


def salvar(nome_arquivo):
    """Salva o gráfico atual em saidas/ e, se quiser, também mostra na tela."""
    caminho = PASTA_SAIDA / nome_arquivo
    plt.tight_layout()
    plt.savefig(caminho, dpi=120)
    print(f"  gráfico salvo em: {caminho}")
    if MOSTRAR_JANELAS:
        plt.show()
    plt.close()


# =============================================================================
# 1. NUMPY: A BASE DO PANDAS
# =============================================================================
# O Pandas guarda cada coluna como um "array" do NumPy. Entender o NumPy
# explica por que as operações do Pandas são rápidas.
print("=" * 70)
print("1. NUMPY")
print("=" * 70)

rng = np.random.default_rng(42)   # gerador de números aleatórios; a seed deixa o resultado repetível

# 1.1 Array = uma coluna de números (equivale a uma coluna de tabela SQL)
mensalidades = np.array([350.0, 420.0, 300.0, 500.0, 380.0])

# 1.2 VETORIZAÇÃO: a operação vale para TODOS os elementos de uma vez.
# É o "SQL baseado em conjunto" (sem LOOP/cursor):  UPDATE ... SET valor = valor * 1.10
reajustadas = mensalidades * 1.10
print("Mensalidades reajustadas em 10%:", reajustadas)

# 1.3 ESTATÍSTICAS DESCRITIVAS (equivalem a AVG, STDDEV e PERCENTILE_CONT do SQL)
print("\nMédia   :", np.mean(mensalidades))                 # AVG(valor)
print("Mediana :", np.median(mensalidades))                  # MEDIAN(valor)
print("Desvio  :", np.std(mensalidades, ddof=1))             # STDDEV(valor)  (ddof=1 = amostral, como o SQL)
print("P90     :", np.percentile(mensalidades, 90))          # PERCENTILE_CONT(0.9)

# 1.4 np.where = CASE WHEN com duas saídas
# SQL: CASE WHEN valor >= 400 THEN 'Alta' ELSE 'Baixa' END
faixa = np.where(mensalidades >= 400, "Alta", "Baixa")
print("\nFaixa:", faixa)

# 1.5 LOOP x VETORIZAÇÃO: meça você mesmo a diferença (os números dependem do seu computador)
grande = rng.random(1_000_000)

inicio = time.perf_counter()
soma_loop = 0.0
for x in grande:               # percorre elemento por elemento (como um cursor)
    soma_loop += x * 2
tempo_loop = time.perf_counter() - inicio

inicio = time.perf_counter()
soma_vetor = (grande * 2).sum()   # uma operação sobre o conjunto inteiro
tempo_vetor = time.perf_counter() - inicio

print(f"\n1 milhão de números -> loop: {tempo_loop:.4f}s | vetorizado: {tempo_vetor:.4f}s")


# =============================================================================
# 2. DADOS SIMULADOS DO GATE4 (um registro por aluno)
# =============================================================================
# Simulamos com NumPy um retrato dos alunos. Os dados têm "sujeira" de propósito
# (valores nulos e erros de digitação) para praticarmos a EDA.
# ATENÇÃO: a relação entre aulas e atraso foi construída por nós neste exemplo.
# Nos dados reais do GATE4 você DESCOBRIRIA (ou não) essa relação.
print("\n" + "=" * 70)
print("2. DADOS SIMULADOS")
print("=" * 70)

N = 150
plano = rng.choice(["Mensal", "Semestral", "Anual"], size=N, p=[0.60, 0.25, 0.15])

# np.select = CASE WHEN com várias saídas (a mensalidade-base depende do plano)
base = np.select([plano == "Mensal", plano == "Semestral"], [450.0, 420.0], default=380.0)
valor_mensalidade = np.round(base + rng.normal(0, 30, size=N), 2)

# Aulas nos últimos 90 dias: contagem de eventos -> distribuição de Poisson
aulas_90d = rng.poisson(lam=np.where(plano == "Mensal", 14, 10))

# Quem tem poucas aulas atrasa mais o pagamento (regra criada para o exemplo)
prob_atraso = 0.15 + 0.30 * (aulas_90d < 8)
em_dia = rng.random(N) > prob_atraso
dias_atraso = np.where(em_dia, 0, np.round(rng.lognormal(mean=2.3, sigma=0.8, size=N)))

idade = rng.integers(8, 65, size=N).astype(float)   # float, porque inteiros não aceitam NaN

df = pd.DataFrame({
    "aluno_id": np.arange(1, N + 1),
    "plano": plano,
    "idade": idade,
    "aulas_90d": aulas_90d,
    "valor_mensalidade": valor_mensalidade,
    "dias_atraso": dias_atraso,
})

# "Sujeira" de propósito:
df.loc[rng.choice(N, size=6, replace=False), "idade"] = np.nan   # 6 idades não informadas (NULL)
df.loc[[10, 77], "valor_mensalidade"] *= 10                      # 2 erros de digitação (valor x10)

print(df.head())


# =============================================================================
# 3. EDA: CONHECENDO OS DADOS
# =============================================================================
print("\n" + "=" * 70)
print("3. EDA - PRIMEIRO CONTATO")
print("=" * 70)

# 3.1 Tamanho e tipos            SQL: SELECT COUNT(*) ... / DESCRIBE tabela
print("Linhas x colunas:", df.shape)
print("\nTipos das colunas:")
print(df.dtypes)

# 3.2 Resumo estatístico         SQL: COUNT, AVG, STDDEV, MIN, MAX e percentis de cada coluna
print("\nResumo estatístico:")
print(df.describe())

# 3.3 Valores nulos              SQL: COUNT(*) - COUNT(coluna)  ou  SUM(CASE WHEN col IS NULL THEN 1 ELSE 0 END)
print("\nValores nulos por coluna (quantidade e %):")
nulos = pd.DataFrame({"qtd": df.isna().sum(), "pct": df.isna().mean() * 100})
print(nulos)

# 3.4 Contagem por categoria     SQL: SELECT plano, COUNT(*) FROM alunos GROUP BY plano
print("\nAlunos por plano:")
print(df["plano"].value_counts())

# 3.5 Duplicados                 SQL: GROUP BY aluno_id HAVING COUNT(*) > 1
print("\nLinhas duplicadas por aluno_id:", df.duplicated(subset="aluno_id").sum())

# 3.6 Estatística por grupo      SQL: GROUP BY plano com AVG, MEDIAN (percentil) e MAX
print("\nDias de atraso por plano:")
print(df.groupby("plano")["dias_atraso"].agg(media="mean", mediana="median", maximo="max"))


# =============================================================================
# 4. OUTLIERS (VALORES FORA DO NORMAL)
# =============================================================================
# Regra do IQR (a mesma que o boxplot desenha):
#   Q1 = percentil 25, Q3 = percentil 75, IQR = Q3 - Q1
#   outlier = abaixo de Q1 - 1,5*IQR  ou  acima de Q3 + 1,5*IQR
print("\n" + "=" * 70)
print("4. OUTLIERS NA MENSALIDADE")
print("=" * 70)

# 4.1 Olhando a base TODA
q1, q3 = np.percentile(df["valor_mensalidade"], [25, 75])   # SQL: PERCENTILE_CONT(0.25) e (0.75)
iqr = q3 - q1
limite_baixo, limite_alto = q1 - 1.5 * iqr, q3 + 1.5 * iqr
print(f"Q1={q1:.2f}  Q3={q3:.2f}  IQR={iqr:.2f}  -> faixa normal: {limite_baixo:.2f} a {limite_alto:.2f}")

fora_da_base = df[(df["valor_mensalidade"] < limite_baixo) | (df["valor_mensalidade"] > limite_alto)]
print("\nMensalidades fora da faixa (olhando a base toda):")
print(fora_da_base[["aluno_id", "plano", "valor_mensalidade"]])
print("\nCUIDADO: os planos têm preços diferentes. Um valor baixo do plano Anual pode ser")
print("NORMAL para ele e só parecer estranho quando comparado com a base toda.")

# 4.2 Olhando DENTRO de cada plano (o contexto importa)
# SQL: PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor) OVER (PARTITION BY plano)
# groupby + transform devolve, para CADA linha, o valor calculado para o plano dela.
q1_plano = df.groupby("plano")["valor_mensalidade"].transform(lambda s: s.quantile(0.25))
q3_plano = df.groupby("plano")["valor_mensalidade"].transform(lambda s: s.quantile(0.75))
iqr_plano = q3_plano - q1_plano
fora_do_plano = (
    (df["valor_mensalidade"] < q1_plano - 1.5 * iqr_plano)
    | (df["valor_mensalidade"] > q3_plano + 1.5 * iqr_plano)
)
print("\nMensalidades fora da faixa DENTRO do próprio plano:")
print(df.loc[fora_do_plano, ["aluno_id", "plano", "valor_mensalidade"]])
# A regra do IQR aponta CANDIDATOS, não certezas: um valor só um pouco fora do padrão
# pode ser variação natural. Os valores 10 vezes maiores são os erros claros.
# Quem decide é o negócio (olhe o cadastro original antes de corrigir).

# Média x mediana: o outlier puxa a MÉDIA, mas quase não mexe na MEDIANA.
print(f"\nMédia: {df['valor_mensalidade'].mean():.2f} | Mediana: {df['valor_mensalidade'].median():.2f}")

# Tratamento (uma decisão de negócio!): aqui, marcamos como nulo em vez de apagar o aluno.
# where() mantém o valor quando a condição é verdadeira e coloca NaN quando é falsa.
df["valor_limpo"] = df["valor_mensalidade"].where(~fora_do_plano)   # o "~" inverte: mantém quem NÃO é outlier
# Idade ausente: preencher com a mediana (SQL: NVL(idade, <mediana>))
df["idade_limpa"] = df["idade"].fillna(df["idade"].median())


# =============================================================================
# 5. VISUALIZAÇÕES
# =============================================================================
print("\n" + "=" * 70)
print("5. GRÁFICOS")
print("=" * 70)
sns.set_theme(style="whitegrid")

# 5.1 HISTOGRAMA: como os valores se distribuem?
# Atenção: muita gente paga em dia (atraso 0) e poucos atrasam muito (cauda longa).
plt.figure(figsize=(8, 4))
sns.histplot(df["dias_atraso"], bins=20, kde=True, color="navy")
plt.title("Distribuição dos dias de atraso")
plt.xlabel("Dias de atraso")
plt.ylabel("Quantidade de alunos")
salvar("01_hist_dias_atraso.png")

# 5.2 BOXPLOT: mediana, quartis e outliers por grupo
plt.figure(figsize=(8, 4))
sns.boxplot(data=df, x="plano", y="valor_mensalidade", hue="plano", legend=False,
            order=["Mensal", "Semestral", "Anual"])
plt.title("Mensalidade por plano (pontos isolados = outliers)")
salvar("02_boxplot_mensalidade_plano.png")

# 5.3 BARRAS: média de atraso por plano (agregação -> gráfico)
media_atraso = df.groupby("plano")["dias_atraso"].mean().reindex(["Mensal", "Semestral", "Anual"])
plt.figure(figsize=(6, 4))
plt.bar(media_atraso.index, media_atraso.values, color=["#1f6feb", "#12805c", "#7b3fe4"])
plt.title("Média de dias de atraso por plano")
plt.ylabel("Dias")
salvar("03_barras_atraso_plano.png")

# 5.4 DISPERSÃO: relação entre duas variáveis numéricas
plt.figure(figsize=(7, 5))
sns.scatterplot(data=df, x="aulas_90d", y="dias_atraso", hue="plano")
plt.title("Aulas nos últimos 90 dias x dias de atraso")
salvar("04_dispersao_aulas_atraso.png")

# 5.5 MAPA DE CALOR DA CORRELAÇÃO   SQL (Oracle): CORR(a, b)
# Vai de -1 (uma sobe, a outra desce) a +1 (sobem juntas). Perto de 0 = sem relação linear.
colunas_num = ["idade_limpa", "aulas_90d", "valor_limpo", "dias_atraso"]
correlacao = df[colunas_num].corr()
plt.figure(figsize=(7, 5))
sns.heatmap(correlacao, annot=True, cmap="coolwarm", fmt=".2f", vmin=-1, vmax=1)
plt.title("Correlação entre as variáveis")
salvar("05_mapa_correlacao.png")

print("\nCorrelação aulas_90d x dias_atraso:", round(correlacao.loc["aulas_90d", "dias_atraso"], 2))
print("(perto de 0 = fraca. A correlação de Pearson é sensível a poucos atrasos muito grandes;")
print(" por isso também comparamos GRUPOS, que é mais fácil de explicar:)")

# Comparação de grupos   SQL: GROUP BY CASE WHEN aulas_90d < 8 THEN ... END
comparacao = df.groupby(df["aulas_90d"] < 8).agg(
    alunos=("aluno_id", "count"),
    pct_atrasam=("dias_atraso", lambda s: (s > 0).mean() * 100),
    media_atraso=("dias_atraso", "mean"),
).rename(index={True: "menos de 8 aulas", False: "8 aulas ou mais"})
print(comparacao)


# =============================================================================
# 6. CONCLUSÕES (o que você diria ao dono do haras)
# =============================================================================
print("\n" + "=" * 70)
print("6. CONCLUSÕES")
print("=" * 70)
pct_atrasam = (df["dias_atraso"] > 0).mean() * 100
print(f"- {pct_atrasam:.0f}% dos alunos atrasam o pagamento; a maioria paga em dia e poucos atrasam muito.")
print("- A mediana de atraso representa melhor o aluno 'típico' do que a média (cauda longa).")
print(f"- {fora_do_plano.sum()} mensalidades fogem do padrão do próprio plano: corrigir na origem e validar o cadastro.")
pct_pouco = comparacao.loc["menos de 8 aulas", "pct_atrasam"]
pct_muito = comparacao.loc["8 aulas ou mais", "pct_atrasam"]
print(f"- Atrasam o pagamento {pct_pouco:.0f}% de quem faz menos de 8 aulas, contra {pct_muito:.0f}% dos demais:")
print("  é uma pista para o modelo de churn.")
print("  CUIDADO: correlação NÃO prova causa. É uma hipótese a investigar.")


# =============================================================================
# 7. EXERCÍCIOS (tente você mesmo, sem copiar)
# =============================================================================
# 1) Quantos alunos têm mais de 30 dias de atraso? Qual a % do total?
#    SQL: SELECT COUNT(*) FROM alunos WHERE dias_atraso > 30;
# 2) Crie a coluna "faixa_atraso" com np.select: 'Em dia' (0), 'Até 15 dias', 'Mais de 15 dias'.
# 3) Faça um boxplot dos dias de atraso por plano. Qual plano tem a maior mediana?
# 4) Depois de preencher a idade, crie faixas com pd.cut (até 12, 13-17, 18-30, 31+)
#    e calcule a média de atraso por faixa (SQL: GROUP BY CASE WHEN ...).