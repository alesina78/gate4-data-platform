# 🛠️ Guia 6 — Orquestração com Apache Airflow

> **Trilha:** B — Engenharia de Dados, MLOps & Nuvem · **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)

---

## 🎯 Objetivo

Orquestrar o pipeline mensal do GATE4 com Apache Airflow — definindo dependências,
retries, idempotência e branch com base no drift do modelo de churn.

---

## 📁 Arquivos

| Arquivo | Tema | Dificuldade |
|---|---|---|
| `ex10_dag_gate4_mensal.py` | DAG completa de produção — coloque em `$AIRFLOW_HOME/dags/` | ⭐⭐⭐ |
| `ex11_conceitos_airflow.py` | Conceitos sem Airflow instalado — roda localmente | ⭐⭐ |

---

## ▶️ Como rodar

```bash
# ex11: roda sem Airflow (demonstração dos conceitos)
source .venv/Scripts/activate
pip install pandas numpy
python ex11_conceitos_airflow.py

# ex10: requer Airflow instalado (via Docker Compose)
# Coloque o arquivo em $AIRFLOW_HOME/dags/
# airflow dags trigger gate4_churn_mensal
```

---

## 🐳 Instalar o Airflow localmente (Docker Compose)

```bash
# Airflow não roda nativamente no Windows — use WSL ou Docker
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
mkdir -p ./dags ./logs ./plugins
echo "AIRFLOW_UID=$(id -u)" > .env
docker compose up airflow-init
docker compose up -d
# Acesse: http://localhost:8080  (admin / admin)
# Copie ex10_dag_gate4_mensal.py para ./dags/
```

---

## 🔵 Analogias Oracle → Airflow

| Oracle / Pentaho / ODI | Apache Airflow |
|---|---|
| Job / Package / Chain | **DAG** (Directed Acyclic Graph) |
| Passo do job (SQL, shell) | **Task** (`@task`) |
| Hop "só avança se OK" | Operador `>>` |
| Agendamento cron | `schedule="0 6 1 * *"` |
| TNS Names / credenciais | **Connections** (UI do Airflow) |
| Reexecutar carga de uma data | **Backfill** / clear de uma run |
| Parâmetro OUT de procedure | **XCom** (retorno da task) |
| `IF/CASE` entre procedures | **@task.branch** |
| `DELETE + INSERT` por partição | Idempotência da task |

---

## ⚠️ As 6 Armadilhas — nunca faça isso

| ❌ Errado | ✅ Correto |
|---|---|
| `datetime.now()` na task | `data_interval_start` (parâmetro da run) |
| `start_date=datetime.now()` | `start_date=datetime(2026, 1, 1)` fixo |
| `catchup=True` sem querer | `catchup=False` por padrão |
| Senha no código | `PostgresHook(postgres_conn_id="gate4_prod")` |
| Query pesada no topo do arquivo | Imports e queries DENTRO das tasks |
| INSERT sem DELETE (duplica) | DELETE + INSERT por período ou MERGE |

---

## 🗺️ Trilha de estudos

```
Guia 18 — Projeto Pandas/NumPy          ✅ Concluído
Guia 1  — SQL → Pandas → ML             ✅ Concluído
Guia 2  — Séries Temporais              ✅ Concluído
Guia 3  — FastAPI + Docker              ✅ Concluído
Guia 6  — Apache Airflow                ✅ Este módulo
Guia 15 — Analytics Engineering (dbt)   🔜 Próximo
Guia 5  — PySpark + Databricks          ⬜ Planejado
Guia 14 — Cloud (AWS/Azure/GCP)         ⬜ Planejado
```
