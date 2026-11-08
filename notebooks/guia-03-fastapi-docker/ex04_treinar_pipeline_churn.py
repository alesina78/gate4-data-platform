"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 3, Exercício 4                                  ║
║  Arquivo : ex04_treinar_pipeline_churn.py                                   ║
║  Tema    : Treinar e serializar o Pipeline Scikit-Learn completo            ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Treinar o pipeline completo de churn (pré-processamento + modelo) e salvar
em disco com versão no nome — pronto para ser carregado pela API FastAPI.

A DIFERENÇA CRÍTICA
-------------------
  ❌ ERRADO : salvar só o modelo           → API precisa repetir transformações
  ✅ CORRETO: salvar o pipeline inteiro    → API chama .predict_proba() diretamente

ANALOGIA ORACLE
---------------
  Pipeline = PACKAGE com lógica interna encapsulada.
  joblib.dump() = exportar o package para outro servidor.
  joblib.load() = importar e usar sem recompilar.

COMO RODAR
----------
  source .venv/Scripts/activate
  pip install scikit-learn pandas joblib numpy
  python ex04_treinar_pipeline_churn.py
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
import pandas  as pd
import numpy   as np
import joblib
import os
from sklearn.compose      import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline     import Pipeline
from sklearn.ensemble     import RandomForestClassifier
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics      import (classification_report,
                                   roc_auc_score,
                                   precision_recall_curve)
import warnings
warnings.filterwarnings('ignore')


# ─────────────────────────────────────────────────────────────────────────────
# 1. DADOS SIMULADOS — substitua pelos dados reais do GATE4
#    Query Oracle equivalente:
#    SELECT a.id,
#           COUNT(au.id) / 30.0           AS frequencia_mensal,
#           COUNT(r.id)                   AS qtd_aulas_reagendadas,
#           AVG(f.dias_atraso)            AS dias_atraso_medio,
#           a.modalidade,
#           CASE WHEN a.dt_cancelamento IS NOT NULL THEN 1 ELSE 0 END AS churn
#    FROM   alunos a
#    LEFT JOIN aulas au ON au.aluno_id = a.id AND au.data >= SYSDATE - 30
#    LEFT JOIN reagendamentos r ON r.aluno_id = a.id AND r.data >= SYSDATE - 60
#    LEFT JOIN faturas f ON f.aluno_id = a.id
#    GROUP BY a.id, a.modalidade, a.dt_cancelamento
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("GATE4 — Exercício 4: Treinar Pipeline Completo de Churn")
print("=" * 65)
print("\n📂 Gerando dados simulados do GATE4...")

rng = np.random.default_rng(seed=42)
n   = 500   # 500 alunos simulados

# Alunos que vão cancelar (churn=1) tendem a ter menos frequência,
# mais reagendamentos e mais atraso — isso é o padrão que o modelo aprende
churn = rng.binomial(1, 0.25, n)   # ~25% de churn (desbalanceado, como na vida real)

dados = pd.DataFrame({
    'frequencia_mensal':     np.where(churn,
                                rng.integers(0, 5, n),      # churns: pouca frequência
                                rng.integers(4, 15, n)),    # ativos: mais frequência
    'qtd_aulas_reagendadas': np.where(churn,
                                rng.integers(3, 10, n),     # churns: muitos reagendamentos
                                rng.integers(0, 4, n)),
    'dias_atraso_medio':     np.where(churn,
                                rng.uniform(15, 90, n),     # churns: atraso alto
                                rng.uniform(0, 20, n)),
    'modalidade':            rng.choice(
                                ['Salto', 'Hipismo', 'Equoterapia'],   # categorias do treino
                                size=n),
    'churn':                 churn
})

