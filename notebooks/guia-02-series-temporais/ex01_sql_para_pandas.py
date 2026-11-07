"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 2, Exercício 1                                  ║
║  Arquivo : ex01_sql_para_pandas.py                                           ║
║  Tema    : Tradução SQL → Pandas (contagem e média móvel de aulas/mês)      ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Converter uma query Oracle com GROUP BY mensal e AVG OVER (janela analítica)
para o equivalente Pandas — sem mudar o resultado, apenas a ferramenta.

QUERY ORIGINAL (Oracle)
-----------------------
    SELECT TRUNC(data_aula, 'MM')   AS mes,
           COUNT(*)                 AS aulas,
           AVG(COUNT(*)) OVER (
               ORDER BY TRUNC(data_aula, 'MM')
               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
           )                        AS media_3m
    FROM   aulas
    GROUP  BY TRUNC(data_aula, 'MM')
    ORDER  BY 1;

CONCEITOS PANDAS USADOS
-----------------------
  pd.to_datetime()      → converte string/objeto para tipo data
  set_index()           → define a coluna de datas como índice do DataFrame
  resample('MS')        → agrupa por início de mês  (= TRUNC(data,'MM'))
  .size()               → conta linhas por grupo     (= COUNT(*))
  .rename()             → renomeia a Series resultante
  .to_frame()           → transforma Series em DataFrame (para adicionar colunas)
  .rolling(3)           → janela deslizante de 3 períodos (= ROWS BETWEEN 2 PRECEDING)
  .mean()               → média da janela             (= AVG(...))
  min_periods=1         → calcula mesmo com menos de 3 meses (início da série)

COMO RODAR
----------
  # No terminal Git Bash (VS Code):
  source .venv/Scripts/activate
  python ex01_sql_para_pandas.py
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd          # biblioteca principal de manipulação de dados
import numpy  as np          # usada para gerar dados simulados (seed fixa)

# ─────────────────────────────────────────────────────────────────────────────
# 1. DADOS — simulação de uma tabela "aulas" do GATE4
#    Em produção substitua por:
#    aulas = pd.read_csv('aulas_gate4.csv', parse_dates=['data_aula'])
#    ou conexão via SQLAlchemy / cx_Oracle
# ─────────────────────────────────────────────────────────────────────────────
rng = np.random.default_rng(seed=42)   # seed fixa → mesmo resultado toda vez que rodar

# Gera 300 registros de aulas espalhados entre jan/2024 e dez/2025
datas_aleatorias = pd.date_range(
    start='2024-01-01',
    end='2025-12-31',
    periods=300           # 300 aulas distribuídas nos 24 meses
)

# Embaralha as datas para simular variação real (alguns meses com mais, outros com menos)
datas_embaralhadas = pd.to_datetime(
    rng.choice(datas_aleatorias, size=300, replace=True)
)

# Monta o DataFrame com a coluna de data (como viria do banco)
aulas = pd.DataFrame({'data_aula': datas_embaralhadas})

print("=" * 60)
print("GATE4 — Exercício 1: SQL → Pandas")
print("=" * 60)
print(f"\n📋 Tabela 'aulas' simulada: {len(aulas)} registros")
print(f"   Período: {aulas['data_aula'].min().date()} → {aulas['data_aula'].max().date()}")
print(f"\nPrimeiras linhas da tabela bruta:")
print(aulas.head())


# ─────────────────────────────────────────────────────────────────────────────
# 2. GARANTIA DE TIPO — pd.to_datetime()
#    Oracle armazena DATE nativamente; ao importar CSV o Pandas pode ler
#    como string (object). to_datetime() converte para o tipo correto.
#
#    SQL equivalente: a coluna já é DATE no Oracle, não precisa converter
# ─────────────────────────────────────────────────────────────────────────────
aulas['data_aula'] = pd.to_datetime(aulas['data_aula'])
# Agora o dtype é datetime64[ns] — o Pandas entende que é uma data de verdade


