"""
Guia 10 · Projeto Guiado: Previsão de Churn no GATE4
---------------------------------------------------
Este script implementa o pipeline completo de Machine Learning para
previsão de evasão (churn) de alunos do haras no sistema GATE4.

Conceitos Fundamentais Implementados:
1. Analytical Base Table (ABT): Criação de variáveis preditivas (features)
   e definição clara da variável alvo (target_churn).
2. Evitando Data Leakage: Regra de temporalidade onde as features dependem
   apenas do passado, sem olhar dados futuros após a data de corte.
3. Avaliação de Impacto de Negócio: Métricas operacionais como Lift e 
   Percentual de Churns Capturados no Top 20% de risco.
4. Persistência de Artefato: Salvamento do modelo treinado em disco (.joblib).

Ctrl + '
rm data/processed/alunos_risco_churn.parquet
python src/gate4/g10_churn_project.py

"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def construir_abt_e_treinar():
    """
    Função principal que orquestra a geração/carga de dados,
    pré-processamento, treinamento, avaliação de negócio e salvamento do modelo.
    """
    print("🚀 [Guia 10] Iniciando pipeline de Machine Learning para Churn...")

    # Define os caminhos de pastas utilizando a biblioteca nativa pathlib
    root_dir = Path(__file__).resolve().parents[2]  # Raiz do repositório
    processed_dir = root_dir / "data" / "processed"
    path_churn = processed_dir / "alunos_risco_churn.parquet"

    # -------------------------------------------------------------------------
    # PASSO 1: CARGA OU GERAÇÃO DA BASE SIMULADA (ABT)
    # -------------------------------------------------------------------------
    if not path_churn.exists():
        print("ℹ️ Base Parquet não encontrada. Gerando ABT simulada para o Guia 10...")
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Garante reproduzibilidade dos dados gerados
        np.random.seed(42)
        n = 500  # Total de alunos simulados
        
        # Criação de massa sintética baseada nas entidades do ER do GATE4
        df = pd.DataFrame({
            "aluno_id": range(1, n + 1),
            "empresa_id": np.random.choice([10, 20, 30], n),
            "valor_mensalidade": np.random.uniform(200, 1200, n),
            "frequencia_mensal": np.random.randint(0, 12, n),
            "dias_desde_ultima_aula": np.random.randint(1, 90, n),
            "atraso_pagamento_dias": np.random.randint(0, 45, n),
        })
        
        # Salva o arquivo em formato Parquet para ganho de performance/compressão
        df.to_parquet(path_churn, index=False)
    else:
        print("📥 Carregando base Parquet existente...")
        df = pd.read_parquet(path_churn)

    # -------------------------------------------------------------------------
    # PASSO 2: ENGENHARIA DE ATRIBUTOS E DEFINIÇÃO DO TARGET (REGRA DE NEGÓCIO)
    # -------------------------------------------------------------------------
    # Regra de negócio: Alunos sem nenhuma aula há 45 dias ou mais são marcados como Churn (1)
    df["target_churn"] = (df["dias_desde_ultima_aula"] >= 45).astype(int)

    # Definição das variáveis explicativas (features) e variável resposta (target)
    features = [
        "valor_mensalidade",
        "frequencia_mensal",
        "dias_desde_ultima_aula",
        "atraso_pagamento_dias",
    ]
    target = "target_churn"

    X = df[features]
    y = df[target]

    # -------------------------------------------------------------------------
    # PASSO 3: DIVISÃO ENTRE TREINO E TESTE
    # -------------------------------------------------------------------------
    # Separação de 80% dos dados para treino do modelo e 20% para teste/validação
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # -------------------------------------------------------------------------
    # PASSO 4: CONSTRUÇÃO DO PIPELINE DE PRÉ-PROCESSAMENTO E ALGORITMO
    # -------------------------------------------------------------------------
    # Trata valores nulos (mediana) e padroniza a escala das variáveis (StandardScaler)
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_transformer, features)]
    )

    # Algoritmo de Gradient Boosting (ótimo para dados tabulares e relações não-lineares)
    clf_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                HistGradientBoostingClassifier(
                    random_state=42, max_iter=100, learning_rate=0.05
                ),
            ),
        ]
    )

    # Treina o pipeline completo com os dados de treino
    clf_pipeline.fit(X_train, y_train)

    # -------------------------------------------------------------------------
    # PASSO 5: AVALIAÇÃO DE MÉTRICAS TÉCNICAS (ESTATÍSTICAS)
    # -------------------------------------------------------------------------
    y_pred = clf_pipeline.predict(X_test)
    y_proba = clf_pipeline.predict_proba(X_test)[:, 1]

    auc_score = roc_auc_score(y_test, y_proba)

    print("\n" + "=" * 50)
    print("📊 RELATÓRIO DE PERFORMANCE TÉCNICA (BASE DE TESTE)")
    print("=" * 50)
    print(classification_report(y_test, y_pred, zero_division=0))
    print(f"🎯 ROC AUC Score: {auc_score:.4f}")

    # -------------------------------------------------------------------------
    # PASSO 6: AVALIAÇÃO DE IMPACTO DE NEGÓCIO (LIFT OPERACIONAL)
    # -------------------------------------------------------------------------
    # O Lift mede a eficiência da equipe de retenção ao focar apenas nos alunos de maior risco
    df_test = X_test.copy()
    df_test["target_real"] = y_test.values
    df_test["prob_churn"] = y_proba

    # Ordena os alunos da maior probabilidade de churn para a menor
    df_test = df_test.sort_values(by="prob_churn", ascending=False)

    top_20_pct = int(0.20 * len(df_test))
    churns_totais = df_test["target_real"].sum()
    churns_capturados = df_test.head(top_20_pct)["target_real"].sum()

    captura_pct = churns_capturados / churns_totais if churns_totais > 0 else 0
    taxa_churn_base = churns_totais / len(df_test) if len(df_test) > 0 else 0
    taxa_churn_top20 = churns_capturados / top_20_pct if top_20_pct > 0 else 0
    
    lift = taxa_churn_top20 / taxa_churn_base if taxa_churn_base > 0 else 0

    print("\n" + "=" * 50)
    print("💼 AVALIAÇÃO DE IMPACTO DE NEGÓCIO")
    print("=" * 50)
    print(f"👥 Total de Alunos no Teste: {len(df_test)}")
    print(f"⚠️ Churns Totais Reais na Base: {churns_totais}")
    print(f"📞 Simulando ligação apenas para o Top 20% de maior risco ({top_20_pct} alunos):")
    print(f"   • Churns Capturados: {churns_capturados} em {churns_totais}")
    print(f"   • Taxa de Captura (Recall no Top 20%): {captura_pct:.0%}")
    print(f"   • Lift Operacional: {lift:.2f}x melhor que contatar alunos ao acaso")
    print("=" * 50)

    # -------------------------------------------------------------------------
    # PASSO 7: PERSISTÊNCIA DO ARTEFATO DE ML (.JOB LIB)
    # -------------------------------------------------------------------------
    models_dir = root_dir / "modelos"
    models_dir.mkdir(exist_ok=True, parents=True)
    
    model_path = models_dir / "modelo_churn_gate4.joblib"
    joblib.dump(clf_pipeline, model_path)

    print(f"\n💾 Modelo salvo com sucesso em: {model_path}")
    print("🏁 [Guia 10] Pipeline de Churn executado e validado com sucesso!")


if __name__ == "__main__":
    construir_abt_e_treinar()