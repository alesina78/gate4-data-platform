# 🐎 GATE4 Data Platform

Plataforma de Engenharia de Dados e Analytics desenvolvida para o gerenciamento analítico de centros equestres, ecoterapia e reabilitação, baseada em um Modelo Entidade-Relacionamento (ER) real contendo 17 tabelas e arquitetura multiempresa.

---

## 🛠️ Arquitetura e Módulos do Projeto

O pipeline de dados é estruturado em módulos independentes e testados via automação:

* **M0 · Gerador Sintético (`g18_m0_gerador.py`):** Geração relacional de massa de dados utilizando `numpy.random` (distribuições Poisson/Lognormal) com injeção controlada de inconsistências.
* **M1 · Qualidade (`g18_m1_qualidade.py`):** Auditoria de integridade referencial, detecção de chaves estrangeiras órfãs e validação de nulos.
* **M2 · Limpeza (`g18_m2_limpeza.py`):** Normalização de textos livres via Regex e conversão segura de tipos (`Int64` e `datetime`).
* **M3 · Financeiro (`g18_m3_financeiro.py`):** Faturamento mensal por empresa, cálculo de inadimplência, aging de faturas com datas dinâmicas e auditoria contábil de itens.
* **M4 · Operação (`g18_m4_operacao.py`):** Taxa de conclusão de aulas por instrutor e detecção de sobrecarga de cavalos via Percentil 90.
* **M5 · Manejo (`g18_m5_manejo.py`):** Auditoria automatizada de prazos de vacinas, vermífugos, ferrageamentos e casqueamentos baseada nas regras configuradas por empresa.
* **M6 · Estoque (`g18_m6_estoque.py`):** Cálculo de dias de cobertura de insumos, prevenção de divisão por zero e alertas de ruptura.
* **M7 · Alunos & RFM (`g18_m7_alunos.py`):** Identificação de alunos ativos em risco de churn (>60 dias sem frequência) e cálculo de métricas RFM.
* **M8 · Orquestração (`g18_pipeline.py`):** Orquestração completa do fluxo com persistência em arquivos Parquet.

---

## 🤖 Módulo de Machine Learning · Previsão de Churn (Guia 10)

Evolução do pipeline analítico para um modelo preditivo de evasão de alunos, construído seguindo boas práticas de MLOps:

* **Construção da ABT (Analytical Base Table):** Agregação de variáveis comportamentais e financeiras por aluno.
* **Prevenção de Data Leakage:** Uso estrito de regras temporais onde as *features* utilizam apenas dados do passado em relação à data de corte.
* **Modelo Preditivo:** Pipeline em Scikit-Learn utilizando `HistGradientBoostingClassifier` com imputação de nulos e padronização.
* **Métricas de Impacto de Negócio:** Além do ROC-AUC técnico, o modelo avalia o **Lift Operacional** (quantas vezes a campanha de retenção direcionada aos clientes de maior risco é mais eficiente do que contatos aleatórios).
* **Persistência de Artefato:** O modelo treinado é serializado e salvo em `modelos/modelo_churn_gate4.joblib`.

---

## 🧪 Testes Automatizados

O projeto conta com uma suíte completa de testes unitários desenvolvida com `pytest`. Para executar a validação:

```bash
pytest -v