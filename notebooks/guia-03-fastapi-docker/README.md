# 🚀 Guia 3 — Modelo em Produção: FastAPI + Docker

> **Trilha:** Engenharia de Dados, MLOps & Nuvem · **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)

---

## 🎯 Objetivo

Colocar o modelo de churn treinado no Guia 2 em produção como uma **API REST em container Docker**, integrada ao painel Django do GATE4.

---

## 📁 Arquivos

| Arquivo | Tema | Dificuldade |
|---|---|---|
| `ex04_treinar_pipeline_churn.py` | Pipeline Scikit-Learn completo + serialização joblib | ⭐⭐ |
| `ex05_fastapi_app.py` | API FastAPI com `/health`, `/predict` e `/predict_lote` | ⭐⭐⭐ |
| `ex06_testes_api.py` | Testes automatizados com pytest + TestClient | ⭐⭐⭐ |

---

## ▶️ Como rodar em sequência

```bash
source .venv/Scripts/activate
pip install fastapi uvicorn scikit-learn pandas joblib pydantic pytest httpx

# 1. Treina e salva o pipeline
python ex04_treinar_pipeline_churn.py

# 2. Sobe a API (modo dev)
uvicorn ex05_fastapi_app:app --reload --port 8000

# 3. Testa (em outro terminal)
pytest ex06_testes_api.py -v
```

---

## 🔵 Analogias Oracle → FastAPI

| Oracle/PL-SQL | FastAPI/Python |
|---|---|
| Package com lógica encapsulada | Pipeline Scikit-Learn serializado |
| `CHECK CONSTRAINT` / `NOT NULL` | Validação Pydantic (erro 422 automático) |
| `SELECT 1 FROM DUAL` | `GET /health` |
| Chamada de FUNCTION | `POST /predict` |
| `FORALL` / bulk processing | `POST /predict_lote` |
| Deploy de package | `docker build && docker push` |

---

## 🐳 Docker (referência rápida)

```bash
# Build
docker build -t gate4-churn:1.0 .

# Run
docker run -d -p 8000:8000 --name churn gate4-churn:1.0

# Testar
curl -X POST localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"frequencia_mensal":2,"qtd_aulas_reagendadas":5,"dias_atraso_medio":40.0,"modalidade":"Salto"}'

# Logs
docker logs churn
```

---

## ⚠️ Regras de Produção

| Regra | Motivo |
|---|---|
| Salvar **Pipeline completo** (não só o modelo) | A API não pode repetir transformações |
| `handle_unknown='ignore'` no OneHotEncoder | Categoria nova não quebra em produção |
| Versionar o `.joblib` (`v1`, `v2`...) | Nunca sobrescrever modelo em produção |
| Usar a **mesma versão** do scikit-learn no treino e na API | Incompatibilidade de versão = erro 500 |
| `timeout=2` ao chamar a API do Django | A IA nunca pode derrubar o sistema principal |
| Nunca colocar senhas na imagem Docker | Usar variáveis de ambiente (`-e` ou `.env`) |

---

## 🗺️ Trilha de estudos

```
Guia 1 — Pandas Fundamentals          ✅ Concluído
Guia 2 — Séries Temporais             ✅ Concluído
Guia 3 — FastAPI + Docker             ✅ Este módulo
Guia 4 — EDA + Visualização           🔜 Próximo
Guia 5 — MLflow + Drift Monitoring    ⬜ Planejado
```
