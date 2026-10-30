"""
Módulo M5 · Manejo e Saúde Animal (GATE4 Data Platform)
-------------------------------------------------------
Verifica prazos de vacinas, vermífugos, ferrageamentos e casqueamentos com base
na configuração específica de cada empresa (haras).
"""

import numpy as np
import pandas as pd


def auditar_prazos_manejo(cavalos: pd.DataFrame, prazos_empresa: pd.DataFrame, data_referencia: str = "2026-10-27") -> pd.DataFrame:
    """
    Cruza os cavalos com os prazos da empresa e calcula o status de vacina,
    vermífugo, ferrageamento e casqueamento.
    """
    df_cav = cavalos.copy()
    df_prz = prazos_empresa.copy()
    ref_date = pd.to_datetime(data_referencia)
    
    # Garante conversão de datas
    for col in ["ultima_vacina", "ultimo_vermifugo", "ultimo_ferrageamento", "ultimo_casqueamento"]:
        if col in df_cav.columns:
            df_cav[col] = pd.to_datetime(df_cav[col])
            
    # Merge com os prazos da empresa (validação 1:1 ou m:1 por empresa_id)
    merged = df_cav.merge(df_prz, on="empresa_id", how="left", suffixes=("", "_prazo"))
    
    # Função auxiliar interna para classificar o status de um manejo específico
    def avaliar_status(data_ultima, prazo_limite):
        if pd.isna(data_ultima):
            return "NUNCA APLICADO"
        if pd.isna(prazo_limite):
            return "SEM PRAZO CONFIGURADO"
            
        dias_decorridos = (ref_date - data_ultima).days
        atraso = dias_decorridos - prazo_limite
        
        # Lógica com np.select
        condicoes = [
            atraso > 0,
            atraso >= -7  # Vencendo nos próximos 7 dias
        ]
        resultados = ["VENCIDO", "VENCE EM 7D"]
        
        return np.select(condicoes, resultados, default="OK")

    # Aplica a avaliação para cada tipo de manejo obrigatório do ER
    if "ultima_vacina" in merged.columns and "prazo_vacina" in merged.columns:
        merged["status_vacina"] = [avaliar_status(row.ultima_vacina, row.prazo_vacina) for _, row in merged.iterrows()]
        
    if "ultimo_vermifugo" in merged.columns and "prazo_vermifugo" in merged.columns:
        merged["status_vermifugo"] = [avaliar_status(row.ultimo_vermifugo, row.prazo_vermifugo) for _, row in merged.iterrows()]
        
    if "ultimo_ferrageamento" in merged.columns and "prazo_ferrageamento" in merged.columns:
        merged["status_ferrageamento"] = [avaliar_status(row.ultimo_ferrageamento, row.prazo_ferrageamento) for _, row in merged.iterrows()]
        
    if "ultimo_casqueamento" in merged.columns and "prazo_casqueamento" in merged.columns:
        merged["status_casqueamento"] = [avaliar_status(row.ultimo_casqueamento, row.prazo_casqueamento) for _, row in merged.iterrows()]
        
    return merged