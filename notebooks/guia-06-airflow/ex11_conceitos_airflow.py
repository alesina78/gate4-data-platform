"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 6, Exercício 11                                 ║
║  Arquivo : ex11_conceitos_airflow.py                                         ║
║  Tema    : Demonstração dos conceitos — idempotência, XCom, branch          ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Este script NÃO é uma DAG — é um arquivo Python puro que demonstra
os conceitos do Airflow sem precisar do Airflow instalado.

Execute localmente para entender:
  - Idempotência com DELETE+INSERT vs INSERT cego
  - Por que datetime.now() quebra o reprocessamento
  - Como o XCom funciona (passagem de dados entre tasks)
  - Como o branch decide o caminho

COMO RODAR
----------
  source .venv/Scripts/activate
  pip install pandas numpy
  python ex11_conceitos_airflow.py
"""

import pandas as pd
import numpy  as np
from datetime import datetime, date
from pathlib  import Path

print("=" * 65)
print("GATE4 — Exercício 11: Conceitos Airflow sem Airflow instalado")
print("=" * 65)


# ─────────────────────────────────────────────────────────────────────────────
# CONCEITO 1 — IDEMPOTÊNCIA
# Demonstra a diferença entre INSERT cego e DELETE + INSERT
# ─────────────────────────────────────────────────────────────────────────────
print("\n📌 CONCEITO 1 — Idempotência")
print("─" * 65)
print("Pergunta: o que acontece se a task rodar 2 vezes para o mesmo período?")

# Simula uma tabela gold (DataFrame em memória)
gold_fat = pd.DataFrame(columns=["mes_ref", "empresa_id", "faturamento"])

def task_carregar_INSERT_CEGO(mes_ref: str, gold: pd.DataFrame) -> pd.DataFrame:
    """❌ Não idempotente — duplica ao rodar 2x."""
    novos = pd.DataFrame({
        "mes_ref":      [mes_ref] * 3,
        "empresa_id":   [1, 2, 3],
        "faturamento":  [10000, 15000, 8000],
    })
    # INSERT sem DELETE — acumula duplicatas!
    return pd.concat([gold, novos], ignore_index=True)

def task_carregar_DELETE_INSERT(mes_ref: str, gold: pd.DataFrame) -> pd.DataFrame:
    """✅ Idempotente — DELETE + INSERT por período."""
    # DELETE do período (Analogia Oracle: DELETE FROM gold.fat WHERE mes_ref = :mes)
    gold = gold[gold["mes_ref"] != mes_ref].copy()
    # INSERT apenas os dados do período
    novos = pd.DataFrame({
        "mes_ref":      [mes_ref] * 3,
        "empresa_id":   [1, 2, 3],
        "faturamento":  [10000, 15000, 8000],
    })
    return pd.concat([gold, novos], ignore_index=True)

# Simula 3 execuções para o mesmo período (como um reprocessamento)
mes = "2026-11"
gold_cego = pd.DataFrame(columns=["mes_ref", "empresa_id", "faturamento"])
gold_idem = pd.DataFrame(columns=["mes_ref", "empresa_id", "faturamento"])

for run in range(1, 4):
    gold_cego = task_carregar_INSERT_CEGO(mes, gold_cego)
    gold_idem = task_carregar_DELETE_INSERT(mes, gold_idem)

print(f"\n  Após 3 execuções para '{mes}':")
print(f"  INSERT cego          : {len(gold_cego)} linhas  ❌ (esperado: 3)")
print(f"  DELETE + INSERT      : {len(gold_idem)} linhas  ✅ (correto)")
print(f"\n  → DELETE + INSERT garante idempotência.")
print(f"    Analogia Oracle: DELETE + INSERT por partição de data, igual ao seu ETL.")


# ─────────────────────────────────────────────────────────────────────────────
# CONCEITO 2 — data_interval vs datetime.now()
# ─────────────────────────────────────────────────────────────────────────────
print("\n📌 CONCEITO 2 — data_interval vs datetime.now()")
print("─" * 65)

# Simula uma run de reprocessamento disparada em novembro/2026
# para processar os dados de janeiro/2026
data_interval_start = datetime(2026, 1, 1)   # período da run (fixo)
hoje = datetime(2026, 11, 9)                  # data em que a run está rodando

print(f"  Run criada para processar: {data_interval_start.strftime('%B/%Y')}")
print(f"  Data em que está rodando:  {hoje.strftime('%B/%Y')}")
print()

# Task errada
mes_errado = hoje.month
print(f"  ❌ datetime.now().month     → extrai dados de: mês {mes_errado} (novembro!)")
print(f"     O reprocessamento de janeiro carregaria dados de novembro.")

# Task correta
mes_certo = data_interval_start.month
print(f"  ✅ data_interval_start.month → extrai dados de: mês {mes_certo:02d} (janeiro ✓)")
print(f"     O reprocessamento de janeiro carrega os dados corretos.")


# ─────────────────────────────────────────────────────────────────────────────
# CONCEITO 3 — XCom (passagem de dados entre tasks)
# ─────────────────────────────────────────────────────────────────────────────
print("\n📌 CONCEITO 3 — XCom: passagem de dados entre tasks")
print("─" * 65)
print("  Analogia Oracle: parâmetro de saída de uma procedure (OUT parameter)")
print()

# Simula o fluxo de XCom entre as 3 tasks principais
def simular_extrair(data_interval_start: datetime) -> str:
    """Retorna o caminho do arquivo — isso vai para o XCom."""
    mes = data_interval_start.strftime("%Y-%m")
    caminho = f"data/staging/abt_churn_{mes}.parquet"
    print(f"  [extrair] → XCom out: '{caminho}'")
    return caminho   # XCom: apenas o caminho, não o DataFrame inteiro!

def simular_calcular_drift(caminho: str) -> dict:
    """Recebe o caminho via XCom e retorna o resultado do drift."""
    print(f"  [calcular_drift] ← XCom in: '{caminho}'")
    resultado = {"mes_ref": "2026-01", "psi_max": 0.31, "status": "ALTO"}
    print(f"  [calcular_drift] → XCom out: {resultado}")
    return resultado   # dict pequeno — adequado para XCom

def simular_decidir(resultado: dict) -> str:
    """Recebe o resultado via XCom e decide o branch."""
    print(f"  [decidir] ← XCom in: {resultado}")
    branch = "treinar_challenger" if resultado["psi_max"] > 0.25 else "avisar"
    print(f"  [decidir] → Branch: '{branch}'")
    return branch

# Executa o fluxo
print("  Simulando o fluxo completo:")
caminho_xcom  = simular_extrair(datetime(2026, 1, 1))
drift_xcom    = simular_calcular_drift(caminho_xcom)
branch_xcom   = simular_decidir(drift_xcom)

print()
print("  ✅ XCom correto: cada task passa apenas valores pequenos")
print("     O DataFrame (potencialmente grande) fica no Parquet")
print("     A task passa só o caminho (string pequena)")


# ─────────────────────────────────────────────────────────────────────────────
# CONCEITO 4 — BRANCH com trigger_rule
# ─────────────────────────────────────────────────────────────────────────────
print("\n📌 CONCEITO 4 — Branch e trigger_rule")
print("─" * 65)

def simular_pipeline(psi: float):
    """Simula o grafo completo da DAG com diferentes valores de PSI."""
    print(f"\n  Simulando com PSI = {psi:.2f} (limite: 0.25)")

    tasks_executadas  = ["extrair", "calcular_drift", "decidir"]
    tasks_puladas     = []

    if psi > 0.25:
        tasks_executadas.append("treinar_challenger")
        print(f"  🔴 Branch → treinar_challenger")
    else:
        tasks_puladas.append("treinar_challenger")
        print(f"  🟢 Branch → pula treinar_challenger")

    # avisar sempre roda (trigger_rule="none_failed_min_one_success")
    tasks_executadas.append("avisar")
    print(f"  → avisar roda SEMPRE (trigger_rule garante isso)")

    print(f"  Executadas : {tasks_executadas}")
    if tasks_puladas:
        print(f"  Puladas    : {tasks_puladas}")

simular_pipeline(psi=0.31)   # drift alto
simular_pipeline(psi=0.18)   # drift ok


# ─────────────────────────────────────────────────────────────────────────────
# RESUMO DAS REGRAS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("📋 RESUMO — 6 Regras do Airflow para não esquecer")
print("=" * 65)
regras = [
    ("1", "NUNCA use datetime.now() em tasks",
           "→ use data_interval_start para reprocessamento correto"),
    ("2", "catchup=False por padrão",
           "→ evita centenas de runs inesperadas ao ativar a DAG"),
    ("3", "start_date fixo no passado",
           "→ nunca datetime(2024, 1, 1) se deployar em 2026 com catchup=True"),
    ("4", "XCom só para valores pequenos",
           "→ dados grandes ficam em arquivo/banco; a task passa só a referência"),
    ("5", "Nada pesado no topo do arquivo",
           "→ imports e queries ficam DENTRO das tasks, não no módulo"),
    ("6", "Idempotência com DELETE+INSERT ou MERGE",
           "→ rodar 2x para o mesmo período dá o mesmo resultado"),
]
for n, regra, detalhe in regras:
    print(f"\n  {n}. {regra}")
    print(f"     {detalhe}")

print("\n" + "=" * 65)
print("✅ Exercício 11 concluído!")
print("   Próximo: ex10_dag_gate4_mensal.py → coloque em $AIRFLOW_HOME/dags/")
print("=" * 65 + "\n")
