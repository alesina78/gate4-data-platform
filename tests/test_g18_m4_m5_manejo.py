import pandas as pd
import pytest
from gate4.g18_m4_operacao import identificar_cavalos_sobrecarregados
from gate4.g18_m5_manejo import auditar_prazos_manejo


def test_auditar_prazos_manejo():
    cavalo_mock = pd.DataFrame({
        "id": [1, 2],
        "empresa_id": [10, 10],
        "ultima_vacina": ["2026-01-01", None], # Cavalo 1 vacinado há muito tempo, Cavalo 2 nunca
        "ultimo_vermifugo": ["2026-10-20", "2026-10-26"],
        "ultimo_ferrageamento": ["2026-09-01", "2026-10-20"],
        "ultimo_casqueamento": ["2026-09-01", "2026-10-20"]
    })
    
    prazos_mock = pd.DataFrame({
        "empresa_id": [10],
        "prazo_vacina": [90],
        "prazo_vermifugo": [60],
        "prazo_ferrageamento": [30],
        "prazo_casqueamento": [30]
    })
    
    res = auditar_prazos_manejo(cavalo_mock, prazos_mock, data_referencia="2026-10-27")
    
    # Cavalo 1 (vacina em jan/2026 com prazo de 90 dias) deve estar VENCIDO
    assert res.loc[res["id"] == 1, "status_vacina"].values[0] == "VENCIDO"
    # Cavalo 2 (nunca vacinado) deve estar NUNCA APLICADO
    assert res.loc[res["id"] == 2, "status_vacina"].values[0] == "NUNCA APLICADO"