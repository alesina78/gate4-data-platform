import numpy as np
import pandas as pd

def gerar_er_gate4_sintetico(seed=42):
    """
    M0 · GERADOR DE DADOS SINTÉTICOS DO GATE4
    
    EXPLICAÇÃO PASSO A PASSO:
    Este script simula o modelo relacional (ER) real do ecossistema do haras (GATEAGORA).
    Ele cria tabelas fictícias interligadas (empresas, alunos, cavalos e faturas) utilizando
    funções estatísticas do NumPy e injeta propositalmente inconsistências (sujeiras) para 
    treinar os próximos módulos de limpeza de dados.
    """
    
    # 1. Inicializa o gerador de números aleatórios do NumPy com uma semente (seed) fixa.
    # Por que fazer isso? Garante a reprodutibilidade: sempre que rodarmos o script,
    # os mesmos dados "aleatórios" serão gerados, permitindo testes consistentes.
    rng = np.random.default_rng(seed)
    
    # 2. Criação da tabela de Empresas (Centros Equestres)
    # No modelo multiempresa do GATE4, os dados são sempre segregados por 'empresa_id'.
    empresas = pd.DataFrame({
        "empresa_id": [1, 2, 3],
        "nome": ["Centro Equestre Alpha", "Haras Beta", "Hipica Gamma"]
    })
    
    # 3. Criação da tabela de Alunos / Clientes (~150 registros)
    n_alunos = 150
    alunos = pd.DataFrame({
        "aluno_id": np.arange(1, n_alunos + 1), # Gera IDs sequenciais de 1 a 150
        "empresa_id": rng.choice([1, 2, 3], size=n_alunos, p=[0.5, 0.3, 0.2]), # Sorteia a empresa vinculada
        "ativo": rng.choice([True, False], size=n_alunos, p=[0.85, 0.15]),     # 85% ativos, 15% inativos
        "valor_aula": rng.uniform(80.0, 200.0, size=n_alunos).round(2),         # Sorteia preços de aula contínuos
        "nome": [f"Aluno {i}" for i in range(1, n_alunos + 1)]                 # Cria nomes fictícios sequenciais
    })
    
    # 4. Criação da tabela de Cavalos (~120 registros)
    # Nota do Guia 18: No sistema legado real, colunas como ração frequentemente vêm 
    # como texto livre ("2 kg", "3kg"). Simulamos isso aqui propositalmente.
    n_cavalos = 120
    racao_textos = [f"{rng.integers(1, 4)} kg" if rng.random() > 0.05 else "indefinido" for _ in range(n_cavalos)]
    
    cavalos = pd.DataFrame({
        "cavalo_id": np.arange(1, n_cavalos + 1),
        "empresa_id": rng.choice([1, 2, 3], size=n_cavalos),
        "peso_kg": rng.normal(480, 45, size=n_cavalos).round(1), # Distribuição normal centrada em 480kg
        "racao_qtd_manha": racao_textos,
        "feno_qtd": [f"{rng.integers(3, 8)}kg" for _ in range(n_cavalos)]
    })
    
    # Injeção proposital de sujeira para testar as regras de limpeza (M1 e M2):
    cavalos.loc[rng.choice(cavalos.index, 5), "peso_kg"] = np.nan       # Insere valores nulos (NaN)
    cavalos.loc[rng.choice(cavalos.index, 3), "peso_kg"] = -50.0      # Insere peso físico impossível (negativo)
    
    # 5. Criação da tabela de Faturas (Financeiro)
    n_faturas = 300
    fatura_aluno_ids = rng.choice(alunos["aluno_id"], size=n_faturas).astype(float)
    
    # Injeção de erros de integridade referencial (FKs quebradas):
    fatura_aluno_ids[rng.choice(n_faturas, 10)] = np.nan             # Faturas sem aluno associado (nulas)
    fatura_aluno_ids[rng.choice(n_faturas, 5)] = 9999                # Faturas com aluno inexistente (ID órfão)
    
    faturas = pd.DataFrame({
        "fatura_id": np.arange(1, n_faturas + 1),
        "aluno_id": fatura_aluno_ids,
        "valor": rng.uniform(150.0, 1200.0, size=n_faturas).round(2),
        "status": rng.choice(["Pago", "Pendente", "Vencido", "Cancelado"], size=n_faturas, p=[0.7, 0.15, 0.1, 0.05])
    })
    
    # Retorna todas as tabelas encapsuladas em um dicionário Python
    return {"empresas": empresas, "alunos": alunos, "cavalos": cavalos, "faturas": faturas}