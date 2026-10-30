import pytest
import pandas as pd
from gate4.g18_m0_gerador import gerar_er_gate4_sintetico
from gate4.g18_m1_qualidade import auditar_qualidade_faturas
from gate4.g18_m2_limpeza import limpar_cavalos
from gate4.g18_pipeline import executar_pipeline_completo

def test_limpeza_racao_regex():
    """
    TESTE DE LIMPEZA COM REGEX (M2)
    
    O QUE FAZ:
    Valida se a função 'limpar_cavalos' usa Expressões Regulares corretamente para 
    extrair o valor numérico de strings livres como '2 kg' e transformá-lo em tipo float.
    """
    # 1. Gera os dados sintéticos em memória usando a semente fixa
    dados = gerar_er_gate4_sintetico(seed=42)
    
    # 2. Aplica a função de limpeza na tabela de cavalos
    cavalos_limpos = limpar_cavalos(dados["cavalos"])
    
    # 3. Asserções (Validações):
    # - Confirma se a nova coluna numérica 'racao_kg_num' foi criada com sucesso
    assert "racao_kg_num" in cavalos_limpos.columns
    # - Confirma se o tipo de dado da coluna é numérico (float)
    assert pd.api.types.is_float_dtype(cavalos_limpos["racao_kg_num"])

def test_execucao_pipeline_completo():
    """
    TESTE DO PIPELINE COMPLETO (M0 até M8)
    
    O QUE FAZ:
    Executa a função principal do pipeline e valida se o relatório de qualidade 
    retorna as inconsistências que injetamos de propósito nos dados sintéticos.
    """
    # Executa o pipeline ponta a ponta
    relatorio = executar_pipeline_completo(seed=42)
    
    # Validações:
    # - O relatório de auditoria não pode estar vazio, pois geramos erros intencionais
    assert not relatorio.empty
    # - A coluna descritiva de contagem de problemas deve existir no relatório
    assert "linhas_com_problema" in relatorio.columns