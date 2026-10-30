import pandas as pd
import pytest
from gate4.g18_m6_estoque import calcular_cobertura_estoque
from gate4.g18_m7_alunos import identificar_alunos_inativos_risco


def test_calcular_cobertura_estoque():
    estoque_mock = pd.DataFrame({
        "id": [1, 2],
        "empresa_id": [10, 10],
        "nome": ["Ração", "Feno"],
        "quantidade_atual": [100.0, 50.0],
        "consumo_diario": [10.0, 0.0], # Item 2 tem consumo zero para testar divisão segura
        "alerta_minimo": [20.0, 10.0]
    })
    
    res = calcular_cobertura_estoque(estoque_mock)
    
    # Item 1: 100 / 10 = 10 dias de cobertura
    assert res.loc[res["id"] == 1, "dias_cobertura"].values[0] == 10.0
    # Item 2: Consumo 0 não deve dar erro de divisão por zero (deve retornar NaN)
    assert pd.isna(res.loc[res["id"] == 2, "dias_cobertura"].values[0])


def test_identificar_alunos_inativos_risco():
    alunos_mock = pd.DataFrame({
        "id": [1, 2],
        "empresa_id": [10, 10],
        "nome": ["Carlos", "Ana"],
        "ativo": [True, True]
    })
    
    aulas_mock = pd.DataFrame({
        "id": [101, 102],
        "aluno_id": [1, 2],
        "data_hora": ["2026-01-01 10:00:00", "2026-10-25 10:00:00"] # Carlos sumido desde jan, Ana teve aula há 2 dias
    })
    
    # Referência: 2026-10-27
    res = identificar_alunos_inativos_risco(alunos_mock, aulas_mock, dias_limite=60, data_referencia="2026-10-27")
    
    # Carlos deve estar em risco (mais de 60 dias sem aula)
    assert 1 in res["id"].values
    # Ana NÃO deve estar em risco (aula recente)
    assert 2 not in res["id"].values