# ─────────────────────────────────────────────────────────────────────────────
# 3. RESAMPLE — contar aulas por mês
#
#    SQL:    GROUP BY TRUNC(data_aula, 'MM')
#    Pandas: set_index('data_aula')      → coloca a data como "eixo" do DataFrame
#            .resample('MS')             → agrupa por início de mês (Month Start)
#            .size()                     → conta linhas de cada grupo (= COUNT(*))
#
#    Frequências úteis do resample:
#      'D'  = diário      'W'  = semanal
#      'MS' = mensal      'QS' = trimestral    'YS' = anual
# ─────────────────────────────────────────────────────────────────────────────
m = (
    aulas
    .set_index('data_aula')      # data_aula vira o índice — necessário para resample
    .resample('MS')              # agrupa por início de cada mês
    .size()                      # conta quantas aulas caíram naquele mês
    .rename('aulas')             # dá nome à coluna (como "AS aulas" no SQL)
    .to_frame()                  # transforma Series em DataFrame para poder adicionar colunas
)

print("\n" + "─" * 60)
print("PASSO 1 — Contagem de aulas por mês (GROUP BY mensal)")
print("─" * 60)
print(m)


# ─────────────────────────────────────────────────────────────────────────────
# 4. MÉDIA MÓVEL — rolling(3).mean()
#
#    SQL:    AVG(COUNT(*)) OVER (
#                ORDER BY TRUNC(data_aula,'MM')
#                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
#            )
#
#    Pandas: .rolling(3)          → janela de 3 linhas (mês atual + 2 anteriores)
#            .mean()              → média dos valores na janela
#            min_periods=1        → calcula mesmo quando há menos de 3 meses disponíveis
#                                   (nos 2 primeiros meses da série, o Oracle também calcula
#                                    com o que tem graças ao ROWS BETWEEN — min_periods replica isso)
#
#    POR QUE NÃO PRECISA DE shift(1) AQUI?
#    Porque estamos calculando a média de um AGREGADO já passado (aulas do mês),
#    não prevendo um valor futuro. O shift(1) é obrigatório quando você usa
#    rolling() como FEATURE de um modelo de ML — para não incluir o mês previsto.
# ─────────────────────────────────────────────────────────────────────────────
m['media_3m'] = (
    m['aulas']
    .rolling(window=3, min_periods=1)   # janela de 3 meses; min_periods=1 evita NaN no início
    .mean()                             # média da janela (= AVG OVER no Oracle)
    .round(1)                           # 1 casa decimal para facilitar leitura
)

print("\n" + "─" * 60)
print("PASSO 2 — Média móvel de 3 meses adicionada (AVG OVER)")
print("─" * 60)
print(m.to_string())   # to_string() mostra todas as linhas, sem truncar


# ─────────────────────────────────────────────────────────────────────────────
# 5. ANÁLISE RÁPIDA — perguntas que a dona do haras faria
# ─────────────────────────────────────────────────────────────────────────────
mes_pico    = m['aulas'].idxmax()   # mês com mais aulas
mes_fraco   = m['aulas'].idxmin()   # mês com menos aulas
media_geral = m['aulas'].mean()     # média mensal do período

print("\n" + "─" * 60)
print("ANÁLISE DE NEGÓCIO (GATE4)")
print("─" * 60)
print(f"  📈 Mês com MAIS  aulas : {mes_pico.strftime('%B/%Y')} → {m.loc[mes_pico, 'aulas']} aulas")
print(f"  📉 Mês com MENOS aulas : {mes_fraco.strftime('%B/%Y')} → {m.loc[mes_fraco, 'aulas']} aulas")
print(f"  📊 Média mensal geral  : {media_geral:.1f} aulas/mês")
print(f"\n  💡 A média móvel de 3m suaviza picos e revela a tendência real.")
print(f"     Compare a coluna 'aulas' com 'media_3m' para ver o efeito.\n")

# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO FINAL
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("RESULTADO FINAL — equivalente à query Oracle")
print("=" * 60)
print(m.to_string())
print("\n✅ Exercício 1 concluído.")
print("   Próximo: ex02_leakage_temporal.py\n")
