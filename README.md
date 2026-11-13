# 🐎 GATE4 Data Platform

> **Plataforma de Engenharia de Dados & Analytics** aplicada à gestão inteligente de centros equestres, ecoterapia e reabilitação.  
> Pipeline end-to-end: setup de ambiente → geração sintética → qualidade → limpeza → análise financeira/operacional → dbt Analytics Engineering → SQL Avançado → Estatística Aplicada → Machine Learning.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt-Core-FF694B?style=flat-square&logo=dbt&logoColor=white)](https://www.getdbt.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.x-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Pytest](https://img.shields.io/badge/Testes-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/alesina78/gate4-data-platform/actions)
[![Status](https://img.shields.io/badge/Status-Ativo-2ea44f?style=flat-square)]()

---

## 🎯 O Problema de Negócio

Centros equestres operam com dados fragmentados: controle de saúde animal em planilhas, faturamento em cadernos, frequência de alunos no WhatsApp. O resultado é **inadimplência invisível, cavalos sobrecarregados e churn de alunos que ninguém antecipou**.

Este projeto constrói a **espinha dorsal analítica** do GATE4 — plataforma SaaS multi-tenant para gestão de haras e hípicas — transformando 17 tabelas relacionais em inteligência acionável para o gestor do centro.

**Perguntas que o pipeline responde:**
- Qual instrutor está com maior taxa de cancelamento de aulas?
- Quais cavalos estão com carga de trabalho acima do Percentil 90?
- Quais alunos têm perfil de churn nos próximos 30 dias?
- Quais insumos entrarão em ruptura de estoque esta semana?
- Qual o aging de inadimplência por empresa e faixa de vencimento?

---

## 🏗️ Arquitetura do Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     GATE4 Data Platform                     │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│    M0    │    M1    │    M2    │  M3–M7   │   M8 / dbt      │
│ Gerador  │Qualidade │ Limpeza  │Analytics │ Analytics Eng.  │
│Sintético │          │          │          │ & Orquestração  │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│             Persistência em Parquet / Postgres DB           │
├─────────────────────────────────────────────────────────────┤
│         ML · Churn Prediction  (HistGradientBoosting)       │
└─────────────────────────────────────────────────────────────┘
```

**Modelo de dados:** 17 tabelas relacionais, arquitetura multi-empresa (multi-tenant), com chaves estrangeiras validadas em cada camada.

---

## 📦 Módulos de Produção

### Camada de Dados

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M0 · Gerador Sintético** | `src/gate4/g18_m0_gerador.py` | Geração relacional com `numpy.random` (Poisson/Lognormal) e injeção controlada de inconsistências |
| **M1 · Qualidade** | `src/gate4/g18_m1_qualidade.py` | Auditoria de integridade referencial, detecção de FKs órfãs e validação de nulos por criticidade |
| **M2 · Limpeza** | `src/gate4/g18_m2_limpeza.py` | Normalização de textos via Regex, conversão segura de tipos (`Int64`, `datetime`) e log de transformações |

### Camada Analítica, Analytics Engineering & Orquestração

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M3 · Financeiro** | `src/gate4/g18_m3_financeiro.py` | Faturamento mensal, inadimplência, aging de faturas com datas dinâmicas e auditoria contábil |
| **M4 · Operação** | `src/gate4/g18_m4_operacao.py` | Taxa de conclusão de aulas por instrutor e sobrecarga de cavalos via Percentil 90 |
| **M5 · Manejo** | `src/gate4/g18_m5_manejo.py` | Auditoria de prazos de vacinas, vermífugos, ferrageamentos e casqueamentos por empresa |
| **M6 · Estoque** | `src/gate4/g18_m6_estoque.py` | Dias de cobertura de insumos, prevenção de divisão por zero e alertas de ruptura |
| **M7 · Alunos & RFM** | `src/gate4/g18_m7_alunos.py` | Alunos em risco de churn (>60 dias sem frequência) e métricas RFM |
| **Power BI & MLOps** | `notebooks/guia-12-power-bi/` | Dashboards Power BI, MLOps, Feature Store e DAGs Airflow para orquestração |
| **dbt Analytics** | `notebooks/guia-15-dbt-analytics/` | Modelagem dbt (staging, marts, incremental), testes de integridade e testes singulares em SQL |
| **SQL Avançado** | `notebooks/guia-13-sql-entrevistas/` | 8 Padrões SQL avançados (Oracle vs PostgreSQL), tuning de queries, janelas analíticas e simulador |

### Camada de Orquestração & ML

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M8 · Pipeline** | `src/gate4/g18_pipeline.py` | Orquestração sequencial M0→M7 com persistência em Parquet (raw → staging → gold) |
| **ML · Churn** | `src/gate4/g18_guia1_churn.py` | Modelo preditivo de evasão — ABT, pipeline Scikit-Learn, ROC-AUC e Lift Operacional |

---

## 🔬 Laboratórios Práticos & Benchmarks

Além do pipeline principal, a pasta `scripts/` e a pasta `notebooks/` abrigam suítes avançadas de validação estatística, modelagem dbt, laboratório de ER do GATE4 e SQL avançado para entrevistas:

| Script / Guia | Foco & Descrição |
|---|---|
| `scripts/g10_churn_project.py` | Protótipo inicial do modelo de churn (versão anterior ao pipeline de produção) |
| `scripts/g16_performance.py` | Benchmarks: vetorização vs loop, otimização de memória, Parquet vs CSV, DuckDB |
| `scripts/generators_G18_1.py` | Gerador auxiliar usado durante o desenvolvimento do M0 |
| `notebooks/guia-19-setup-vscode/` | **Guia 19:** Passo a passo interativo de setup do ambiente (VS Code, Python, venv, pytest, Git) |
| `notebooks/guia-18-projeto-pandas-numpy/` | **Guias 18A, 18B, 18C:** Exploração do ER real (17 tabelas), laboratório de dados sintéticos (M0) e plano de projeto |
| `notebooks/guia-12-power-bi/` | **Guia 12:** Dashboards Power BI, modelagem de dimensões, Feature Store (MLOps) e DAGs Airflow |
| `notebooks/guia-13-sql-entrevistas/` | **Guia 13:** 8 padrões SQL de entrevistas (Top-N, Gaps & Islands, Coorte, NOT EXISTS vs NOT IN) |
| `notebooks/guia-15-dbt-analytics/` | **Guia 15:** Projeto dbt Core com camada de staging, marts, testes schema e singulares |

---

## 🤖 Machine Learning — Previsão de Churn

**Construção da ABT (Analytical Base Table)**
- Variáveis comportamentais (frequência, cancelamentos, intervalo desde última aula) e financeiras (inadimplência, ticket médio)
- Data de corte dinâmica — features usam **apenas dados do passado** *(zero data leakage)*

**Modelo & Validação**
- `HistGradientBoostingClassifier` — robusto a nulos, sem imputação manual
- Pipeline Scikit-Learn com validação cruzada temporal (`TimeSeriesSplit`)

**Métricas de Impacto de Negócio**
- **ROC-AUC** — discriminação técnica do modelo
- **Lift Operacional** — eficiência da campanha direcionada vs. contatos aleatórios

**Artefato treinado:** `modelos/modelo_churn_gate4.joblib`

---

## 📊 Visualizações Geradas

O pipeline produz automaticamente 7 gráficos salvos em `saidas/`:

| Arquivo | Visualização |
|---|---|
| `01_hist_dias_atraso.png` | Distribuição de dias de atraso nas faturas |
| `02_boxplot_mensalidade_plano.png` | Mensalidade por plano contratado |
| `03_barras_atraso_plano.png` | Inadimplência por tipo de plano |
| `04_dispersao_aulas_atraso.png` | Correlação entre frequência e atraso |
| `05_mapa_correlacao.png` | Mapa de calor das correlações |
| `06_matriz_confusao.png` | Desempenho do modelo de churn |
| `07_curva_precision_recall.png` | Trade-off precisão × recall |

---

## 📚 Trilha de Estudos

Jornada de transição de **Oracle/PL-SQL Sênior → Engenharia de Dados & Analytics**, documentada com scripts comentados linha a linha no padrão **SQL → Pandas**:

| Pasta | Guia | Tema | Status |
|---|---|---|---|
| `notebooks/guia-19-setup-vscode/` | Guia 19 | Setup Passo a Passo: VS Code, Python, venv, pytest e Git | ✅ Concluído |
| `notebooks/guia-18-projeto-pandas-numpy/` | Guia 18 | Laboratório ER GATE4 (18A), Gerador Sintético (18B) e Plano M0–M8 (18C) | ✅ Concluído |
| `notebooks/guia-01-sql-pandas-ml/` | Guia 1 | SQL → Pandas → ML: EDA, NumPy e visualizações | ✅ Concluído |
| `notebooks/guia-02-series-temporais/` | Guia 2 | Séries Temporais, resample, rolling e leakage temporal | ✅ Concluído |
| `notebooks/guia-03-fastapi-docker/` | Guia 3 | FastAPI + Docker: API de risco de churn em container | ✅ Concluído |
| `notebooks/guia-06-airflow/` | Guia 6 | Orquestração de workflows com Apache Airflow | ✅ Concluído |
| `notebooks/guia-12-power-bi/` | Guia 12 | Power BI, MLOps, Feature Store e DAG Airflow | ✅ Concluído |
| `notebooks/guia-13-sql-entrevistas/` | Guia 13 | SQL Avançado para Entrevistas (8 Padrões Oracle/PG, Tuning) | ✅ Concluído |
| `notebooks/guia-15-dbt-analytics/` | Guia 15 | Analytics Engineering com dbt (Staging, Marts, Testes) | ✅ Concluído |

---

## 🧪 Testes Automatizados

Suíte completa de testes unitários e de integração com `pytest`, cobrindo todos os módulos do pipeline:

| Arquivo | Cobertura |
|---|---|
| `tests/test_g18_m3_financeiro.py` | Módulo financeiro — faturamento e aging |
| `tests/test_g18_m4_m5_manejo.py` | Operação e manejo animal |
| `tests/test_g18_m6_m7_estoque_alunos.py` | Estoque, RFM e early warning de churn |
| `tests/test_g18_pipeline.py` | Integração end-to-end do pipeline completo |
| `tests/test_smoke_basico.py` | Sanidade e fumaça básicos |
| `tests/test_smoke.py` | Fumaça estrutural do projeto |

```bash
pip install -r requirements.txt
pytest -v
```

---

## ▶️ Como Executar

```bash
git clone https://github.com/alesina78/gate4-data-platform.git
cd gate4-data-platform

python -m venv .venv
source .venv/Scripts/activate    # Git Bash / Windows

pip install -r requirements.txt

# Pipeline completo (M0 → M8)
python src/gate4/g18_pipeline.py

# Módulo individual
python src/gate4/g18_m3_financeiro.py
```

---

## 📁 Estrutura do Repositório

```
gate4-data-platform/
│
├── src/gate4/                             # Módulos de produção (M0–M8 + ML Churn)
│   ├── g18_m0_gerador.py
│   ├── g18_m1_qualidade.py
│   ├── g18_m2_limpeza.py
│   ├── g18_m3_financeiro.py
│   ├── g18_m4_operacao.py
│   ├── g18_m5_manejo.py
│   ├── g18_m6_estoque.py
│   ├── g18_m7_alunos.py
│   ├── g18_pipeline.py
│   └── g18_guia1_churn.py
│
├── notebooks/                             # Cadernos de estudo — trilha de transição
│   ├── guia-01-sql-pandas-ml/             # Guia 1: SQL → Pandas → ML
│   ├── guia-02-series-temporais/          # Guia 2: Séries temporais, rolling, leakage
│   ├── guia-03-fastapi-docker/            # Guia 3: FastAPI + Docker
│   ├── guia-06-airflow/                   # Guia 6: Orquestração com Apache Airflow
│   ├── guia-12-power-bi/                  # Guia 12: Power BI, MLOps, Feature Store e Airflow
│   │   ├── 01_dim_data.sql
│   │   ├── 02_feature_store.py
│   │   ├── 03_dax_medidas
│   │   ├── 04_pipeline_airflow.py
│   │   ├── gitignore
│   │   ├── README.md
│   │   └── requirements.txt
│   ├── guia-13-sql-entrevistas/           # Guia 13: SQL Avançado (8 Padrões Oracle/PG, Tuning)
│   ├── guia-15-dbt-analytics/             # Guia 15: dbt Analytics Engineering (Staging, Marts, Testes)
│   ├── guia-18-projeto-pandas-numpy/      # Guia 18 (18A/18B/18C): ER real, gerador M0 e plano M0–M8
│   └── guia-19-setup-vscode/              # Guia 19: Setup interativo de ambiente e Git
│
├── scripts/                               # Utilitários, protótipos e benchmarks
│   ├── g10_churn_project.py
│   ├── g16_performance.py
│   ├── generators_G18_1.py
│   └── README.md
│
├── modelos/                               # Artefatos serializados (.joblib)
│   ├── churn_v1.joblib
│   └── modelo_churn_gate4.joblib
│
├── docs/                                  # Documentação e anotações técnicas
│   ├── Anotacoes.sql
│   ├── ARQUITETURA.md
│   └── DIAGNOSTICO_GATE4.md
│
├── saidas/                                # Visualizações PNG geradas pelo pipeline
│   ├── 01_hist_dias_atraso.png
│   ├── 02_boxplot_mensalidade_plano.png
│   ├── 03_barras_atraso_plano.png
│   ├── 04_dispersao_aulas_atraso.png
│   ├── 05_mapa_correlacao.png
│   ├── 06_matriz_confusao.png
│   └── 07_curva_precision_recall.png
│
├── tests/                                 # Suíte pytest (unitários + integração)
│   ├── test_g18_m3_financeiro.py
│   ├── test_g18_m4_m5_manejo.py
│   ├── test_g18_m6_m7_estoque_alunos.py
│   ├── test_g18_pipeline.py
│   ├── test_smoke_basico.py
│   └── test_smoke.py
│
├── .github/workflows/python-tests.yml     # CI — executa pytest a cada push
├── pyproject.toml
└── README.md
```

### 📂 Detalhamento do Guia 12 (`notebooks/guia-12-power-bi/`)

A pasta do Guia 12 integra a camada de visualização, MLOps e orquestração do ecossistema GATE4 com os seguintes componentes:

| Arquivo | Descrição / Responsabilidade |
|---|---|
| `01_dim_data.sql` | Scripts SQL para criação e população da dimensão de tempo/data de suporte analítico. |
| `02_feature_store.py` | Extração e persistência de features para o pipeline de Machine Learning (MLOps). |
| `03_dax_medidas` | Fórmulas e medidas DAX avançadas estruturadas para os dashboards do Power BI. |
| `04_pipeline_airflow.py` | DAG do Apache Airflow para orquestração automatizada do fluxo de dados. |
| `requirements.txt` | Dependências e bibliotecas Python específicas necessárias para rodar os scripts do guia. |
| `README.md` | Documentação e guia de instruções dedicado ao laboratório do Power BI e MLOps. |

---

## 👤 Autor

**Alessandro Giordano**  
Senior Data Engineer & Analytics Specialist | 25+ anos em TI Corporativa

[![LinkedIn](https://img.shields.io/badge/LinkedIn-alessandrolesina-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/alessandrolesina/)
[![GitHub](https://img.shields.io/badge/GitHub-alesina78-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/alesina78)
[![Email](https://img.shields.io/badge/Email-giordano.dba%40gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:giordano.dba@gmail.com)

> *Arquiteto do GATE4 — plataforma SaaS multi-tenant para gestão de centros equestres, desenvolvida do zero com Django, PostgreSQL e OCI.*

---

*Dados 100% sintéticos, gerados pelo módulo M0 para fins de estudo e demonstração de pipeline.*