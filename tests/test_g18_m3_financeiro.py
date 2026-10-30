import pandas as pd
import pytest
from gate4.g18_m3_financeiro import (
    calcular_faturamento_mensal,
    calcular_aging_faturas,
    auditar_consistencia_itens
)

def test_calcular_faturamento_mensal():
    # Dados fictícios manuais para teste unitário puro
    faturas_mock = pd.DataFrame({
        "id": [1, 2, 3],
        "empresa_id": [1, 1, 2],
        "data_vencimento": ["2026-01-10", "2026-01-15", "2026-01-20"],
        "valor": [100.0, 200.0, 300.0],
        "status": ["PAGO", "PENDENTE", "PAGO"]
    })
    
    res = calcular_faturamento_mensal(faturas_mock)
    
    assert len(res) == 2
    # Empresa 1 deve ter bruto 300.0 e pago 100.0
    emp1 = res[res["empresa_id"] == 1].iloc[0]
    assert emp1["faturamento_bruto"] == 300.0
    assert emp1["faturamento_pago"] == 100.0
    assert emp1["taxa_inadimplencia_pct"] == pytest.approx(66.66, rel=1e-2)

def test_auditar_consistencia_itens():
    faturas_mock = pd.DataFrame({
        "id": [10, 20],
        "empresa_id": [1, 1],
        "valor": [150.0, 300.0]
    })
    
    itens_mock = pd.DataFrame({
        "fatura_id": [10, 10, 20],
        "valor": [50.0, 100.0, 250.0]  # Fatura 20 diverge (300 vs 250)
    })
    
    divergentes = auditar_consistencia_itens(faturas_mock, itens_mock)
    
    assert len(divergentes) == 1
    assert divergentes.iloc[0]["id"] == 20
    assert divergentes.iloc[0]["valor"] == 300.0
    assert divergentes.iloc[0]["soma_itens_valor"] == 250.0