import pandas as pd

def auditar_qualidade_faturas(faturas, alunos):
    """
    M1 · CARGA E QUALIDADE DOS DADOS
    
    EXPLICAÇÃO PASSO A PASSO:
    Responde à pergunta central de engenharia: 'Posso confiar nestes dados?'
    Este script varre a tabela em busca de anomalias relacionais (como chaves estrangeiras
    órfãs e nulos) e retorna um DataFrame de relatório pronto para auditoria.
    """
    relatorios = []
    
    # 1. Regra de Negócio: 'aluno_id' não pode ser nulo em hipótese alguma
    nulos_aluno = faturas["aluno_id"].isna().sum()
    if nulos_aluno > 0:
        relatorios.append({
            "tabela": "faturas",
            "regra": "aluno_id não pode ser nulo",
            "linhas_com_problema": int(nulos_aluno)
        })
        
    # 2. Regra de Negócio: Integridade Referencial (Verificação de FKs órfãs)
    # Extrai todos os IDs válidos da tabela pai (alunos)
    ids_alunos_validos = set(alunos["aluno_id"].dropna())
    
    # Filtra faturas que possuem aluno_id preenchido
    faturas_validas = faturas.dropna(subset=["aluno_id"])
    
    # O operador ~ inverte a condição: localiza quem NÃO está presente na lista de IDs válidos
    orfaos = ~faturas_validas["aluno_id"].isin(ids_alunos_validos)
    qtd_orfaos = orfaos.sum()
    
    if qtd_orfaos > 0:
        relatorios.append({
            "tabela": "faturas",
            "regra": "Chave estrangeira órfã (aluno_id inexistente)",
            "linhas_com_problema": int(qtd_orfaos)
        })
        
    # 3. Regra de Negócio: Domínio de texto esperado para o status de pagamento
    status_permitidos = {"Pago", "Pendente", "Vencido", "Cancelado"}
    status_inesperados = ~faturas["status"].isin(status_permitidos)
    qtd_status_ruim = status_inesperados.sum()
    
    if qtd_status_ruim > 0:
        relatorios.append({
            "tabela": "faturas",
            "regra": "Status de fatura fora do domínio esperado",
            "linhas_com_problema": int(qtd_status_ruim)
        })
        
    # Retorna o relatório consolidado em formato de tabela Pandas
    return pd.DataFrame(relatorios)