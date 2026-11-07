# 🐎 GATE4 Data Platform

> **Plataforma de Engenharia de Dados & Analytics** aplicada à gestão inteligente de centros equestres, ecoterapia e reabilitação.  
> Pipeline end-to-end: geração sintética de dados → qualidade → limpeza → análise financeira/operacional → Machine Learning.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.x-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Pytest](https://img.shields.io/badge/Testes-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![Status](https://img.shields.io/badge/Status-Ativo-2ea44f?style=flat-square)]()
[![Licença](https://img.shields.io/badge/Licença-MIT-yellow?style=flat-square)]()

---

## 🎯 O Problema de Negócio

Centros equestres operam com dados fragmentados: controle de saúde animal em planilhas, faturamento em cadernos, frequência de alunos no WhatsApp. O resultado é **inadimplência invisível, cavalos sobrecarregados e churn de alunos que ninguém antecipou**.

Este projeto constrói a **espinha dorsal analítica** do [GATE4](https://github.com/alesina78) — plataforma SaaS multi-tenant para gestão de haras e hípicas — transformando 17 tabelas relacionais em inteligência acionável para o gestor do centro.

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
│                     GATE4 Data Platform                      │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  M0      │  M1      │  M2      │  M3–M7   │  M8             │
│ Gerador  │Qualidade │ Limpeza  │Analytics │ Orquestração    │
│Sintético │          │          │          │                  │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│            Persistência em Parquet  (staging → gold)         │
├─────────────────────────────────────────────────────────────┤
│          ML · Churn Prediction  (HistGradientBoosting)       │
└─────────────────────────────────────────────────────────────┘
```

**Modelo de dados:** 17 tabelas relacionais, arquitetura multi-empresa (multi-tenant), com chaves estrangeiras validadas em cada camada.

---

## 📦 Módulos

### Camada de Dados

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M0 · Gerador Sintético** | `g18_m0_gerador.py` | Geração relacional com `numpy.random` (Poisson/Lognormal) e injeção controlada de inconsistências para simular dados reais de produção |
| **M1 · Qualidade** | `g18_m1_qualidade.py` | Auditoria de integridade referencial, detecção de FKs órfãs e validação de nulos por criticidade de coluna |
| **M2 · Limpeza** | `g18_m2_limpeza.py` | Normalização de textos livres via Regex, conversão segura de tipos (`Int64`, `datetime`) e log de transformações |

### Camada Analítica

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M3 · Financeiro** | `g18_m3_financeiro.py` | Faturamento mensal por empresa, inadimplência, aging de faturas com datas dinâmicas e auditoria contábil de itens |
| **M4 · Operação** | `g18_m4_operacao.py` | Taxa de conclusão de aulas por instrutor, detecção de sobrecarga de cavalos via Percentil 90 |
| **M5 · Manejo** | `g18_m5_manejo.py` | Auditoria automatizada de prazos de vacinas, vermífugos, ferrageamentos e casqueamentos por empresa |
| **M6 · Estoque** | `g18_m6_estoque.py` | Dias de cobertura de insumos, prevenção de divisão por zero e alertas de ruptura iminente |
| **M7 · Alunos & RFM** | `g18_m7_alunos.py` | Alunos em risco de churn (>60 dias sem frequência) e cálculo de métricas RFM (Recência, Frequência, Monetário) |

### Camada de Orquestração & ML

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| **M8 · Pipeline** | `g18_pipeline.py` | Orquestração sequencial M0→M7 com persistência em Parquet por camada (raw → staging → gold) |
| **ML · Churn** | `g18_ml_churn.py` | Modelo preditivo de evasão de alunos — ABT, pipeline Scikit-Learn, ROC-AUC e Lift Operacional |

---

## 🤖 Machine Learning — Previsão de Churn

Evolução do pipeline analítico para um modelo preditivo de evasão de alunos, seguindo boas práticas de MLOps:

**Construção da ABT (Analytical Base Table)**
- Agregação de variáveis comportamentais (frequência, cancelamentos, intervalo desde última aula) e financeiras (inadimplência, ticket médio) por aluno
- Data de corte dinâmica — features usam **apenas dados do passado** em relação à data de avaliação *(zero data leakage)*

**Modelo & Validação**
- `HistGradientBoostingClassifier` — robusto a nulos, sem necessidade de imputação manual
- Pipeline Scikit-Learn com padronização e validação cruzada temporal (`TimeSeriesSplit`)

**Métricas de Impacto de Negócio**
- **ROC-AUC** — métrica técnica de discriminação
- **Lift Operacional** — quantas vezes a campanha direcionada aos alunos de maior risco é mais eficiente do que contatos aleatórios *(ex.: Lift 3.2× = a campanha atinge 3× mais churns por contato)*

**Persistência**
```
modelos/modelo_churn_gate4.joblib
```

---

## 🧪 Testes Automatizados

Suíte completa de testes unitários com `pytest`, cobrindo validações de integridade, transformações e saídas dos módulos analíticos.

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar todos os testes
pytest -v

# Executar módulo específico
pytest tests/test_financeiro.py -v
```

---

## ▶️ Como Executar

```bash
# 1. Clonar o repositório
git clone https://github.com/alesina78/gate4-data-platform.git
cd gate4-data-platform

# 2. Criar e ativar o ambiente virtual (Git Bash / Windows)
python -m venv .venv
source .venv/Scripts/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Rodar o pipeline completo (M0 → M8)
python g18_pipeline.py

# 5. Rodar módulo individual (exemplo)
python g18_m3_financeiro.py
```

---

## 📚 Trilha de Estudos / Guias

Os módulos do pipeline foram desenvolvidos em paralelo com uma **trilha estruturada de estudos** em Data Science, com scripts didáticos comentados linha a linha no padrão SQL → Pandas:

| Guia | Tema | Pasta |
|---|---|---|
| Guia 1 | Fundamentos Pandas + NumPy | `guia-01/` |
| Guia 2 | Séries Temporais, Rolling, Leakage Temporal | `guia-02/` |
| Guia 3 | Visualização com Matplotlib/Seaborn | `guia-03/` *(em breve)* |
| Guia 10 | Machine Learning — Churn Prediction | integrado ao M8 |

> Scripts escritos para profissionais com background Oracle/PL-SQL em transição para o ecossistema Python. Cada método Pandas tem comentário com o equivalente SQL correspondente.

---

## 🛠️ Stack Técnica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.13 |
| Manipulação de dados | Pandas 2.x, NumPy |
| Machine Learning | Scikit-Learn (`HistGradientBoostingClassifier`, `TimeSeriesSplit`) |
| Persistência | Parquet (via PyArrow / FastParquet) |
| Testes | pytest |
| Controle de versão | Git + GitHub |
| Ambiente | VS Code · Git Bash · `.venv` |

---

## 📁 Estrutura do Repositório

```
gate4-data-platform/
│
├── g18_m0_gerador.py           # M0 · Gerador sintético relacional
├── g18_m1_qualidade.py         # M1 · Qualidade e integridade referencial
├── g18_m2_limpeza.py           # M2 · Limpeza e normalização
├── g18_m3_financeiro.py        # M3 · Analytics financeiro e aging
├── g18_m4_operacao.py          # M4 · Analytics operacional e instrutores
├── g18_m5_manejo.py            # M5 · Saúde e manejo animal
├── g18_m6_estoque.py           # M6 · Estoque e cobertura de insumos
├── g18_m7_alunos.py            # M7 · RFM e churn early warning
├── g18_pipeline.py             # M8 · Orquestração completa (M0→M7)
├── g18_ml_churn.py             # ML · Modelo preditivo de churn
│
├── modelos/
│   └── modelo_churn_gate4.joblib   # Artefato treinado (serializado)
│
├── guia-02-series-temporais/   # Scripts didáticos — Guia 2
│   ├── ex01_sql_para_pandas.py
│   ├── ex02_leakage_temporal.py
│   ├── ex03_previsao_faturamento_gate4.py
│   └── README.md
│
├── tests/                      # Suíte pytest
├── requirements.txt
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

*Dados utilizados: 100% sintéticos, gerados pelo módulo M0 para fins de estudo e demonstração de pipeline. Nenhum dado real de clientes é utilizado ou exposto.*
