"""
Módulo M4 · Operação das Aulas (GATE4 Data Platform)
----------------------------------------------------
Analisa a performance de conclusão de aulas por instrutor, horários de pico
e sobrecarga de trabalho dos cavalos com base no percentil 90.
"""

import numpy as np
import pandas as pd


def calcular_taxa_conclusao_instrutor(aulas: pd.DataFrame, perfis: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a taxa de conclusão de aulas por instrutor, cruzando com a tabela de perfis.
    Trata instrutores nulos separadamente.
    """
    df = aulas.copy()
    
    # Identifica aulas sem instrutor atribuído
    df["instrutor_id"] = df["instrutor_id"].fillna(-1)
    
    # Agrupa por instrutor
    resumo = (
        df.groupby("instrutor_id")
        .agg(
            total_aulas=("id", "count"),
            aulas_concluidas=("concluida", lambda x: x.sum()),
        )
        .reset_index()
    )
    
    resumo["taxa_conclusao_pct"] = (
        resumo["aulas_concluidas"] / resumo["total_aulas"]
    ) * 100
    
    # Cruza com o nome/cargo do perfil se houver instrutores válidos
    perfis_clean = perfis.copy()
    perfis_clean["id"] = perfis_clean["id"].astype(int)
    
    resultado = resumo.merge(
        perfis_clean[["id", "cargo"]],
        left_on="instrutor_id",
        right_on="id",
        how="left"
    )
    
    resultado["cargo"] = resultado["cargo"].fillna("Sem Instrutor / Externo")
    return resultado.drop(columns=["id"])


def identificar_cavalos_sobrecarregados(aulas: pd.DataFrame, threshold_percentil: float = 90.0) -> pd.DataFrame:
    """
    Identifica quais cavalos possuem uma carga de aulas semanal acima do percentil configurado
    (por padrão, P90), indicando risco potencial de sobrecarga.
    """
    df = aulas.copy()
    df["data_hora"] = pd.to_datetime(df["data_hora"])
    
    # Cria uma coluna de Ano-Semana para agrupar as aulas por semana
    df["ano_semana"] = df["data_hora"].dt.strftime("%Y-W%V")
    
    # Conta quantas aulas cada cavalo fez por semana
    carga_semanal = (
        df.groupby(["cavalo_id", "ano_semana"])
        .agg(aulas_na_semana=("id", "count"))
        .reset_index()
    )
    
    # Média de aulas semanais por cavalo ao longo do período
    media_cavalo = (
        carga_semanal.groupby("cavalo_id")
        .agg(media_aulas_semana=("aulas_na_semana", "mean"))
        .reset_index()
    )
    
    # Calcula o limiar do percentil 90
    limiar_p90 = np.percentile(media_cavalo["media_aulas_semana"], threshold_percentil)
    
    # Filtra cavalos acima do limiar
    sobrecarregados = media_cavalo[media_cavalo["media_aulas_semana"] >= limiar_p90].copy()
    sobrecarregados["limiar_utilizado_p90"] = limiar_p90
    
    return sobrecarregados.sort_values(by="media_aulas_semana", ascending=False)