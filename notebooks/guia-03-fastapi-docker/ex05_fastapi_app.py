"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 3, Exercício 5                                  ║
║  Arquivo : ex05_fastapi_app.py                                               ║
║  Tema    : API FastAPI completa com /health, /predict e /predict_lote       ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
API de risco de churn do GATE4 pronta para rodar em container Docker.
Recebe dados de um aluno via POST, aplica o pipeline treinado e retorna
a probabilidade de cancelamento.

COMO RODAR
----------
  source .venv/Scripts/activate
  pip install fastapi uvicorn scikit-learn pandas joblib pydantic

  # Certifique-se de ter rodado ex04 primeiro para gerar modelos/churn_v1.joblib
  python ex04_treinar_pipeline_churn.py

  # Sobe a API em modo desenvolvimento (--reload reinicia ao salvar o arquivo)
  uvicorn ex05_fastapi_app:app --reload --port 8000

TESTAR NO BROWSER
-----------------
  http://localhost:8000/docs      → Swagger interativo (FastAPI gera automaticamente)
  http://localhost:8000/health    → {"status": "ok"}

TESTAR COM CURL (Git Bash)
--------------------------
  curl -X POST http://localhost:8000/predict \\
       -H "Content-Type: application/json" \\
       -d '{"frequencia_mensal":2,"qtd_aulas_reagendadas":5,"dias_atraso_medio":40.0,"modalidade":"Salto"}'

ANALOGIA ORACLE
---------------
  FastAPI     = Package PL/SQL exposta via REST (o contrato é o schema Pydantic)
  Pydantic    = CHECK CONSTRAINTS + NOT NULL do banco (valida antes de processar)
  /health     = SELECT 1 FROM DUAL (verifica se a API está viva)
  /predict    = Chamada de FUNCTION que retorna a probabilidade
  /predict_lote = Processamento em bulk (como um FORALL em PL/SQL)
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
from fastapi   import FastAPI, HTTPException
from pydantic  import BaseModel, Field
from typing    import List
from datetime  import datetime, timezone
import joblib, pandas as pd, logging, os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DO LOGGER
# Em produção: substitua por logging estruturado (JSON) para ELK ou CloudWatch
# Analogia Oracle: como DBMS_OUTPUT ou UTL_FILE para registrar auditoria
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("gate4.churn_api")


# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO DA API
# title e description aparecem automaticamente em /docs (Swagger)
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GATE4 — Churn Risk API",
    version="1.0.0",
    description=(
        "Prediz a probabilidade de churn (cancelamento) de alunos do haras. "
        "Alimenta o painel de alertas do sistema GATE4 Django."
    )
)


# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DO MODELO
# Feito uma vez ao iniciar a API — fica em memória para todas as requisições
# Analogia Oracle: como abrir um cursor global no package initialization
# ─────────────────────────────────────────────────────────────────────────────
CAMINHO_MODELO = os.getenv("MODELO_PATH", "modelos/churn_v1.joblib")
VERSAO_MODELO  = "churn_v1"
LIMIAR         = float(os.getenv("LIMIAR_CHURN", "0.30"))   # configurável via env

try:
    pipeline = joblib.load(CAMINHO_MODELO)
    logger.info(f"Modelo carregado: {CAMINHO_MODELO} | Limiar: {LIMIAR}")
except FileNotFoundError:
    logger.error(f"Modelo não encontrado em: {CAMINHO_MODELO}")
    logger.error("Rode ex04_treinar_pipeline_churn.py primeiro!")
    pipeline = None


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS PYDANTIC — contratos de entrada e saída
# Analogia Oracle: como definir o TYPE RECORD de entrada/saída de uma procedure
# ─────────────────────────────────────────────────────────────────────────────

class AlunoInput(BaseModel):
    """
    Dados de um aluno para previsão de churn.
    Pydantic valida automaticamente — erro 422 se algum campo for inválido.
    """
    frequencia_mensal:      int   = Field(
        ge=0, le=31,
        description="Aulas frequentadas no mês (0 a 31)",
        example=4
    )
    qtd_aulas_reagendadas:  int   = Field(
        ge=0,
        description="Reagendamentos nos últimos 60 dias",
        example=2
    )
    dias_atraso_medio:      float = Field(
        ge=0,
        description="Média de dias de atraso nas mensalidades",
        example=12.5
    )
    modalidade:             str   = Field(
        description="Modalidade do aluno: Salto, Hipismo, Equoterapia...",
        example="Salto"
    )


