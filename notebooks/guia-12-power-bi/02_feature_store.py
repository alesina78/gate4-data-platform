"""
GATE4 Data Platform · Guia 12
Arquivo : 02_feature_store.py
Propósito: Calcular features de churn para cada aluno e gravar na tabela gold.

Analogia Oracle / ODI:
    Este script faz o que você faria num Package PL/SQL de ETL:
    1. Lê dados do banco (SELECT com JOINs e GROUP BY)
    2. Calcula colunas derivadas
    3. Grava na tabela de destino (INSERT ... ON CONFLICT DO UPDATE)

    Em Python/Pandas:
    - pd.read_sql()   ≈  OPEN cursor / FETCH (lê do banco)
    - df.merge()      ≈  JOIN
    - df.groupby()    ≈  GROUP BY
    - df.to_sql()     ≈  INSERT INTO ... SELECT

Execute:
    source .venv/Scripts/activate   # Git Bash Windows
    python scripts/guia12/02_feature_store.py

Requer:
    pip install pandas sqlalchemy psycopg2-binary python-dotenv
"""

import os
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv  # pip install python-dotenv

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
# Crie um arquivo .env na raiz com: DATABASE_URL=postgresql://user:pass@host/db
# Nunca comite o .env no Git! (já está no .gitignore)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gate4:gate4@localhost:5432/gate4_dw")

# ── CONSTANTES ────────────────────────────────────────────────────────────────
DATA_REFERENCIA = date.today()          # "hoje" para o cálculo das features
JANELA_30D      = DATA_REFERENCIA - timedelta(days=30)
JANELA_90D      = DATA_REFERENCIA - timedelta(days=90)
SCHEMA_GOLD     = "gold"
TABELA_DESTINO  = f"{SCHEMA_GOLD}.feature_store_churn"


# ── FUNÇÕES ───────────────────────────────────────────────────────────────────

def conectar_banco() -> object:
    """
    Cria e retorna uma engine SQLAlchemy.

    Analogia Oracle: equivale ao DBMS_CONNECTION ou ao TNS connect.
    A engine não abre conexão até a primeira consulta (lazy).
    """
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f"✅ Engine criada para: {DATABASE_URL.split('@')[-1]}")
    return engine


def extrair_dados_base(engine) -> dict[str, pd.DataFrame]:
    """
    Lê as tabelas necessárias do banco operacional.

    Analogia Oracle/ODI: é a fase de Extração de um fluxo de Interface ODI.
    Usamos read_sql para trazer só as colunas e linhas que precisamos
    — equivalente a empurrar o filtro para o banco (query folding).
    """

    # ── Alunos cadastrados ──────────────────────────────────────────────────
    # Analogia: SELECT a.id, a.data_cadastro, a.plano FROM alunos a
    sql_alunos = """
        SELECT
            a.id              AS aluno_id,
            a.data_cadastro,
            a.plano,          -- ex: 'MENSAL', 'TRIMESTRAL', 'ANUAL'
            a.haras_id,
            a.modalidade_id
        FROM alunos a
        WHERE a.ativo = TRUE
    """

    # ── Aulas realizadas ────────────────────────────────────────────────────
    # Analogia: SELECT aluno_id, data FROM aulas WHERE data >= SYSDATE - 90
    sql_aulas = f"""
        SELECT
            au.aluno_id,
            au.data,
            au.status         -- 'REALIZADA', 'FALTA', 'CANCELADA'
        FROM aulas au
        WHERE au.data >= '{JANELA_90D}'
          AND au.status = 'REALIZADA'
    """

    # ── Faturas pagas ───────────────────────────────────────────────────────
    sql_faturas = f"""
        SELECT
            f.aluno_id,
            f.valor,
            f.data_pagamento,
            f.status          -- 'PAGA', 'ATRASADA', 'PENDENTE'
        FROM faturas f
        WHERE f.data_vencimento >= '{JANELA_90D}'
    """

    print("📥 Lendo dados do banco...")
    with engine.connect() as conn:
        df_alunos  = pd.read_sql(sql_alunos,  conn)
        df_aulas   = pd.read_sql(sql_aulas,   conn)
        df_faturas = pd.read_sql(sql_faturas, conn)

    print(f"   Alunos ativos : {len(df_alunos):,}")
    print(f"   Aulas (90d)   : {len(df_aulas):,}")
    print(f"   Faturas (90d) : {len(df_faturas):,}")

    return {"alunos": df_alunos, "aulas": df_aulas, "faturas": df_faturas}


