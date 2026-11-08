"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 3, Exercício 6                                  ║
║  Arquivo : ex06_testes_api.py                                                ║
║  Tema    : Testes automatizados da API com pytest + TestClient              ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Testar a API FastAPI sem precisar subir um servidor — o TestClient do FastAPI
simula as requisições HTTP diretamente em memória.

PRINCÍPIO: Teste ANTES de subir o Docker
Analogia Oracle: como rodar um DBMS_UNIT ou script de validação antes
de dar o deploy em produção. Nunca envie uma API para o container sem
pelo menos 3 casos de teste: positivo, inválido e edge case.

COMO RODAR
----------
  source .venv/Scripts/activate
  pip install pytest httpx fastapi scikit-learn pandas joblib pydantic

  # Certifique-se de ter o modelo treinado (ex04) e o app (ex05) disponíveis
  python ex04_treinar_pipeline_churn.py   # gera modelos/churn_v1.joblib

  # Roda todos os testes
  pytest ex06_testes_api.py -v

  # Roda um teste específico
  pytest ex06_testes_api.py::test_predict_aluno_risco_alto -v

CONVENÇÃO pytest
----------------
  - Arquivos de teste: começam com test_ ou terminam com _test.py
  - Funções de teste: começam com test_
  - assert é a verificação — se falhar, o teste falha com mensagem clara
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
import pytest
from fastapi.testclient import TestClient

# Importa o app do ex05 — o TestClient usa o app diretamente, sem servidor HTTP
from ex05_fastapi_app import app

# TestClient: simula requisições HTTP em memória
# É como ter um cliente SQL interno para testar procedures sem abrir uma sessão real
client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# DADOS DE TESTE — fixtures reutilizáveis
# ─────────────────────────────────────────────────────────────────────────────

# Aluno com perfil de ALTO risco: pouca frequência, muitos reagendamentos, muito atraso
ALUNO_RISCO_ALTO = {
    "frequencia_mensal":     1,     # quase não vai às aulas
    "qtd_aulas_reagendadas": 7,     # reagenda muito
    "dias_atraso_medio":     60.0,  # paga com atraso
    "modalidade":            "Salto"
}

# Aluno com perfil de BAIXO risco: frequente, pontual, sem reagendamentos
ALUNO_RISCO_BAIXO = {
    "frequencia_mensal":     12,    # vai muito
    "qtd_aulas_reagendadas": 0,     # nunca reagenda
    "dias_atraso_medio":     0.0,   # sempre em dia
    "modalidade":            "Hipismo"
}

# Aluno com modalidade NOVA — não existia no treino (testa handle_unknown)
ALUNO_MODALIDADE_NOVA = {
    "frequencia_mensal":     5,
    "qtd_aulas_reagendadas": 1,
    "dias_atraso_medio":     5.0,
    "modalidade":            "Dressage"   # nunca visto no treino
}


# ─────────────────────────────────────────────────────────────────────────────
# TESTES DO ENDPOINT /health
# ─────────────────────────────────────────────────────────────────────────────

def test_health_retorna_200():
    """
    O /health deve sempre responder 200 quando o modelo está carregado.
    Usado pelo Docker healthcheck e pelo load balancer para saber se
    o container está saudável.
    """
    r = client.get("/health")
    assert r.status_code == 200, f"Esperado 200, recebeu {r.status_code}"
    assert r.json()["status"] == "ok"
    assert "modelo" in r.json()


# ─────────────────────────────────────────────────────────────────────────────
# TESTES DO ENDPOINT /predict
# ─────────────────────────────────────────────────────────────────────────────

def test_predict_retorna_200_com_campos_corretos():
    """
    Uma requisição válida deve retornar 200 com os campos esperados.
    Verifica o contrato da API (schema de resposta).
    """
    r = client.post("/predict", json=ALUNO_RISCO_BAIXO)

    assert r.status_code == 200, f"Esperado 200, recebeu {r.status_code}: {r.text}"

    dados = r.json()
    # Verifica que todos os campos obrigatórios estão presentes
    assert "prob_churn"  in dados, "Campo 'prob_churn' ausente na resposta"
    assert "risco"       in dados, "Campo 'risco' ausente na resposta"
    assert "modelo"      in dados, "Campo 'modelo' ausente na resposta"
    assert "timestamp"   in dados, "Campo 'timestamp' ausente na resposta"


def test_predict_probabilidade_entre_0_e_1():
    """
    A probabilidade deve sempre estar entre 0.0 e 1.0.
    Se estiver fora desse intervalo, o modelo está com problema.
    """
    r = client.post("/predict", json=ALUNO_RISCO_ALTO)
    prob = r.json()["prob_churn"]

    assert 0.0 <= prob <= 1.0, f"Probabilidade inválida: {prob} (deve ser 0 a 1)"


def test_predict_risco_valido():
    """
    O campo 'risco' deve ser exatamente 'ALTO' ou 'BAIXO' — nada mais.
    Consistência do contrato com o Django que vai consumir essa API.
    """
    for aluno in [ALUNO_RISCO_ALTO, ALUNO_RISCO_BAIXO]:
        r = client.post("/predict", json=aluno)
        risco = r.json()["risco"]
        assert risco in ["ALTO", "BAIXO"], f"Risco inválido: '{risco}'"