class ChurnResponse(BaseModel):
    """
    Resposta da previsão de churn.
    """
    prob_churn:   float   # probabilidade entre 0.000 e 1.000
    risco:        str     # "ALTO" ou "BAIXO"
    modelo:       str     # versão do modelo (para rastreabilidade)
    timestamp:    str     # momento da previsão (para auditoria)


class AlunoInputLote(AlunoInput):
    """
    Estende AlunoInput com ID para processamento em lote.
    O ID é devolvido na resposta para o Django associar ao aluno correto.
    """
    aluno_id: int = Field(description="ID do aluno no sistema GATE4", example=42)


class ChurnResponseLote(ChurnResponse):
    aluno_id: int


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Monitoramento"])
def health():
    """
    Verifica se a API e o modelo estão operacionais.
    Usado pelo Docker healthcheck e pelo load balancer.
    Analogia: SELECT 1 FROM DUAL — confirmação de vida do serviço.
    """
    if pipeline is None:
        # 503 = serviço indisponível (modelo não carregou)
        raise HTTPException(status_code=503, detail="Modelo não carregado")
    return {
        "status":  "ok",
        "modelo":  VERSAO_MODELO,
        "limiar":  LIMIAR,
        "api":     "GATE4 Churn Risk v1.0"
    }


@app.post("/predict", response_model=ChurnResponse, tags=["Previsão"])
def predict(aluno: AlunoInput):
    """
    Prevê o risco de churn de um único aluno.

    Recebe os dados via JSON, aplica o pipeline de ML e retorna:
    - prob_churn: probabilidade de cancelamento (0.0 a 1.0)
    - risco: "ALTO" se prob >= LIMIAR, "BAIXO" caso contrário
    - modelo: versão do modelo usado (rastreabilidade)
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Modelo não disponível")

    # 1. Converte Pydantic → DataFrame com as mesmas colunas do treino
    df   = pd.DataFrame([aluno.model_dump()])

    # 2. Pipeline aplica pré-processamento + previsão em uma chamada
    #    predict_proba retorna [[prob_classe_0, prob_classe_1]]
    #    [:, 1] pega a probabilidade da classe positiva (churn)
    prob  = float(pipeline.predict_proba(df)[0, 1])
    risco = "ALTO" if prob >= LIMIAR else "BAIXO"
    ts    = datetime.now(timezone.utc).isoformat()

    # 3. Auditoria — toda previsão em produção deve ser logada
    logger.info(f"predict | prob={prob:.3f} | risco={risco} | mod={VERSAO_MODELO}")

    return ChurnResponse(
        prob_churn=round(prob, 3),
        risco=risco,
        modelo=VERSAO_MODELO,
        timestamp=ts
    )


@app.post("/predict_lote", response_model=List[ChurnResponseLote], tags=["Previsão"])
def predict_lote(alunos: List[AlunoInputLote]):
    """
    Prevê o risco de churn para uma lista de alunos de uma só vez.

    Muito mais eficiente que chamar /predict N vezes:
    o DataFrame é criado uma vez e o pipeline processa todos juntos.

    Analogia Oracle: como um FORALL em PL/SQL ou um SELECT em bulk
    em vez de chamar uma FUNCTION linha a linha em LOOP.

    Exemplo de uso (relatório mensal):
      POST /predict_lote
      Body: [{"aluno_id": 1, ...}, {"aluno_id": 2, ...}]
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Modelo não disponível")

    # 1. Lista de objetos Pydantic → DataFrame
    df   = pd.DataFrame([a.model_dump() for a in alunos])
    ids  = df.pop('aluno_id')   # separa IDs (não são features do modelo)

    # 2. Previsão em bulk — uma chamada para todos os alunos
    probs = pipeline.predict_proba(df)[:, 1]
    ts    = datetime.now(timezone.utc).isoformat()

    logger.info(f"predict_lote | {len(alunos)} alunos | mod={VERSAO_MODELO}")

    # 3. Monta resposta associando cada ID à sua probabilidade
    return [
        ChurnResponseLote(
            aluno_id=int(aid),
            prob_churn=round(float(p), 3),
            risco="ALTO" if p >= LIMIAR else "BAIXO",
            modelo=VERSAO_MODELO,
            timestamp=ts
        )
        for aid, p in zip(ids, probs)
    ]