def calcular_features(dados: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Calcula as features de churn por aluno.

    Analogia Oracle: equivale a um bloco PL/SQL com GROUP BY e CASE WHEN
    numa query analítica que alimenta uma tabela de staging.

    Pandas vs SQL:
        df.groupby()  →  GROUP BY
        .agg()        →  SUM(), COUNT(), MAX()
        .merge()      →  JOIN
        .fillna()     →  NVL() / COALESCE()
        pd.cut()      →  CASE WHEN ... THEN ... (faixas)
    """

    df_alunos  = dados["alunos"].copy()
    df_aulas   = dados["aulas"].copy()
    df_faturas = dados["faturas"].copy()

    # ── Feature 1: Frequência de aulas nos últimos 30 dias ──────────────────
    # SQL equivalente: COUNT(*) FILTER (WHERE data >= SYSDATE-30) GROUP BY aluno_id
    aulas_30d = (
        df_aulas[df_aulas["data"] >= JANELA_30D.isoformat()]
        .groupby("aluno_id")
        .size()
        .reset_index(name="freq_aulas_30d")
    )

    # ── Feature 2: Frequência de aulas nos últimos 90 dias ──────────────────
    aulas_90d = (
        df_aulas
        .groupby("aluno_id")
        .size()
        .reset_index(name="freq_aulas_90d")
    )

    # ── Feature 3: Valor pago nos últimos 90 dias ───────────────────────────
    # SQL equivalente: SUM(valor) WHERE status = 'PAGA' GROUP BY aluno_id
    valor_90d = (
        df_faturas[df_faturas["status"] == "PAGA"]
        .groupby("aluno_id")["valor"]
        .sum()
        .reset_index(name="valor_pago_90d")
    )

    # ── Feature 4: Dias desde a última aula ─────────────────────────────────
    # SQL equivalente: CURRENT_DATE - MAX(data) GROUP BY aluno_id
    ultima_aula = (
        df_aulas
        .groupby("aluno_id")["data"]
        .max()
        .reset_index(name="data_ultima_aula")
    )
    ultima_aula["dias_sem_aula"] = (
        pd.Timestamp(DATA_REFERENCIA) - pd.to_datetime(ultima_aula["data_ultima_aula"])
    ).dt.days

    # ── Feature 5: Faturas em atraso ────────────────────────────────────────
    # SQL equivalente: COUNT(*) FILTER (WHERE status = 'ATRASADA') GROUP BY aluno_id
    faturas_atraso = (
        df_faturas[df_faturas["status"] == "ATRASADA"]
        .groupby("aluno_id")
        .size()
        .reset_index(name="qtd_faturas_atrasadas")
    )

    # ── Feature 6: Tempo de casa (dias desde o cadastro) ────────────────────
    # SQL equivalente: CURRENT_DATE - data_cadastro
    df_alunos["dias_como_aluno"] = (
        pd.Timestamp(DATA_REFERENCIA) - pd.to_datetime(df_alunos["data_cadastro"])
    ).dt.days

    # ── JOIN de todas as features ────────────────────────────────────────────
    # Analogia Oracle: equivale a um LEFT OUTER JOIN em série (CTE encadeados)
    df = (
        df_alunos
        .merge(aulas_30d,       on="aluno_id", how="left")
        .merge(aulas_90d,       on="aluno_id", how="left")
        .merge(valor_90d,       on="aluno_id", how="left")
        .merge(ultima_aula,     on="aluno_id", how="left")
        .merge(faturas_atraso,  on="aluno_id", how="left")
    )

    # ── COALESCE / NVL (tratar nulos para alunos sem aulas/faturas) ──────────
    # Analogia Oracle: NVL(freq_aulas_30d, 0)
    df["freq_aulas_30d"]        = df["freq_aulas_30d"].fillna(0).astype(int)
    df["freq_aulas_90d"]        = df["freq_aulas_90d"].fillna(0).astype(int)
    df["valor_pago_90d"]        = df["valor_pago_90d"].fillna(0.0)
    df["dias_sem_aula"]         = df["dias_sem_aula"].fillna(999)  # nunca fez aula
    df["qtd_faturas_atrasadas"] = df["qtd_faturas_atrasadas"].fillna(0).astype(int)

    # ── Feature derivada: queda de frequência (sinal forte de churn) ────────
    # (aulas nos últimos 30d) vs (média mensal nos 90d anteriores)
    media_mensal_90d = df["freq_aulas_90d"] / 3  # 90 dias / 3 meses
    df["variacao_freq"] = (df["freq_aulas_30d"] - media_mensal_90d).round(2)

    # ── Feature derivada: score de risco simples (heurística) ───────────────
    # Analogia Oracle: CASE WHEN ... THEN ... para gerar faixa
    df["score_risco_heur"] = (
          (df["dias_sem_aula"]         > 30).astype(int) * 30
        + (df["qtd_faturas_atrasadas"] > 0 ).astype(int) * 25
        + (df["variacao_freq"]         < -2).astype(int) * 25
        + (df["freq_aulas_30d"]        == 0).astype(int) * 20
    )

    # ── Faixa de risco (pd.cut = CASE WHEN com ranges) ──────────────────────
    df["faixa_risco"] = pd.cut(
        df["score_risco_heur"],
        bins=[-1, 25, 50, 101],
        labels=["BAIXO", "MEDIO", "ALTO"]
    ).astype(str)

    # ── Metadados de linhagem ────────────────────────────────────────────────
    df["data_ref"]      = DATA_REFERENCIA.isoformat()
    df["versao_script"] = "v1.0-heuristica"

    # ── Selecionar apenas as colunas da tabela destino ───────────────────────
    colunas_gold = [
        "aluno_id", "haras_id", "modalidade_id", "plano", "dias_como_aluno",
        "freq_aulas_30d", "freq_aulas_90d", "valor_pago_90d",
        "dias_sem_aula", "qtd_faturas_atrasadas", "variacao_freq",
        "score_risco_heur", "faixa_risco", "data_ref", "versao_script"
    ]
    df = df[[c for c in colunas_gold if c in df.columns]]

    print(f"\n📊 Features calculadas: {df.shape[0]:,} alunos × {df.shape[1]} features")
    print(df["faixa_risco"].value_counts().to_string())

    return df


def gravar_gold(df: pd.DataFrame, engine) -> None:
    """
    Grava as features na tabela gold (upsert por aluno_id + data_ref).

    Analogia Oracle/ODI:
        Equivale ao MERGE (INSERT ... ON DUPLICATE KEY UPDATE no PG).
        O if_exists='replace' em dev é equivalente a TRUNCATE + INSERT.
        Em produção, usar o MERGE via psycopg2 ou dbt.
    """
    print(f"\n💾 Gravando em {TABELA_DESTINO}...")

    with engine.begin() as conn:
        # Em dev: replace; em produção: append + chave única
        df.to_sql(
            name="feature_store_churn",
            con=conn,
            schema=SCHEMA_GOLD,
            if_exists="replace",   # dev: recria; prod: "append" com upsert
            index=False,
            method="multi",        # batch insert (mais rápido que linha a linha)
            chunksize=1000
        )

    print(f"✅ {len(df):,} linhas gravadas em {TABELA_DESTINO}")


def validar_resultado(engine) -> None:
    """
    Validação pós-carga: verifica contagem e distribuição de risco.

    Analogia Oracle: equivale a um CHECK no pacote ETL que você já faz
    com SELECT COUNT(*) após cada carga crítica.
    """
    sql = f"""
        SELECT
            faixa_risco,
            COUNT(*)                                      AS qtd_alunos,
            ROUND(AVG(dias_sem_aula)::NUMERIC, 1)         AS media_dias_sem_aula,
            ROUND(AVG(freq_aulas_30d)::NUMERIC, 1)        AS media_aulas_30d
        FROM {TABELA_DESTINO}
        WHERE data_ref = '{DATA_REFERENCIA}'
        GROUP BY faixa_risco
        ORDER BY qtd_alunos DESC
    """
    with engine.connect() as conn:
        df_check = pd.read_sql(sql, conn)

    print("\n📋 Validação — distribuição por faixa de risco:")
    print(df_check.to_string(index=False))


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("GATE4 · Feature Store de Churn")
    print(f"Data referência: {DATA_REFERENCIA}")
    print("=" * 60)

    engine  = conectar_banco()
    dados   = extrair_dados_base(engine)
    df_feat = calcular_features(dados)
    gravar_gold(df_feat, engine)
    validar_resultado(engine)

    print("\n✅ Pipeline concluído com sucesso.")
    print("   O Power BI pode consumir gold.feature_store_churn agora.")
