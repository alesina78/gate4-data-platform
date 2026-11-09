"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 6, Exercício 10                                 ║
║  Arquivo : ex10_dag_gate4_mensal.py                                          ║
║  Tema    : DAG completa da rotina mensal do GATE4                            ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
DAG de produção da rotina mensal do GATE4:
  1. Extrai dados do período (idempotente)
  2. Calcula PSI (drift do modelo de churn)
  3. Branch: drift alto → retreina challenger | drift ok → só avisa
  4. Envia alerta com resumo

ANALOGIA ORACLE
---------------
  DAG          = DBMS_SCHEDULER Chain (ou Job Pentaho/ODI)
  Task         = Passo do Chain (procedure, shell, SQL)
  >>           = Hop "só avança se OK"
  schedule     = cron do DBMS_SCHEDULER
  catchup=False= não reexecutar períodos passados automaticamente
  data_interval= o período que esta run processa (como :DATA_REF na procedure)
  XCom         = parâmetro de saída de uma procedure que entra na próxima
  Connections  = TNS Names / credenciais centralizadas (nunca senha no código)
  Backfill     = reprocessar uma data específica manualmente

COMO USAR
---------
  # 1. Coloque este arquivo em $AIRFLOW_HOME/dags/
  # 2. O Airflow detecta automaticamente em ~30 segundos
  # 3. Para testar manualmente:
  #    airflow dags trigger gate4_churn_mensal
  # 4. Para reprocessar um mês específico:
  #    airflow dags backfill gate4_churn_mensal --start-date 2026-10-01 --end-date 2026-11-01

INSTALAÇÃO LOCAL (Docker Compose)
----------------------------------
  # Cria o docker-compose do Airflow (versão oficial)
  curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
  mkdir -p ./dags ./logs ./plugins
  echo "AIRFLOW_UID=$(id -u)" > .env
  docker compose up airflow-init
  docker compose up -d
  # Acesse: http://localhost:8080  (admin / admin)
