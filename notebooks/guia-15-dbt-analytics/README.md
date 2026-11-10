# 🧱 Guia 15 — Analytics Engineering com dbt

> **Trilha:** B — Engenharia de Dados, MLOps & Nuvem · **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)

---

## 🎯 Objetivo

Organizar, testar e documentar as transformações SQL do GATE4 usando dbt —
o caminho mais curto do SQL sênior Oracle para o cargo de **Analytics Engineer**.

---

## 📁 Arquivos

| Arquivo | Tema | Dificuldade |
|---|---|---|
| `ex12_dbt_projeto_gate4.sql` | Todos os models SQL: staging + marts + incremental | ⭐⭐⭐ |
| `ex13_dbt_testes_schema.yml` | Testes genéricos e documentação (schema.yml) | ⭐⭐ |
| `ex14_dbt_testes_singulares.sql` | Testes singulares: reconciliação, validação de faixas | ⭐⭐⭐ |

---

## 🏗️ Estrutura do Projeto dbt GATE4

```
gate4_dbt/
│
├── models/
│   ├── sources.yml                     # tabelas cruas do GATE4
│   ├── staging/
│   │   ├── stg_alunos.sql             # view: limpa o cadastro de alunos
│   │   ├── stg_aulas.sql              # view: normaliza registro de aulas
│   │   ├── stg_faturas.sql            # view: tipa e calcula flags de atraso
│   │   └── schema.yml                 # testes: unique, not_null, relationships
│   └── marts/
│       ├── fct_faturamento_mensal.sql  # table: faturamento + inadimplência por mês
│       ├── fct_inadimplencia_por_modalidade.sql
│       ├── fct_abt_churn.sql          # incremental: ABT do modelo de churn (Guia 10)
│       ├── dim_aluno.sql              # table: dimensão para o Power BI (Guia 12)
│       └── schema.yml                 # testes dos marts
│
├── tests/                              # testes singulares (SQL customizado)
│   ├── assert_faturas_valor_positivo.sql
│   ├── assert_faturamento_reconciliado.sql
│   ├── assert_inadimplencia_percentual_valido.sql
│   ├── assert_churn_sem_data_futura.sql
│   └── assert_abt_churn_features_validas.sql
│
├── dbt_project.yml
└── profiles.yml   # ⚠️ FORA do Git — contém credenciais
```

---

## ▶️ Como instalar e rodar

```bash
# Instalar (requer Python)
pip install dbt-postgres

# Inicializar projeto
dbt init gate4_dbt
cd gate4_dbt

# Copie os arquivos dos exercícios para models/ e tests/
# Configure profiles.yml com as credenciais do seu Postgres GATE4

# Compilar (ver SQL gerado sem executar)
dbt compile

# Rodar models + testes
dbt build

# Rodar só um model e seus dependentes
dbt build --select stg_faturas+

# Gerar documentação
dbt docs generate && dbt docs serve
```

---

## 🔵 SQL Oracle → dbt

| Oracle / ODI | dbt |
|---|---|
| `CREATE OR REPLACE VIEW` | Model com `materialized='view'` (staging) |
| `CREATE TABLE AS SELECT` | Model com `materialized='table'` (marts) |
| `MERGE INTO` | Model com `materialized='incremental'` |
| Ordem manual de execução no ODI | `ref()` define o grafo automaticamente |
| `UNIQUE CONSTRAINT` | Teste `unique` no schema.yml |
| `NOT NULL CONSTRAINT` | Teste `not_null` no schema.yml |
| `FOREIGN KEY` | Teste `relationships` no schema.yml |
| `CHECK CONSTRAINT` com lista | Teste `accepted_values` |
| Query de auditoria | Teste singular em `tests/` |
| Wiki de documentação | `dbt docs generate` |

---

## ⚠️ Armadilhas — nunca faça isso

| ❌ Errado | ✅ Correto |
|---|---|
| Regras de negócio no Power BI E no SQL | Centralize no mart dbt |
| `SELECT *` nos marts | Selecione apenas as colunas necessárias |
| Zero testes | `dbt build` sem testes é só um agendador de views |
| Senha no `profiles.yml` commitado | `profiles.yml` no `.gitignore` + variável de ambiente |
| Model incremental sem `unique_key` | Declara `unique_key` e teste `unique` |
| `select schema.tabela` hardcoded | Use sempre `source()` ou `ref()` |

---

## 🗺️ Trilha de estudos

```
Guia 18 — Projeto Pandas/NumPy           ✅ Concluído
Guia 1  — SQL → Pandas → ML             ✅ Concluído
Guia 2  — Séries Temporais              ✅ Concluído
Guia 3  — FastAPI + Docker              ✅ Concluído
Guia 6  — Apache Airflow                ✅ Concluído
Guia 15 — Analytics Engineering (dbt)   ✅ Este módulo
Guia 5  — PySpark + Databricks          🔜 Próximo
Guia 14 — Cloud (AWS/Azure/GCP)         ⬜ Planejado
```
