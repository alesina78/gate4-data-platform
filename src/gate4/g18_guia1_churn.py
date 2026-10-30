"""
Guia 1 · EDA & Baseline de Churn (GATE4 Data Platform)
------------------------------------------------------
Demonstra a transição de SQL para Pandas, análise exploratória (EDA) 
e construção de um pipeline de Machine Learning (Scikit-Learn).
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def executar_eda_e_baseline():
    print("📊 [Guia 1] Carregando dados para modelagem...")
    
    processed_dir = Path("data/processed")
    path_churn = processed_dir / "alunos_risco_churn.parquet"
    
    # Se o arquivo não existir, cria um DataFrame sintético equivalente para fins de laboratório
    if not path_churn.exists():
        print("ℹ️ Arquivo parquet não encontrado. Gerando massa simulada para o laboratório do Guia 1...")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        np.random.seed(42)
        n = 200
        df = pd.DataFrame({
            "id": range(1, n + 1),
            "empresa_id": [10] * n,
            "nome": [f"Aluno {i}" for i in range(1, n + 1)],
            "valor_aula": np.random.uniform(100, 500, n),
            "dias_desde_ultima_aula": np.random.randint(5, 120, n)
        })
        df.to_parquet(path_churn, index=False)
    else:
        df = pd.read_parquet(path_churn)
    
    # 1. EDA Básica (Equivalente a comandos SQL de contagem e distribuição)
    print("\n--- 1. Análise Exploratória de Dados (EDA) ---")
    print(f"Shape da base: {df.shape}")
    print(f"Média de dias desde a última aula: {df['dias_desde_ultima_aula'].mean():.1f}")
    print(f"Mediana de dias desde a última aula: {df['dias_desde_ultima_aula'].median():.1f}")
    
    # 2. Preparação da ABT (Analytical Base Table)
    df["target_churn"] = (df["dias_desde_ultima_aula"] >= 60).astype(int)
    
    features = ["valor_aula"]
    target = "target_churn"
    
    X = df[features]
    y = df[target]
    
    # 3. Pipeline de Machine Learning com Scikit-Learn
    print("\n--- 2. Treinamento do Modelo Baseline (Scikit-Learn) ---")
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), features)
        ]
    )
    
    model_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", HistGradientBoostingClassifier(random_state=42))
    ])
    
    model_pipeline.fit(X, y)
    y_pred = model_pipeline.predict(X)
    
    print("Relatório de Classificação:")
    print(classification_report(y, y_pred, zero_division=0))
    print("🏁 [Guia 1] EDA e Baseline executados com sucesso!")


if __name__ == "__main__":
    executar_eda_e_baseline()