print(f"   Alunos simulados : {n}")
print(f"   Churns (label=1) : {churn.sum()} ({churn.mean():.1%}) — desbalanceado como produção")
print(f"   Features          : {list(dados.columns[:-1])}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. SEPARAÇÃO TREINO / TESTE — corte temporal (sem vazamento)
#    Em produção: use data de corte real (ex: alunos ativos até 2025-06-01)
# ─────────────────────────────────────────────────────────────────────────────
X = dados.drop(columns='churn')
y = dados['churn']

# Corte fixo (80% treino / 20% teste) — sem shuffle para simular corte temporal
corte = int(len(X) * 0.8)
X_tr, X_te = X.iloc[:corte], X.iloc[corte:]
y_tr, y_te = y.iloc[:corte], y.iloc[corte:]

print(f"\n   Treino: {len(X_tr)} alunos | Teste: {len(X_te)} alunos")


# ─────────────────────────────────────────────────────────────────────────────
# 3. DEFINIÇÃO DO PIPELINE COMPLETO
# ─────────────────────────────────────────────────────────────────────────────
print("\n🔧 Montando Pipeline (pré-processamento + modelo)...")

# ── Colunas por tipo ─────────────────────────────────────────────────────────
colunas_num = ['frequencia_mensal', 'qtd_aulas_reagendadas', 'dias_atraso_medio']
colunas_cat = ['modalidade']

# ── Pré-processador: cada tipo recebe o tratamento correto ────────────────────
preprocessador = ColumnTransformer(
    transformers=[
        # StandardScaler: normaliza numéricos para média 0 e desvio padrão 1
        # Analogia: como um z-score calculado em Oracle com STDDEV() OVER ()
        ('num', StandardScaler(), colunas_num),

        # OneHotEncoder: 'Salto' → [1,0,0] | 'Hipismo' → [0,1,0] | ...
        # handle_unknown='ignore': categoria nova → vetor de zeros (não quebra em produção)
        ('cat', OneHotEncoder(handle_unknown='ignore'), colunas_cat),
    ],
    remainder='drop'   # descarta qualquer coluna não listada acima
)

# ── Pipeline: pré-processador + classificador em sequência ────────────────────
pipeline = Pipeline(steps=[
    ('pre',   preprocessador),
    ('model', RandomForestClassifier(
        n_estimators=100,         # 100 árvores — mais = mais robusto, mais lento
        class_weight='balanced',  # compensa desequilíbrio: dá mais peso aos churns
        random_state=42           # reprodutibilidade
    ))
])

print("   ColumnTransformer : StandardScaler (num) + OneHotEncoder (cat)")
print("   Classificador     : RandomForestClassifier (class_weight=balanced)")


# ─────────────────────────────────────────────────────────────────────────────
# 4. TREINO
# ─────────────────────────────────────────────────────────────────────────────
print("\n🌲 Treinando o pipeline...")
pipeline.fit(X_tr, y_tr)
print("   Treino concluído!")


# ─────────────────────────────────────────────────────────────────────────────
# 5. AVALIAÇÃO — métricas de negócio + técnicas
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 Avaliando no conjunto de teste...")

y_pred      = pipeline.predict(X_te)
y_prob      = pipeline.predict_proba(X_te)[:, 1]   # probabilidade de churn
roc_auc     = roc_auc_score(y_te, y_prob)

print("\n   Relatório de Classificação:")
print(classification_report(y_te, y_pred, target_names=['Ativo', 'Churn']))
print(f"   ROC-AUC: {roc_auc:.3f}")

# ── Lift Operacional ──────────────────────────────────────────────────────────
# "Quantas vezes a campanha direcionada é mais eficiente que contatos aleatórios?"
# Pega o top 20% com maior risco e vê quantos churns reais estão ali
n_top     = max(1, int(len(y_te) * 0.20))
idx_top   = np.argsort(y_prob)[-n_top:]           # índices dos 20% maior risco
taxa_top  = y_te.iloc[idx_top].mean()              # % de churn real no top 20%
taxa_base = y_te.mean()                            # % de churn no total
lift      = taxa_top / taxa_base if taxa_base > 0 else 0

print(f"\n   Lift Operacional (top 20% de risco):")
print(f"   Taxa de churn no top 20% : {taxa_top:.1%}")
print(f"   Taxa de churn geral      : {taxa_base:.1%}")
print(f"   Lift                     : {lift:.1f}×")
print(f"   → A campanha direcionada é {lift:.1f}× mais eficiente que contatos aleatórios")


# ─────────────────────────────────────────────────────────────────────────────
# 6. SERIALIZAÇÃO COM VERSÃO
# ─────────────────────────────────────────────────────────────────────────────
print("\n💾 Salvando pipeline...")

os.makedirs('modelos', exist_ok=True)   # cria pasta se não existir
caminho = 'modelos/churn_v1.joblib'
joblib.dump(pipeline, caminho)

tamanho_kb = os.path.getsize(caminho) / 1024
print(f"   Arquivo: {caminho}")
print(f"   Tamanho: {tamanho_kb:.1f} KB")
print(f"   Contém : pré-processamento + modelo (tudo junto)")


# ─────────────────────────────────────────────────────────────────────────────
# 7. TESTE DE CARGA — simula o que a API vai fazer
# ─────────────────────────────────────────────────────────────────────────────
print("\n🔬 Teste de inferência (simula a API recebendo dados)...")

pipeline_carregado = joblib.load(caminho)   # carrega como a API faria

# Aluno de teste — como viria no body da requisição POST /predict
aluno_teste = pd.DataFrame([{
    'frequencia_mensal':     2,       # pouca frequência → alto risco
    'qtd_aulas_reagendadas': 5,       # muitos reagendamentos
    'dias_atraso_medio':     40.0,    # bastante atraso
    'modalidade':            'Salto'
}])

prob  = float(pipeline_carregado.predict_proba(aluno_teste)[0, 1])
risco = "ALTO" if prob >= 0.30 else "BAIXO"

print(f"   Dados do aluno: freq=2, reagend=5, atraso=40, modalidade=Salto")
print(f"   → prob_churn : {prob:.3f}")
print(f"   → risco      : {risco}")
print(f"   → modelo     : churn_v1")

# Categoria nova — teste do handle_unknown='ignore'
aluno_novo = pd.DataFrame([{
    'frequencia_mensal':     3,
    'qtd_aulas_reagendadas': 2,
    'dias_atraso_medio':     10.0,
    'modalidade':            'Dressage'   # NÃO estava no treino!
}])

prob_novo = float(pipeline_carregado.predict_proba(aluno_novo)[0, 1])
print(f"\n   Categoria nova 'Dressage' (não vista no treino):")
print(f"   → prob_churn : {prob_novo:.3f}  ✅ Não quebrou! (handle_unknown='ignore')")

print("\n" + "=" * 65)
print("✅ Exercício 4 concluído!")
print("   Próximo: ex05_fastapi_app.py — criar e testar a API")
print("=" * 65 + "\n")
