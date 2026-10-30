import numpy as np
import pandas as pd

def gerar_dados_gate4(n_alunos=100, n_cavalos=None, n_empresas=3, seed=42):
    """Gera dados didáticos e sintéticos para empresas, alunos e cavalos do GATE4."""
    if n_alunos < 0 or n_empresas < 1:
        raise ValueError("n_alunos deve ser >= 0 e n_empresas deve ser >= 1.")
    if n_cavalos is None:
        n_cavalos = max(1, n_alunos // 4)
    if n_cavalos < 0:
        raise ValueError("n_cavalos deve ser >= 0.")

    rng = np.random.default_rng(seed)
    empresa_ids = np.arange(1, n_empresas + 1)

    empresas = pd.DataFrame({
        "empresa_id": empresa_ids,
        "nome": [f"Centro Equestre {i:02d}" for i in empresa_ids],
    })

    alunos = pd.DataFrame({
        "aluno_id": np.arange(1, n_alunos + 1),
        "empresa_id": rng.choice(empresa_ids, size=n_alunos),
        "ativo": rng.choice([True, False], size=n_alunos, p=[0.85, 0.15]),
        "valor_aula": rng.uniform(70, 180, size=n_alunos).round(2),
    })

    cavalos = pd.DataFrame({
        "cavalo_id": np.arange(1, n_cavalos + 1),
        "empresa_id": rng.choice(empresa_ids, size=n_cavalos),
        "peso_kg": rng.normal(480, 55, size=n_cavalos).round(1),
    })

    return empresas, alunos, cavalos

def introduzir_inconsistencias(cavalos, seed=7, proporcao=0.10):
    """Injeca erros artificiais (nulos e valores inválidos) para praticar limpeza de dados."""
    rng = np.random.default_rng(seed)
    sujos = cavalos.copy()
    quantidade = int(len(sujos) * proporcao)
    if quantidade == 0:
        return sujos
    indices = rng.choice(sujos.index.to_numpy(), size=quantidade, replace=False)
    metade = quantidade // 2
    if metade:
        sujos.loc[indices[:metade], "peso_kg"] = np.nan
    sujos.loc[indices[metade:], "peso_kg"] = -10
    return sujos