def test_predict_aluno_risco_alto():
    """
    Aluno com perfil de alto risco deve retornar 'ALTO'.
    Este teste valida que o modelo aprendeu o padrão correto.
    """
    r = client.post("/predict", json=ALUNO_RISCO_ALTO)
    assert r.status_code == 200

    dados = r.json()
    # O aluno com freq=1, reagend=7, atraso=60 deve ter risco ALTO
    assert dados["risco"] == "ALTO", (
        f"Esperado ALTO para aluno de alto risco, recebeu {dados['risco']} "
        f"(prob={dados['prob_churn']})"
    )


def test_predict_frequencia_negativa_retorna_422():
    """
    Frequência negativa deve ser rejeitada pelo Pydantic (ge=0).
    Retorna 422 Unprocessable Entity automaticamente — sem código manual.
    Analogia Oracle: violação de CHECK CONSTRAINT.
    """
    r = client.post("/predict", json={
        "frequencia_mensal":     -5,     # ← inválido: ge=0 não satisfeito
        "qtd_aulas_reagendadas": 2,
        "dias_atraso_medio":     10.0,
        "modalidade":            "Salto"
    })
    assert r.status_code == 422, f"Esperado 422, recebeu {r.status_code}"


def test_predict_campo_faltando_retorna_422():
    """
    Campos obrigatórios faltando devem retornar 422.
    O Pydantic valida que todos os campos do schema estão presentes.
    """
    r = client.post("/predict", json={
        "frequencia_mensal": 5
        # faltam: qtd_aulas_reagendadas, dias_atraso_medio, modalidade
    })
    assert r.status_code == 422


def test_predict_modalidade_nova_nao_quebra():
    """
    Modalidade não vista no treino (Dressage) NÃO deve retornar 500.
    Testa o handle_unknown='ignore' do OneHotEncoder.
    Se este teste falhar: adicionar handle_unknown='ignore' e re-treinar.
    """
    r = client.post("/predict", json=ALUNO_MODALIDADE_NOVA)
    assert r.status_code == 200, (
        f"Modalidade nova causou erro {r.status_code}: {r.text}\n"
        "Correção: adicionar handle_unknown='ignore' no OneHotEncoder e re-treinar."
    )
    assert 0.0 <= r.json()["prob_churn"] <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# TESTES DO ENDPOINT /predict_lote
# ─────────────────────────────────────────────────────────────────────────────

def test_predict_lote_retorna_lista_correta():
    """
    /predict_lote deve retornar uma lista com o mesmo número de alunos enviados.
    Cada item deve ter aluno_id, prob_churn e risco.
    """
    payload = [
        {"aluno_id": 1, **ALUNO_RISCO_ALTO},
        {"aluno_id": 2, **ALUNO_RISCO_BAIXO},
        {"aluno_id": 3, **ALUNO_MODALIDADE_NOVA},
    ]
    r = client.post("/predict_lote", json=payload)

    assert r.status_code == 200, f"Erro {r.status_code}: {r.text}"

    resultados = r.json()
    assert len(resultados) == 3, f"Esperado 3 resultados, recebeu {len(resultados)}"

    for res in resultados:
        assert "aluno_id"   in res
        assert "prob_churn" in res
        assert "risco"      in res
        assert 0.0 <= res["prob_churn"] <= 1.0


def test_predict_lote_preserva_ids():
    """
    Os IDs devolvidos devem corresponder aos IDs enviados.
    Crítico para o Django associar cada resultado ao aluno correto.
    """
    payload = [
        {"aluno_id": 42, **ALUNO_RISCO_ALTO},
        {"aluno_id": 99, **ALUNO_RISCO_BAIXO},
    ]
    r = client.post("/predict_lote", json=payload)
    ids_devolvidos = [res["aluno_id"] for res in r.json()]

    assert 42 in ids_devolvidos, "ID 42 não encontrado na resposta"
    assert 99 in ids_devolvidos, "ID 99 não encontrado na resposta"


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO DE EXECUÇÃO DIRETA (sem pytest)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("GATE4 — Exercício 6: Executando testes manualmente")
    print("=" * 65)
    print("(Para resultado completo, rode: pytest ex06_testes_api.py -v)\n")

    testes = [
        ("health retorna 200",             test_health_retorna_200),
        ("predict campos corretos",        test_predict_retorna_200_com_campos_corretos),
        ("probabilidade entre 0 e 1",      test_predict_probabilidade_entre_0_e_1),
        ("risco válido (ALTO/BAIXO)",      test_predict_risco_valido),
        ("aluno risco alto → ALTO",        test_predict_aluno_risco_alto),
        ("frequência negativa → 422",      test_predict_frequencia_negativa_retorna_422),
        ("campo faltando → 422",           test_predict_campo_faltando_retorna_422),
        ("modalidade nova não quebra",     test_predict_modalidade_nova_nao_quebra),
        ("lote retorna lista correta",     test_predict_lote_retorna_lista_correta),
        ("lote preserva IDs",              test_predict_lote_preserva_ids),
    ]

    ok = err = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"  ✅ {nome}")
            ok += 1
        except AssertionError as e:
            print(f"  ❌ {nome}: {e}")
            err += 1
        except Exception as e:
            print(f"  ⚠️  {nome}: {type(e).__name__}: {e}")
            err += 1

    print(f"\n{'='*65}")
    print(f"Resultado: {ok}/{ok+err} testes passaram")
    if err == 0:
        print("✅ Todos os testes passaram — API pronta para o Docker!")
    else:
        print("❌ Corrija os erros antes de fazer o docker build.")
    print("=" * 65 + "\n")
