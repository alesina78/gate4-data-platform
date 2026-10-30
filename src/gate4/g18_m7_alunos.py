"""
Módulo M7 · Alunos e Retenção / RFM (GATE4 Data Platform)
---------------------------------------------------------
Calcula métricas de Recência, Frequência e Valor (RFM) dos alunos e identifica
alunos ativos em risco de churn (sem aulas há mais de 60 dias).
"""

import numpy as np
import pandas as pd


def identificar_alunos_inativos_risco(alunos: pd.DataFrame, aulas: pd.DataFrame, dias_limite: int = 60, data_referencia: str = "2026-10-27") -> pd.DataFrame:
    """
    Filtra alunos marcados como ativos (ativo=True) que não possuem registros
    de aula nos últimos X dias (padrão 60 dias), identificando risco de evasão (churn).
    """
    df_alu = alunos[alunos["ativo"] == True].copy()
    df_aul = aulas.copy()
    
    df_aul["data_hora"] = pd.to_datetime(df_aul["data_hora"])
    ref_date = pd.to_datetime(data_referencia)
    
    # Encontra a data da última aula de cada aluno
    ultima_aula = (
        df_aul.groupby("aluno_id")["data_hora"]
        .max()
        .reset_index(name="ultima_aula_data")
    )
    
    # Cruza com a lista de alunos ativos
    analise = df_alu.merge(ultima_aula, left_on="id", right_on="aluno_id", how="left")
    
    # Calcula dias desde a última aula
    analise["dias_desde_ultima_aula"] = (ref_date - analise["ultima_aula_data"]).dt.days
    
    # Alunos que nunca tiveram aula ou cuja última aula ultrapassou o limite são considerados em risco
    em_risco = analise[
        analise["dias_desde_ultima_aula"].isna() | 
        (analise["dias_desde_ultima_aula"] >= dias_limite)
    ].copy()
    
    # Trata nulos para exibição amigável
    em_risco["dias_desde_ultima_aula"] = em_risco["dias_desde_ultima_aula"].fillna(9999) # 9999 = Nunca teve aula
    
    # Define as colunas de retorno de forma dinâmica caso valor_aula exista ou não
    colunas_base = ["id", "empresa_id", "nome", "dias_desde_ultima_aula"]
    if "valor_aula" in em_risco.columns:
        colunas_base.insert(3, "valor_aula")
        
    return em_risco[colunas_base]


def calcular_rfm_alunos(alunos: pd.DataFrame, aulas: pd.DataFrame, faturas: pd.DataFrame, data_referencia: str = "2026-10-27") -> pd.DataFrame:
    """
    Calcula as métricas RFM (Recência, Frequência, Monetário) básicas para cada aluno.
    """
    ref_date = pd.to_datetime(data_referencia)
    
    # Frequência: Total de aulas por aluno
    freq = aulas.groupby("aluno_id").agg(frequencia_aulas=("id", "count")).reset_index()
    
    # Recência: Dias desde a última aula
    aulas_dt = aulas.copy()
    aulas_dt["data_hora"] = pd.to_datetime(aulas_dt["data_hora"])
    rec = aulas_dt.groupby("aluno_id").agg(ultima_aula=("data_hora", "max")).reset_index()
    rec["recencia_dias"] = (ref_date - rec["ultima_aula"]).dt.days
    
    # Monetário: Soma das faturas pagas ou emitidas por aluno
    mon = faturas.groupby("aluno_id").agg(valor_total_faturas=("valor", "sum")).reset_index()
    
    # Consolida com a base de alunos
    rfm = alunos[["id", "empresa_id", "nome"]].merge(freq, left_on="id", right_on="aluno_id", how="left")
    rfm = rfm.merge(rec[["aluno_id", "recencia_dias"]], on="aluno_id", how="left")
    rfm = rfm.merge(mon, on="aluno_id", how="left")
    
    # Preenche valores ausentes para alunos sem aulas ou faturas
    rfm["frequencia_aulas"] = rfm["frequencia_aulas"].fillna(0).astype(int)
    rfm["recencia_dias"] = rfm["recencia_dias"].fillna(999)
    rfm["valor_total_faturas"] = rfm["valor_total_faturas"].fillna(0.0)
    
    return rfm.drop(columns=["aluno_id"], errors="ignore")