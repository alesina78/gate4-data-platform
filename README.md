# 🐎 GATE4 Data Platform

> **Plataforma de Engenharia de Dados & Analytics** aplicada à gestão inteligente de centros equestres, ecoterapia e reabilitação.  
> Pipeline end-to-end: geração sintética → qualidade → limpeza → análise financeira/operacional → Machine Learning.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
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

```text
┌─────────────────────────────────────────────────────────────┐
│                     GATE4 Data Platform                     │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  M0      │  M1      │  M2      │  M3–M7   │  M8             │
│ Gerador  │Qualidade │ Limpeza  │Analytics │ Orquestração    │
│Sintético │          │          │          │                 │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│            Persistência em Parquet  (staging → gold)         │
├─────────────────────────────────────────────────────────────┤
│          ML · Churn Prediction  (HistGradientBoosting)       │
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

### Camada Analítica

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M3 · Financeiro** | `src/gate4/g18_m3_financeiro.py` | Faturamento mensal, inadimplência, aging de faturas com datas dinâmicas e auditoria contábil |
| **M4 · Operação** | `src/gate4/g18_m4_operacao.py` | Taxa de conclusão de aulas por instrutor e sobrecarga de cavalos via Percentil 90 |
| **M5 · Manejo** | `src/gate4/g18_m5_manejo.py` | Auditoria de prazos de vacinas, vermífugos, ferrageamentos e casqueamentos por empresa |
| **M6 · Estoque** | `src/gate4/g18_m6_estoque.py` | Dias de cobertura de insumos, prevenção de divisão por zero e alertas de ruptura |
| **M7 · Alunos & RFM** | `src/gate4/g18_m7_alunos.py` | Alunos em risco de churn (>60 dias sem frequência) e métricas RFM |

### Camada de Orquestração & ML

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M8 · Pipeline** | `src/gate4/g18_pipeline.py` | Orquestração sequencial M0→M7 com persistência em Parquet (raw → staging → gold) |
| **ML · Churn** | `src/gate4/g18_guia1_churn.py` | Modelo preditivo de evasão — ABT, pipeline Scikit-Learn, ROC-AUC e Lift Operacional |

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

## 📚 Trilha de Estudos (Apostila Guia 0)

Jornada de transição de **Oracle/PL-SQL Sênior → Engenharia de Dados & Analytics**, documentada em notebooks e scripts com foco no padrão **SQL → Pandas**:

| Trilha / Guia | Tema & Entregável | Status |
|---|---|---|
| `notebooks/guia-18-projeto-pandas-numpy/` | Guia 18: Projeto Pandas/NumPy com ER real do GATE4 | ✅ Concluído |
| `notebooks/guia-01-sql-pandas-ml/` | Guia 1: SQL → Pandas → ML: EDA, NumPy e visualizações | ✅ Concluído |
| `notebooks/guia-02-series-temporais/` | Guia 2: Séries Temporais, resample, rolling e leakage | ✅ Concluído |
| `notebooks/guia-03-fastapi-docker/` | Guia 3: FastAPI + Docker: API de risco de churn | ✅ Concluído |

---

## 🧪 Testes Automatizados

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
source .venv/Scripts/activate

pip install -r requirements.txt

# Pipeline completo (M0 -> M8)
python src/gate4/g18_pipeline.py

# Módulo individual
python src/gate4/g18_m3_financeiro.py
```

---

## 📁 Estrutura do Repositório

```text
gate4-data-platform/
│
├── src/gate4/                          # Módulos de produção do pipeline M0 a M8 + ML Churn
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
├── notebooks/                          # Cadernos de estudo organizados por guia da apostila
│   ├── guia-01-sql-pandas-ml/          # Guia 1: SQL → Pandas → ML
│   │   ├── ex07_numpy_fundamentos.py
│   │   ├── ex08_eda_completo_gate4.py
│   │   ├── ex09_visualizacoes_avancadas.py
│   │   └── README.md
│   │
│   ├── guia-02-series-temporais/       # Guia 2: Séries temporais, rolling, leakage
│   │   ├── ex01_sql_para_pandas.py
│   │   ├── ex02_leakage_temporal.py
│   │   ├── ex03_previsao_faturamento_gate4.py
│   │   └── README.md
│   │
│   ├── guia-03-fastapi-docker/         # Guia 3: FastAPI + Docker
│   │   ├── ex04_treinar_pipeline_churn.py
│   │   ├── ex05_fastapi_app.py
│   │   ├── ex06_testes_api.py
│   │   └── README.md
│   │
│   └── guia-18-projeto-pandas-numpy/   # Guia 18: Laboratório do ER real GATE4
│       ├── 01_teste_pandas.py
│       ├── 02_series_temporais_pandas.py
│       ├── 03_numpy_eda_visualizacao.py
│       ├── 04_machine_learning_churn.py
│       └── README.md
│
├── scripts/                            # Utilitários e experimentos
│   ├── g10_churn_project.py
│   ├── g16_performance.py
│   ├── generators_G18_1.py
│   └── README.md
│
├── modelos/                            # Artefatos serializados (.joblib)
│   ├── churn_v1.joblib
│   └── modelo_churn_gate4.joblib
│
├── docs/                               # Documentação e anotações técnicas
│   ├── Anotacoes.sql
│   ├── ARQUITETURA.md
│   └── DIAGNOSTICO_GATE4.md
│
├── data/processed/                     # Camada Gold/Staging Parquet (no .gitignore)
│   ├── alunos.parquet
│   ├── alunos_risco_churn.parquet
│   ├── cavalos_tratados.parquet
│   └── relatorio_qualidade.parquet
│
├── saidas/                             # 7 visualizações PNG geradas pelo pipeline
│   ├── 01_hist_dias_atraso.png
│   ├── 02_boxplot_mensalidade_plano.png
│   ├── 03_barras_atraso_plano.png
│   ├── 04_dispersao_aulas_atraso.png
│   ├── 05_mapa_correlacao.png
│   ├── 06_matriz_confusao.png
│   └── 07_curva_precision_recall.png
│
├── tests/                              # Suíte de testes automatizados (pytest)
├── pyproject.toml
└── README.md
```

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
