"""
Módulo M3 · Financeiro (GATE4 Data Platform)
--------------------------------------------
Calcula o faturamento mensal por empresa, taxa de inadimplência, aging de faturas,
atraso médio em dias úteis e audita a consistência entre o valor da fatura e a soma dos seus itens.
"""

import numpy as np
import pandas as pd


def calcular_faturamento_mensal(faturas: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o faturamento bruto e o valor efetivamente pago agrupado por empresa e mês de vencimento.
    Filtra apenas faturas que não foram canceladas.
    """
    df = faturas.copy()
    
    # Padroniza a data de vencimento e extrai o ano-mês
    df["data_vencimento"] = pd.to_datetime(df["data_vencimento"])
    df["ano_mes"] = df["data_vencimento"].dt.to_period("M").astype(str)
    
    # Considera apenas faturas ativas (exclui canceladas se houver)
    ativas = df[df["status"].str.upper() != "CANCELADO"].copy()
    
    # Agrupamento por empresa e mês
    faturamento = (
        ativas.groupby(["empresa_id", "ano_mes"], dropna=False)
        .agg(
            faturamento_bruto=("valor", "sum"),
            faturamento_pago=("valor", lambda x: x[ativas["status"].str.upper() == "PAGO"].sum()),
            total_faturas=("id", "count")
        )
        .reset_index()
    )
    
    # Calcula a taxa de inadimplência básica
    faturamento["taxa_inadimplencia_pct"] = np.where(
        faturamento["faturamento_bruto"] > 0,
        ((faturamento["faturamento_bruto"] - faturamento["faturamento_pago"]) / faturamento["faturamento_bruto"]) * 100,
        0.0
    )
    
    return faturamento


def calcular_aging_faturas(faturas: pd.DataFrame, data_referencia: str = None) -> pd.DataFrame:
    """
    Classifica as faturas pendentes ou atrasadas em faixas de aging (0-30, 31-60, 61-90, 90+ dias),
    utilizando pd.cut. Se data_referencia for None, usa a data atual do sistema de forma dinâmica.
    """
    df = faturas.copy()
    df["data_vencimento"] = pd.to_datetime(df["data_vencimento"])
    
    # Se nenhuma data foi passada, usa o dia de hoje dinamicamente!
    ref_date = pd.to_datetime(data_referencia) if data_referencia else pd.Timestamp.today().normalize()
    
    # Filtra apenas o que está em aberto / vencido
    aberto = df[df["status"].str.upper().isin(["PENDENTE", "ATRASADO"])].copy()
    
    # Calcula quantos dias passou do vencimento em relação à data de referência
    aberto["dias_atraso"] = (ref_date - aberto["data_vencimento"]).dt.days
    aberto["dias_atraso"] = aberto["dias_atraso"].clip(lower=0)  # Evita negativos para vencimentos futuros
    
    # Define as faixas de aging
    bins = [-1, 30, 60, 90, 99999]
    labels = ["0-30 dias", "31-60 dias", "61-90 dias", "90+ dias"]
    
    aberto["faixa_aging"] = pd.cut(aberto["dias_atraso"], bins=bins, labels=labels)
    
    # Agrupa por empresa e faixa de aging
    aging_resumo = (
        aberto.groupby(["empresa_id", "faixa_aging"], observed=False)
        .agg(
            quantidade_faturas=("id", "count"),
            valor_total_devido=("valor", "sum")
        )
        .reset_index()
    )
    
    return aging_resumo


def auditar_consistencia_itens(faturas: pd.DataFrame, itens_fatura: pd.DataFrame) -> pd.DataFrame:
    """
    Compara o valor total registrado na tabela fatura com a soma dos valores na tabela itemfatura.
    Identifica divergências contábeis para auditoria de integridade.
    """
    # Soma os itens por fatura_id
    soma_itens = (
        itens_fatura.groupby("fatura_id")["valor"]
        .sum()
        .reset_index(name="soma_itens_valor")
    )
    
    # Cruza com a tabela de faturas
    auditoria = faturas.merge(soma_itens, left_on="id", right_on="fatura_id", how="left")
    auditoria["soma_itens_valor"] = auditoria["soma_itens_valor"].fillna(0.0)
    
    # Identifica divergências (tolerância de centavos para evitar problemas de ponto flutuante)
    auditoria["divergencia"] = np.isclose(auditoria["valor"], auditoria["soma_itens_valor"], atol=1e-2) == False
    
    # Retorna apenas as faturas com divergência para investigação
    divergentes = auditoria[auditoria["divergencia"]][["id", "empresa_id", "valor", "soma_itens_valor"]]
    
    return divergentes