"""
Módulo M6 · Estoque (GATE4 Data Platform)
------------------------------------------
Calcula dias de cobertura de insumos, identifica risco de ruptura e compara
o consumo real de estoque com o consumo diário planejado.
"""

import numpy as np
import pandas as pd


def calcular_cobertura_estoque(estoque: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula os dias de cobertura de estoque para cada item (quantidade_atual / consumo_diario).
    Trata divisões por zero ou valores nulos com segurança usando np.where e np.nan.
    """
    df = estoque.copy()
    
    # Converte colunas numéricas
    df["quantidade_atual"] = pd.to_numeric(df["quantidade_atual"], errors="coerce").fillna(0)
    df["consumo_diario"] = pd.to_numeric(df["consumo_diario"], errors="coerce")
    df["alerta_minimo"] = pd.to_numeric(df["alerta_minimo"], errors="coerce").fillna(0)
    
    # Cálculo seguro de dias de cobertura (evita divisão por zero ou consumo nulo/negativo)
    consumo = df["consumo_diario"].to_numpy()
    qtd = df["quantidade_atual"].to_numpy()
    
    dias_cobertura = np.where((consumo > 0) & (qtd >= 0), qtd / consumo, np.nan)
    df["dias_cobertura"] = np.round(dias_cobertura, 1)
    
    # Identifica itens abaixo do ponto de reposição / alerta mínimo
    df["alerta_reposicao"] = df["quantidade_atual"] <= df["alerta_minimo"]
    
    return df


def auditar_consumo_real(estoque: pd.DataFrame, movimentacoes: pd.DataFrame, dias_janela: int = 30, data_referencia: str = "2026-10-27") -> pd.DataFrame:
    """
    Compara o consumo real médio dos últimos X dias (saídas de estoque) 
    com o consumo diário cadastrado na tabela de itens.
    """
    df_mov = movimentacoes.copy()
    df_mov["data"] = pd.to_datetime(df_mov["data"])
    ref_date = pd.to_datetime(data_referencia)
    
    # Filtra apenas o histórico da janela recente (ex: últimos 30 dias) e tipos de saída
    data_corte = ref_date - pd.Timedelta(days=dias_janela)
    saidas = df_mov[
        (df_mov["data"] >= data_corte) & 
        (df_mov["data"] <= ref_date) & 
        (df_mov["tipo"].str.upper().isin(["SAIDA", "CONSUMO", "BAIXA"]))
    ].copy()
    
    # Soma a quantidade consumida por item na janela
    consumo_recente = (
        saidas.groupby("item_id")["quantidade"]
        .sum()
        .reset_index(name="total_consumido_janela")
    )
    
    # Calcula a média diária real no período
    consumo_recente["consumo_medio_real_diario"] = consumo_recente["total_consumido_janela"] / dias_janela
    
    # Cruza com o cadastro oficial de estoque
    comparativo = estoque.merge(consumo_recente, left_on="id", right_on="item_id", how="left")
    comparativo["consumo_medio_real_diario"] = comparativo["consumo_medio_real_diario"].fillna(0.0)
    comparativo["consumo_diario"] = comparativo["consumo_diario"].fillna(0.0)
    
    # Identifica desvios expressivos (ex: consumo real 30% maior que o cadastrado)
    comparativo["desvio_consumo"] = (
        comparativo["consumo_medio_real_diario"] - comparativo["consumo_diario"]
    )
    
    return comparativo[["id", "nome", "empresa_id", "consumo_diario", "consumo_medio_real_diario", "desvio_consumo"]]