"""

from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES DO AIRFLOW
# Airflow 3.x: from airflow.sdk import dag, task
# Airflow 2.x: from airflow.decorators import dag, task
# Confira sua versão: airflow version
# ─────────────────────────────────────────────────────────────────────────────
try:
    from airflow.sdk import dag, task           # Airflow 3.x
except ImportError:
    from airflow.decorators import dag, task   # Airflow 2.x (fallback)


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA DAG
# @dag equivale a criar uma instância de DAG no estilo clássico:
#   with DAG("gate4_churn_mensal", schedule="0 6 1 * *", ...) as dag:
# ─────────────────────────────────────────────────────────────────────────────
@dag(
    dag_id="gate4_churn_mensal",

    # Cron: dia 1 de cada mês às 06:00
    # Mesmo formato do DBMS_SCHEDULER / crontab que você já usa
    # "0 6 1 * *" = minuto 0, hora 6, dia 1, qualquer mês, qualquer dia da semana
    schedule="0 6 1 * *",

    # Data de início — SEMPRE uma data fixa no passado, NUNCA datetime.now()
    # Se usar datetime.now() e catchup=True: centenas de runs disparadas!
    start_date=datetime(2026, 1, 1),

    # catchup=False: não reprocessar os meses passados automaticamente
    # Se True e start_date for 2026-01-01: 10 runs disparadas ao ativar a DAG
    catchup=False,

    # Configuração padrão para todas as tasks desta DAG
    default_args={
        "retries":      2,                       # tenta 2 vezes antes de falhar
        "retry_delay":  timedelta(minutes=5),    # aguarda 5 min entre tentativas
        "email_on_failure": False,               # configurar email separadamente
    },

    # Tags para filtrar na UI do Airflow
    tags=["gate4", "ml", "churn", "mensal"],

    # Descrição aparece na UI
    description="Rotina mensal: extrai dados, calcula drift do modelo de churn "
                "e retreina o challenger se necessário.",
)
def pipeline_mensal():
    """
    DAG da rotina mensal do GATE4.

    Fluxo:
        extrair → calcular_drift → decidir (branch)
                                        ├── treinar_challenger → avisar
                                        └── avisar
    """

    # ─────────────────────────────────────────────────────────────────────────
    # TASK 1 — EXTRAIR
    # Extrai os dados do período da run para a camada staging
    # ─────────────────────────────────────────────────────────────────────────
    @task(task_id="extrair")
    def extrair(data_interval_start=None, data_interval_end=None) -> str:
        """
        Extrai dados do Postgres para Parquet na camada staging.

        IDEMPOTENTE: sobrescreve o arquivo do período.
        Rodar 2x para novembro/2026 sempre gera o mesmo resultado.

        Args:
            data_interval_start: início do período desta run (injetado pelo Airflow)
            data_interval_end:   fim do período desta run

        Returns:
            str: caminho do arquivo Parquet gerado (passado via XCom para a próxima task)

        Analogia Oracle:
            DELETE FROM staging.abt_churn WHERE mes_ref = :inicio;
            INSERT INTO staging.abt_churn SELECT ... WHERE data BETWEEN :inicio AND :fim;
        """
        # NUNCA use datetime.now() aqui!
        # Se reprocessar janeiro em março, data_interval_start ainda será janeiro.
        mes_ref = data_interval_start.strftime("%Y-%m")
        print(f"[extrair] Período: {data_interval_start.date()} → {data_interval_end.date()}")

        # Em produção: substitua por conexão real ao Postgres
        # from airflow.hooks.postgres_hook import PostgresHook
        # hook = PostgresHook(postgres_conn_id="gate4_prod")  # credencial na UI, não no código
        # df = hook.get_pandas_df("SELECT * FROM faturas WHERE mes_ref = %s", parameters=(mes_ref,))

        # Simulação: gera dados fictícios
        import pandas as pd
        import numpy as np
        rng = np.random.default_rng(seed=42)
        df = pd.DataFrame({
            "aluno_id":           range(1, 151),
            "mes_ref":            mes_ref,
            "frequencia_mensal":  rng.integers(0, 20, 150),
            "dias_atraso":        rng.exponential(5, 150).round(0),
        })

        # Idempotência: sobrescreve o arquivo se já existir
        import os
        os.makedirs("data/staging", exist_ok=True)
        caminho = f"data/staging/abt_churn_{mes_ref}.parquet"
        df.to_parquet(caminho, index=False)

        print(f"[extrair] {len(df)} registros salvos em: {caminho}")

        # Retorno vai para o XCom — a próxima task recebe este valor
        # XCom: apenas valores pequenos (string, número, dict)
        # Dados grandes ficam no arquivo; a task passa só o caminho
        return caminho

    # ─────────────────────────────────────────────────────────────────────────
    # TASK 2 — CALCULAR DRIFT (PSI)
    # Mede se a distribuição dos dados mudou desde o treino do modelo
    # ─────────────────────────────────────────────────────────────────────────
    @task(task_id="calcular_drift")
    def calcular_drift(caminho_staging: str) -> dict:
        """
        Calcula o PSI (Population Stability Index) do modelo de churn.

        PSI < 0.10  → distribuição estável (modelo OK)
        PSI 0.10–0.25 → mudança moderada (monitorar)
        PSI > 0.25  → drift alto (considerar retreino)

        Args:
            caminho_staging: caminho do Parquet gerado pela task extrair (via XCom)

        Returns:
            dict: resultado do drift para a task branch (via XCom)
        """
        import pandas as pd
        import numpy as np

        df = pd.read_parquet(caminho_staging)
        mes_ref = df["mes_ref"].iloc[0]

        print(f"[calcular_drift] Calculando PSI para: {mes_ref}")
        print(f"[calcular_drift] {len(df)} registros lidos de: {caminho_staging}")

        # Em produção: compare com a distribuição de referência (data de treino)
        # Simulação: PSI calculado sobre frequencia_mensal
        rng = np.random.default_rng(seed=0)   # distribuição de referência (treino)
        ref = rng.integers(0, 20, 500)
        cur = df["frequencia_mensal"].values

        # PSI = SUM[(atual% - ref%) * ln(atual% / ref%)] por bin
        bins = np.linspace(0, 20, 11)
        ref_pct = np.histogram(ref, bins=bins)[0] / len(ref) + 1e-6
        cur_pct = np.histogram(cur, bins=bins)[0] / len(cur) + 1e-6
        psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))

        resultado = {
            "mes_ref":  mes_ref,
            "psi_max":  round(psi, 4),
            "status":   "ALTO" if psi > 0.25 else ("MODERADO" if psi > 0.10 else "OK"),
        }
        print(f"[calcular_drift] PSI = {psi:.4f} → status: {resultado['status']}")
        return resultado   # → XCom para a task branch

    # ─────────────────────────────────────────────────────────────────────────
    # TASK 3 — DECIDIR (BRANCH)
    # Escolhe o caminho com base no PSI calculado
    # ─────────────────────────────────────────────────────────────────────────
    @task.branch(task_id="decidir")
    def decidir(resultado: dict) -> str:
        """
        Branch: decide qual task executar a seguir com base no PSI.

        Analogia Oracle:
            IF psi_max > 0.25 THEN
                retreinar_challenger;
            ELSE
                avisar_time;
            END IF;

        Returns:
            str: task_id da próxima task a executar
        """
        psi = resultado["psi_max"]
        print(f"[decidir] PSI recebido: {psi} | Limite: 0.25")

        if psi > 0.25:
            print("[decidir] 🔴 Drift ALTO → branch: treinar_challenger")
            return "treinar_challenger"   # task_id da próxima task
        else:
            print("[decidir] 🟢 Modelo OK → branch: avisar")
            return "avisar"

    # ─────────────────────────────────────────────────────────────────────────
    # TASK 4 — TREINAR CHALLENGER (só se PSI > 0.25)
    # ─────────────────────────────────────────────────────────────────────────
    @task(task_id="treinar_challenger")
    def treinar_challenger():
        """
        Treina um novo modelo challenger e registra no MLflow.

        A PROMOÇÃO para produção é MANUAL — um humano decide se o challenger
        é melhor que o campeão antes de substituir.

        Em produção: chama src/gate4/g18_guia1_churn.py via subprocess
        ou importa a função de treino diretamente.
        """
        print("[treinar_challenger] 🌲 Iniciando treino do challenger...")
        print("[treinar_challenger] Carregando ABT histórica...")
        print("[treinar_challenger] Treinando HistGradientBoostingClassifier...")
        print("[treinar_challenger] ROC-AUC challenger: 0.847")
        print("[treinar_challenger] Registrando no MLflow como 'churn-challenger-v2'...")
        print("[treinar_challenger] ✅ Challenger registrado. Aguarda aprovação manual.")

    # ─────────────────────────────────────────────────────────────────────────
    # TASK 5 — AVISAR
    # Sempre roda — independente do caminho tomado pelo branch
    # ─────────────────────────────────────────────────────────────────────────
    @task(
        task_id="avisar",
        # trigger_rule: roda mesmo quando treinar_challenger foi pulada pelo branch
        # Sem isso, avisar ficaria em "skipped" se o branch não tomou o caminho do treino
        # "none_failed_min_one_success" = roda se nenhuma upstream falhou e pelo menos uma teve sucesso
        trigger_rule="none_failed_min_one_success",
    )
    def avisar():
        """
        Envia resumo da rotina mensal para o time via Telegram/Slack.

        Em produção: use TelegramOperator ou SlackWebhookOperator,
        ou chame a API via requests com a credencial no Connections do Airflow.

        Sem retries: se a task de notificação falhar, não queremos
        mandar a mesma mensagem duas vezes.
        """
        print("[avisar] 📱 Enviando resumo para o time...")
        print("[avisar] Mensagem: 'Rotina mensal GATE4 concluída. Verifique o relatório.'")
        print("[avisar] ✅ Notificação enviada.")

    # ─────────────────────────────────────────────────────────────────────────
    # DEPENDÊNCIAS — GRAFO DA DAG
    # Define a ordem de execução com o operador >>
    # Analogia Oracle: a ordem dos passos no DBMS_SCHEDULER Chain
    # ─────────────────────────────────────────────────────────────────────────
    # Instancia as tasks (cada chamada cria um nó no grafo)
    caminho  = extrair()                    # task 1 → retorna caminho via XCom
    drift    = calcular_drift(caminho)      # task 2 → recebe caminho, retorna dict
    decisao  = decidir(drift)              # task 3 → recebe dict, retorna task_id

    # Branch: dois caminhos possíveis
    # Caminho 1 (PSI alto):  decidir → treinar_challenger → avisar
    # Caminho 2 (PSI ok):    decidir → avisar
    decisao >> treinar_challenger() >> avisar()
    decisao >> avisar()


# Instancia a DAG — OBRIGATÓRIO no final do arquivo
# O Airflow importa este módulo e procura por objetos DAG no namespace global
pipeline_mensal()
