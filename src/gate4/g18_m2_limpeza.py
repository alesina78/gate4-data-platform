import pandas as pd
import numpy as np

def limpar_cavalos(cavalos):
    """
    M2 · LIMPEZA E TIPAGEM DA TABELA DE CAVALOS
    
    EXPLICAÇÃO PASSO A PASSO:
    Resolve problemas comuns de sistemas legados:
    1. Extrai valores numéricos de colunas de texto livre (ex: transformar "2 kg" em número float).
    2. Identifica e neutraliza outliers físicos absurdos (ex: pesos negativos gerados por erro).
    """
    df = cavalos.copy()
    
    # 1. Uso de Expressões Regulares (Regex) para limpar campos de texto de ração:
    # - r'(\d+\.?\d*)' busca e captura o padrão numérico (dígitos e ponto decimal) dentro de strings como "2 kg".
    # - pd.to_numeric converte a string capturada para o tipo numérico float. Se falhar, vira NaN.
    df["racao_kg_num"] = pd.to_numeric(
        df["racao_qtd_manha"].str.extract(r'(\d+\.?\d*)')[0],
        errors="coerce"
    )
    
    # 2. Tratamento de Outliers de Peso:
    # Identifica pesos menores ou iguais a 0 (negativos) ou absurdamente altos (> 900kg) e anula os dados.
    peso_invalido = (df["peso_kg"] <= 0) | (df["peso_kg"] > 900)
    df.loc[peso_invalido, "peso_kg"] = np.nan
    
    return df