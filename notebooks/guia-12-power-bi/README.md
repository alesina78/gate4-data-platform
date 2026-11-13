# 🐎 GATE4 Data Platform

> **Laboratório prático de Engenharia de Dados, Analytics e MLOps**  
> Plataforma SaaS real de gestão de haras/hípicas usada como caso de uso end-to-end.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql)](https://postgresql.org)
[![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-F2C811?logo=powerbi)](https://powerbi.microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 Problema de negócio

O GATE4 é uma plataforma SaaS para haras e clubes hípicos que gerencia alunos, cavalos,
aulas, baias, faturamento e ocupação. Com dezenas de clientes e milhares de registros
diários, surgem perguntas de negócio que só dados respondem:

- Quais alunos têm maior probabilidade de cancelar nos próximos 30 dias?
- Como está a ocupação de baias por período e quais estão gerando prejuízo?
- Qual é a inadimplência real por haras, modalidade e faixa de atraso?
- Qual o lote econômico de pedido de ração para cada tamanho de haras?

Este repositório documenta a jornada de construção de uma **plataforma de dados completa**
para responder essas perguntas — do banco transacional ao dashboard executivo.

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────────────────────────┐
│                        GATE4 Data Platform                           │
│                                                                      │
│  ┌─────────────┐    ┌──────────┐    ┌────────────┐    ┌──────────┐  │
│  │  Django /   │───▶│ Airflow  │───▶│  dbt (DW)  │───▶│ Power BI │  │
│  │ PostgreSQL  │    │  DAGs    │    │  Star Sch. │    │ Dashboard│  │
│  └─────────────┘    └──────────┘    └────────────┘    └──────────┘  │
│         │                │                │                          │
│         │                ▼                ▼                          │
│         │          ┌──────────┐    ┌────────────┐                   │
│         └─────────▶│ Feature  │───▶│  ML Models │                   │
│                    │  Store   │    │ (Churn/EOQ)│                   │
│                    └──────────┘    └────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

**Camadas do Data Warehouse (Medallion Architecture):**

| Camada | Schema | Descrição |
|--------|--------|-----------|
| Bronze | `raw`  | Dados como chegam do PostgreSQL operacional |
| Silver | `staging` | Dados limpos, tipados, sem duplicatas |
| Gold   | `gold` | Tabelas prontas para consumo (BI + ML) |

---

## 📁 Estrutura do repositório

```
gate4-data-platform/
├── README.md                    ← você está aqui
├── docs/
│   └── guia12_powerbi_mlops.html  ← Guia de estudo interativo
├── scripts/
│   └── guia12/
│       ├── 01_dim_data.sql          ← Criação da tabela de datas
│       ├── 02_feature_store.py      ← Features de churn (Python/Pandas)
│       ├── 03_dax_medidas.md        ← Medidas DAX documentadas
│       └── 04_pipeline_airflow.py   ← Estrutura do DAG diário
├── data/
│   └── synthetic/               ← Dados sintéticos para testes
└── notebooks/
    └── eda_gate4.ipynb          ← Análise exploratória inicial
```

---

## 🚀 Setup rápido (Windows / Git Bash)

```bash
# 1. Clone o repositório
git clone https://github.com/alesina78/gate4-data-platform.git
cd gate4-data-platform

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/Scripts/activate   # Git Bash no Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o script de features
python scripts/guia12/02_feature_store.py
```

---

## 📊 Modelo estrela — GATE4 DW

```
                    ┌─────────────┐
                    │  dim_data   │
                    │  (sem bur.) │
                    └──────┬──────┘
                           │
┌──────────────┐    ┌──────▼──────┐    ┌────────────────┐
│  dim_aluno   │───▶│ fato_faturas│◀───│  dim_haras     │
└──────────────┘    └─────────────┘    └────────────────┘
                           │
┌──────────────┐    ┌──────▼──────┐    ┌────────────────┐
│ dim_modalid. │───▶│  fato_aulas │◀───│  dim_haras     │
└──────────────┘    └─────────────┘    └────────────────┘
```

---

## 🤖 Modelos preditivos implementados

| Modelo | Algoritmo | Acurácia (dados sintéticos) | Tabela gold |
|--------|-----------|----------------------------|-------------|
| Churn de alunos | LightGBM | ~84% AUC-ROC | `gold.risco_churn` |
| Previsão de ocupação | Prophet | MAPE ~12% | `gold.previsao_ocupacao` |
| EOQ de insumos | Fórmula Wilson + ajuste | — | `gold.pedido_econ` |

> **Nota:** modelos treinados com dados sintéticos/anonimizados. Dados reais de clientes
> não são publicados por razões de LGPD e confidencialidade.

---

## 📈 Dashboard Power BI (3 páginas)

| Página | Foco | KPIs principais |
|--------|------|-----------------|
| Saúde Financeira | Faturamento, inadimplência, A/R | MoM %, YTD, faixa de atraso |
| Alunos em Risco | Churn prediction | Prob. saída, dias inativos |
| Ocupação | Baias e horários | % ociosidade, previsão 30d |

📸 *Screenshots disponíveis em [`/docs/screenshots/`](docs/screenshots/)*

---

## 🛠️ Stack tecnológica

**Dados & Engenharia**
- Python 3.11+ · Pandas · NumPy · SQLAlchemy
- PostgreSQL 15 · dbt (Data Build Tool)
- Apache Airflow (orquestração)

**Machine Learning**
- Scikit-learn · LightGBM · Prophet
- MLflow (versionamento de modelos)

**BI & Visualização**
- Power BI Desktop (DAX, Power Query, RLS)

**Infra & DevOps**
- Git / GitHub · Docker (ambiente local)
- BigQuery / Snowflake (opcional — Cloud)

---

## 📚 Guias de estudo

Este repositório acompanha uma trilha de transição de carreira
Oracle/PL-SQL → Engenharia de Dados. Os guias estão em `/docs/`.

| Guia | Tema | Arquivo |
|------|------|---------|
| 12 | Power BI, MLOps & Portfólio | [guia12_powerbi_mlops.html](docs/guia12_powerbi_mlops.html) |

---

## 👤 Autor

**Alessandro** · Senior Oracle PL-SQL Developer & Analyst → Data Engineer  
25+ anos em sistemas mission-critical (Banco do Brasil, Santander, Sicredi, Engie)  
Criador da plataforma GATE4 · Equitação desde 1987

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin)](https://linkedin.com/in/alesina78)
[![GitHub](https://img.shields.io/badge/GitHub-alesina78-181717?logo=github)](https://github.com/alesina78)

---

## 📄 Licença

MIT — veja [LICENSE](LICENSE) para detalhes.  
Dados de clientes reais do GATE4 não fazem parte deste repositório.
