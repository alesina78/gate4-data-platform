"""
GATE4 Data Platform · Guia 12
Arquivo : 04_pipeline_airflow.py
Propósito: DAG Airflow do pipeline diário de dados GATE4

Analogia Oracle / ODI:
    Este DAG equivale a um Plano de Carga ODI com steps dependentes:
    - Cada 'task' é uma Interface ODI ou um Procedure PL/SQL
    - A dependência t1 >> t2 >> t3 equivale ao "On Success → próximo passo"
    - O schedule_interval é o trigger do Agent ODI (06:00 todo dia)
    - O retry é equivalente ao ON_ERROR → retry no ODI

Diferenças chave vs ODI/PL-SQL:
    - Airflow é open-source, Python nativo, cloud-ready
    - Cada task pode ser monitorada individualmente (UI web)
    - Suporta backfill (re-executar datas passadas) automaticamente
    - É o padrão de mercado para pipelines de dados hoje

Como executar localmente:
    # Requer Docker ou Airflow instalado
    airflow dags test gate4_daily 2024-01-15
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago


# ── CONFIGURAÇÕES PADRÃO ──────────────────────────────────────────────────────
# Analogia Oracle: equivale aos parâmetros globais de um Package PL/SQL

DEFAULT_ARGS = {
    "owner"           : "alesina78",
    "depends_on_past" : False,         # não espera o run anterior terminar
    "email"           : ["alerta@gate4.com.br"],
    "email_on_failure": True,
    "email_on_retry"  : False,
    "retries"         : 2,             # tenta 2x antes de falhar
    "retry_delay"     : timedelta(minutes=5),
}


# ── FUNÇÕES DE CADA TASK ──────────────────────────────────────────────────────
# Em produção: cada função estaria num módulo separado (ex: gate4/tasks/extract.py)

def extract_incremental(**context) -> dict:
    """
    Lê só as linhas novas do PostgreSQL desde a última execução.

    Analogia Oracle/ODI:
        Equivale a um CDC (Change Data Capture) por updated_at.
        No ODI seria: WHERE updated_at > TO_DATE(:LAST_RUN, 'YYYY-MM-DD')

    XCom: retorna a contagem de linhas para a task de qualidade checar depois.
    """
    exec_date = context["execution_date"].date()
    yesterday = exec_date - timedelta(days=1)

    print(f"📥 Extraindo linhas com updated_at >= {yesterday}")

    # Em produção: usar SQLAlchemy + pd.read_sql
    # linhas = engine.execute(f"SELECT ... WHERE updated_at >= '{yesterday}'")

    # Simular contagem para o exemplo
    contagens = {
        "faturas" : 142,
        "aulas"   : 387,
        "alunos"  : 5,
        "ocupacao": 96,
    }

    print(f"✅ Extração concluída: {contagens}")

    # XCom: passa os dados para a próxima task via Airflow XCom
    # (equivale a uma variável de pacote PL/SQL compartilhada entre procedures)
    context["ti"].xcom_push(key="contagens_extracao", value=contagens)

    return contagens


def run_dbt_models(**context) -> None:
    """
    Executa os modelos dbt para transformar bronze → silver → gold.

    Analogia Oracle/ODI:
        dbt run = executa todos os INSERTs/MERGEs das tabelas DW em sequência.
        dbt test = executa os constraints e assertions (como NOT NULL, UNIQUE).

    Em produção usar o operador BashOperator:
        BashOperator(bash_command="dbt run --select tag:daily --profiles-dir /opt/dbt")
    """
    print("⚙️ Executando modelos dbt...")
    print("   dbt run --select tag:daily")
    print("   dbt test --select tag:daily")

    # Modelos executados (na ordem de dependência):
    modelos = [
        "staging.stg_faturas",
        "staging.stg_aulas",
        "gold.fato_faturas",
        "gold.fato_aulas",
        "gold.fato_ocupacao",
    ]
    for modelo in modelos:
        print(f"   ✅ {modelo}")


def run_inference(**context) -> None:
    """
    Carrega o modelo de churn versionado e grava gold.risco_churn.

    Analogia Oracle:
        Equivale a executar um Package PL/SQL de scoring que calcula
        probabilidades e faz INSERT ... ON CONFLICT DO UPDATE.

    Boas práticas MLOps:
        - Sempre carregar o modelo por versão (nunca o "último")
        - Gravar a versão usada na coluna versao_modelo
        - Monitorar data drift (se a distribuição mudou, retreinar)
    """
    print("🤖 Executando inferência de churn...")

    # Em produção:
    # modelo = mlflow.sklearn.load_model("models:/gate4_churn/Production")
    # features = pd.read_sql("SELECT * FROM gold.feature_store_churn WHERE data_ref = TODAY")
    # predicoes = modelo.predict_proba(features)
    # gravar_gold(predicoes)

    print("   Modelo: v2.1-lgbm (AUC-ROC: 0.84)")
    print("   Alunos scored: 1.247")
    print("   ✅ Gravado em gold.risco_churn")


def run_quality_checks(**context) -> None:
    """
    Verificações de qualidade pós-carga.

    Analogia Oracle:
        Equivale ao bloco de validação no final de um Procedure ETL:
        IF qtd_linhas < qtd_esperado THEN RAISE_APPLICATION_ERROR(...)

    Checks executados:
        1. Contagem mínima de linhas (evitar carga vazia)
        2. Nulos em colunas críticas
        3. Valores fora do range esperado
        4. Consistência entre tabelas (fato_faturas.aluno_id existe em dim_aluno)
    """
    exec_date = context["execution_date"].date()

    print(f"🔍 Executando quality checks para {exec_date}...")

    # Recuperar contagens da task de extração via XCom
    contagens = context["ti"].xcom_pull(
        task_ids="extract_incremental",
        key="contagens_extracao"
    )

    checks = [
        ("Faturas carregadas > 0",          contagens.get("faturas", 0) > 0),
        ("Aulas carregadas > 0",            contagens.get("aulas", 0) > 0),
        ("gold.risco_churn sem nulos",      True),   # simulado
        ("Alunos em risco_churn em dim_aluno", True),  # simulado
    ]

    falhas = []
    for descricao, resultado in checks:
        status = "✅" if resultado else "❌"
        print(f"   {status} {descricao}")
        if not resultado:
            falhas.append(descricao)

    if falhas:
        raise ValueError(f"Quality checks falharam: {falhas}")

    print(f"\n✅ Todos os quality checks passaram para {exec_date}")


def notify_success(**context) -> None:
    """Notificação de sucesso — em produção: Slack, email ou PagerDuty."""
    exec_date = context["execution_date"].date()
    print(f"📢 Pipeline gate4_daily concluído com sucesso para {exec_date}")
    # slack_hook.send(f"✅ GATE4 Daily Pipeline — {exec_date} OK")


# ── DEFINIÇÃO DO DAG ──────────────────────────────────────────────────────────

with DAG(
    dag_id="gate4_daily",
    description="Pipeline diário GATE4: extração incremental → dbt → ML → quality checks",
    schedule_interval="0 6 * * *",   # 06:00 todo dia (cron: min hora * * *)
    start_date=days_ago(1),
    catchup=False,                   # não re-executa datas passadas ao ligar
    default_args=DEFAULT_ARGS,
    tags=["gate4", "daily", "data-platform"],
    doc_md="""
    ## GATE4 Daily Pipeline

    Orquestra a carga incremental do Data Warehouse GATE4.

    **Ordem de execução:**
    1. `extract_incremental` → lê novos registros do PostgreSQL
    2. `run_dbt_models`       → transforma bronze → silver → gold
    3. `run_inference`        → scoring de churn + EOQ
    4. `run_quality_checks`   → valida contagens e nulos
    5. `notify_success`       → notifica equipe

    **SLA:** deve terminar antes das 08:00 (janela de 2 horas).
    **On-call:** alesina78
    """
) as dag:

    # ── Sentinela de início (boa prática: documenta o ponto de entrada) ──────
    inicio = EmptyOperator(task_id="inicio")

    # ── Tasks ────────────────────────────────────────────────────────────────
    t_extract = PythonOperator(
        task_id="extract_incremental",
        python_callable=extract_incremental,
    )

    t_dbt = PythonOperator(
        task_id="run_dbt_models",
        python_callable=run_dbt_models,
    )

    t_inference = PythonOperator(
        task_id="run_inference",
        python_callable=run_inference,
    )

    t_quality = PythonOperator(
        task_id="run_quality_checks",
        python_callable=run_quality_checks,
    )

    t_notify = PythonOperator(
        task_id="notify_success",
        python_callable=notify_success,
    )

    # ── Dependências (equivale ao fluxo de Interface ODI) ────────────────────
    # Analogia Oracle: "On Success → próximo step"
    inicio >> t_extract >> t_dbt >> t_inference >> t_quality >> t_notify
