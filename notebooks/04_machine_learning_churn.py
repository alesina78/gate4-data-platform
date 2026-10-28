"""
=============================================================================
PROJETO: GATE4 - Transição de SQL para Pandas (Análise de Dados)
AULA 4: Machine Learning com scikit-learn - Prevendo o cancelamento de alunos
AUTOR: Alessandro Lesina Giordano
DESCRIÇÃO: Este script mostra o fluxo completo de um primeiro modelo de
           Machine Learning: preparar os dados (X e y), separar treino e teste,
           comparar com um modelo "bobo" (baseline), treinar, avaliar com as
           métricas certas, validar de forma robusta e traduzir para negócio.

ANTES DE RODAR (uma vez só, com o (.venv) ligado no terminal Git Bash):
    pip install scikit-learn

COMO EXECUTAR (na pasta do projeto, com o (.venv) ligado):
    python 04_machine_learning_churn.py

SAÍDA: imagens PNG na pasta "saidas/" e o modelo treinado em "modelos/".
=============================================================================
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    average_precision_score,
    classification_report,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.options.display.float_format = '{:.3f}'.format

MOSTRAR_JANELAS = False            # True = abre uma janela por gráfico (o script pausa até fechar)
PASTA_SAIDA = Path("saidas")
PASTA_MODELOS = Path("modelos")
PASTA_SAIDA.mkdir(exist_ok=True)
PASTA_MODELOS.mkdir(exist_ok=True)


def salvar(nome_arquivo):
    """Salva o gráfico atual em saidas/ e, se quiser, também mostra na tela."""
    caminho = PASTA_SAIDA / nome_arquivo
    plt.tight_layout()
    plt.savefig(caminho, dpi=120)
    print(f"  gráfico salvo em: {caminho}")
    if MOSTRAR_JANELAS:
        plt.show()
    plt.close()


def metricas(y_real, y_prev, y_prob, titulo):
    """Imprime as métricas principais de um modelo."""
    print(f"\n[{titulo}]")
    print(f"  Precision: {precision_score(y_real, y_prev, zero_division=0):.3f}")
    print(f"  Recall   : {recall_score(y_real, y_prev, zero_division=0):.3f}")
    if y_prob is not None:
        print(f"  ROC-AUC  : {roc_auc_score(y_real, y_prob):.3f}")
        print(f"  PR-AUC   : {average_precision_score(y_real, y_prob):.3f}")


# =============================================================================
# 1. A IDEIA DO MACHINE LEARNING (em termos de SQL)
# =============================================================================
# Programação tradicional (PL/SQL):  ENTRADA + REGRA  = SAÍDA
# Machine Learning:                  ENTRADA + SAÍDA  = REGRA (o "modelo")
#
# Você entrega ao algoritmo exemplos do passado (alunos que cancelaram e que
# ficaram) e ele DESCOBRE a regra que separa um grupo do outro.
#
#   X = as colunas explicativas (features)    -> as colunas do SELECT
#   y = o que queremos prever (target)        -> a coluna "resposta" (0 ou 1)
#
# Em engenharia de dados, a tabela com uma linha por aluno, features e target
# se chama ABT (Analytical Base Table). Aqui, vamos SIMULAR essa tabela.
print("=" * 70)
print("1. DADOS (ABT SIMULADA)")
print("=" * 70)

rng = np.random.default_rng(42)
N = 1500

plano = rng.choice(["Mensal", "Semestral", "Anual"], size=N, p=[0.60, 0.25, 0.15])
idade = rng.integers(8, 65, size=N)
tempo_casa_meses = rng.integers(1, 61, size=N)
aulas_90d = rng.poisson(lam=np.where(plano == "Mensal", 13, 10))
atraso_medio = np.where(rng.random(N) < 0.70, 0, np.round(rng.lognormal(2.3, 0.8, size=N)))
mensalidade = np.round(
    np.select([plano == "Mensal", plano == "Semestral"], [450.0, 420.0], default=380.0)
    + rng.normal(0, 30, size=N), 2
)

# ATENÇÃO: aqui NÓS definimos a regra que gera o cancelamento (para ter o que o
# modelo descobrir). No GATE4 real, essa regra é desconhecida: é isso que o
# modelo tenta aprender. Menos aulas, mais atraso e menos tempo de casa = mais risco.
z = (-1.2
     - 0.22 * (aulas_90d - 12)
     + 0.04 * atraso_medio
     - 0.02 * tempo_casa_meses
     + 0.5 * (plano == "Mensal"))
prob_real = 1 / (1 + np.exp(-z))                       # função sigmoide: transforma z em probabilidade (0 a 1)
cancelou = (rng.random(N) < prob_real).astype(int)     # sorteia quem cancelou (1) ou ficou (0)

df = pd.DataFrame({
    "aluno_id": np.arange(1, N + 1),
    "plano": plano,
    "idade": idade,
    "tempo_casa_meses": tempo_casa_meses,
    "aulas_90d": aulas_90d,
    "atraso_medio": atraso_medio,
    "mensalidade": mensalidade,
    "cancelou": cancelou,
})
print(df.head())

# Taxa de cancelamento   SQL: SELECT AVG(cancelou) FROM abt  /  GROUP BY cancelou
print("\nQuantidade por classe:")
print(df["cancelou"].value_counts())
taxa = df["cancelou"].mean()
print(f"\nTaxa de cancelamento: {taxa:.1%}  -> classes DESBALANCEADAS (poucos 1, muitos 0)")


# =============================================================================
# 2. X, y E A DIVISÃO TREINO / TESTE
# =============================================================================
# Regra de ouro: NUNCA avalie um modelo com os mesmos dados usados para treiná-lo.
# É como testar uma procedure em produção sem ter validado em homologação.
#   treino (80%): o algoritmo aprende
#   teste  (20%): "dados do futuro" que o modelo nunca viu
X = df.drop(columns=["aluno_id", "cancelou"])   # aluno_id é só identificador: não ajuda a prever
y = df["cancelou"]

X_treino, X_teste, y_treino, y_teste = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,     # deixa a divisão sempre igual (reprodutível)
    stratify=y,          # mantém a MESMA proporção de cancelamentos nos dois grupos
)
print(f"\nTreino: {len(X_treino)} alunos | Teste: {len(X_teste)} alunos")
print(f"Taxa de cancelamento no treino: {y_treino.mean():.1%} | no teste: {y_teste.mean():.1%}")


# =============================================================================
# 3. BASELINE: O MODELO "BOBO" (e a armadilha da acurácia)
# =============================================================================
# Todo modelo precisa ser comparado com um baseline. O mais simples: prever
# sempre a classe mais comum ("ninguém cancela").
print("\n" + "=" * 70)
print("3. BASELINE")
print("=" * 70)

baseline = DummyClassifier(strategy="most_frequent")
baseline.fit(X_treino, y_treino)
prev_base = baseline.predict(X_teste)
acuracia_base = (prev_base == y_teste).mean()
print(f"Acurácia do baseline: {acuracia_base:.1%}  (parece ótimo...)")
metricas(y_teste, prev_base, None, "Baseline - sempre prevê 'não cancela'")
print(f"\n=> Acertou {acuracia_base:.0%} dos casos e detectou ZERO cancelamentos. Para retenção, esse modelo é inútil.")
print("   Por isso NÃO usamos só acurácia: olhamos Recall e Precision.")


# =============================================================================
# 4. O PIPELINE: PRÉ-PROCESSAMENTO + MODELO NUM PACOTE SÓ
# =============================================================================
# Algoritmos só entendem números, então:
#   - colunas numéricas: padronizamos a escala (StandardScaler)
#   - coluna de texto (plano): viramos colunas 0/1 (OneHotEncoder)
#       SQL: é como  CASE WHEN plano = 'Mensal' THEN 1 ELSE 0 END  para cada plano.
# O Pipeline junta tudo: o que for "aprendido" (média, desvio) vem SÓ do treino,
# evitando VAZAMENTO DE DADOS (data leakage).
print("\n" + "=" * 70)
print("4. MODELOS")
print("=" * 70)

colunas_numericas = ["idade", "tempo_casa_meses", "aulas_90d", "atraso_medio", "mensalidade"]
colunas_texto = ["plano"]

preprocessamento = ColumnTransformer([
    ("num", StandardScaler(), colunas_numericas),
    ("cat", OneHotEncoder(handle_unknown="ignore"), colunas_texto),   # ignore = não quebra com plano novo
])

modelo_logistico = Pipeline([
    ("pre", preprocessamento),
    # class_weight="balanced": dá mais peso à classe rara (cancelou), compensando o desbalanceamento
    ("modelo", LogisticRegression(class_weight="balanced", max_iter=1000)),
])

modelo_floresta = Pipeline([
    ("pre", preprocessamento),
    ("modelo", RandomForestClassifier(
        n_estimators=200, max_depth=6, min_samples_leaf=10,
        class_weight="balanced", random_state=42,
    )),
])

resultados = {}
for nome, modelo in [("Regressão Logística", modelo_logistico), ("Random Forest", modelo_floresta)]:
    modelo.fit(X_treino, y_treino)                    # .fit = o modelo APRENDE com o treino
    prob = modelo.predict_proba(X_teste)[:, 1]        # probabilidade de cancelar (coluna da classe 1)
    prev = modelo.predict(X_teste)                    # decisão com o limiar padrão (0,5)
    resultados[nome] = (modelo, prob, prev)
    metricas(y_teste, prev, prob, nome)

# Relatório completo e matriz de confusão do modelo logístico
modelo, prob, prev = resultados["Regressão Logística"]
print("\nRelatório detalhado (Regressão Logística):")
print(classification_report(y_teste, prev, target_names=["ficou", "cancelou"]))

# Matriz de confusão:
#                   previu "ficou"       previu "cancelou"
# realmente ficou   acerto (VN)          alarme falso (FP)
# realmente saiu    PERDEU O ALUNO (FN)  acerto (VP)
ConfusionMatrixDisplay.from_predictions(y_teste, prev, display_labels=["ficou", "cancelou"], cmap="Blues")
plt.title("Matriz de confusão - Regressão Logística")
salvar("06_matriz_confusao.png")


# =============================================================================
# 5. O QUE O MODELO APRENDEU? (explicabilidade)
# =============================================================================
# Em negócio, "por quê" importa tanto quanto "quem". Nos coeficientes da regressão
# logística: sinal positivo = aumenta o risco de cancelar; negativo = reduz.
nomes_colunas = modelo.named_steps["pre"].get_feature_names_out()
coeficientes = pd.Series(modelo.named_steps["modelo"].coef_[0], index=nomes_colunas).sort_values()
print("\nCoeficientes (colunas numéricas já padronizadas, por isso comparáveis):")
print(coeficientes)

# Importância das variáveis na Random Forest (quanto cada coluna ajudou a separar os grupos)
floresta = resultados["Random Forest"][0]
importancia = pd.Series(
    floresta.named_steps["modelo"].feature_importances_,
    index=floresta.named_steps["pre"].get_feature_names_out(),
).sort_values(ascending=False)
print("\nImportância das variáveis (Random Forest):")
print(importancia.head(5))


# =============================================================================
# 6. VALIDAÇÃO CRUZADA: UMA NOTA MAIS CONFIÁVEL
# =============================================================================
# Um único corte treino/teste pode ser "fácil" ou "difícil" por sorte. A validação
# cruzada treina e testa 5 vezes, em fatias diferentes, e mostra a média e o desvio.
# Usamos o PIPELINE INTEIRO: o escalonamento é refeito dentro de cada fatia
# (sem vazamento).
print("\n" + "=" * 70)
print("6. VALIDAÇÃO CRUZADA (5 fatias, só nos dados de TREINO)")
print("=" * 70)

validacao = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv = cross_validate(
    modelo_logistico, X_treino, y_treino, cv=validacao,
    scoring=["recall", "precision", "average_precision"],
)
for metrica in ["recall", "precision", "average_precision"]:
    valores = cv[f"test_{metrica}"]
    print(f"  {metrica:18s}: média {valores.mean():.3f} | desvio {valores.std():.3f}")
print("  (desvio pequeno = o resultado é estável; grande = depende da sorte da divisão)")


# =============================================================================
# 7. DO MODELO PARA O NEGÓCIO: LIMIAR E LISTA DE CONTATO
# =============================================================================
# O modelo devolve uma PROBABILIDADE. Quem vira "alerta" depende do limiar:
#   limiar baixo -> pega mais cancelamentos (recall alto), mas gera mais ligações inúteis
#   limiar alto  -> poucas ligações, mas deixa escapar gente
print("\n" + "=" * 70)
print("7. NEGÓCIO")
print("=" * 70)

print("\nEfeito do limiar (modelo logístico, base de teste):")
linhas = []
for limiar in [0.3, 0.4, 0.5, 0.6, 0.7]:
    alerta = (prob >= limiar).astype(int)
    linhas.append({
        "limiar": limiar,
        "alunos_no_alerta": int(alerta.sum()),
        "precision": precision_score(y_teste, alerta, zero_division=0),
        "recall": recall_score(y_teste, alerta, zero_division=0),
    })
print(pd.DataFrame(linhas).to_string(index=False))

# Lista de contato: ordena do maior para o menor risco   SQL: ORDER BY prob DESC
teste = X_teste.copy()
teste["risco"] = prob
teste["cancelou_de_verdade"] = y_teste.values
teste = teste.sort_values("risco", ascending=False)

# LIFT: se a equipe liga só para os 20% de maior risco, quantos dos que sairiam são atingidos?
corte = int(len(teste) * 0.20)
captura = teste.head(corte)["cancelou_de_verdade"].sum() / teste["cancelou_de_verdade"].sum()
print(f"\nLigando para os 20% de maior risco ({corte} alunos), atingimos {captura:.0%} dos que cancelariam.")
print("Ligar para 20% ao acaso atingiria cerca de 20%. A diferença é o ganho do modelo (lift).")

print("\nTop 5 alunos de maior risco:")
print(teste[["plano", "aulas_90d", "atraso_medio", "tempo_casa_meses", "risco"]].head(5))

PrecisionRecallDisplay.from_predictions(y_teste, prob)
plt.title("Curva Precision x Recall - Regressão Logística")
salvar("07_curva_precision_recall.png")


# =============================================================================
# 8. ARMADILHA: VAZAMENTO DE DADOS (DATA LEAKAGE)
# =============================================================================
# Se uma coluna só existe DEPOIS do cancelamento, ela "entrega a resposta".
# Exemplo: "motivo de desligamento preenchido". O modelo parece incrível no
# notebook e fracassa em produção (no momento da previsão, o aluno ainda não saiu).
print("\n" + "=" * 70)
print("8. DEMONSTRAÇÃO DE VAZAMENTO")
print("=" * 70)

X_vazado = X.copy()
X_vazado["motivo_preenchido"] = ((y == 1) & (rng.random(N) < 0.95)).astype(int)   # quase = o alvo

Xv_treino, Xv_teste, yv_treino, yv_teste = train_test_split(
    X_vazado, y, test_size=0.20, random_state=42, stratify=y
)
pre_vazado = ColumnTransformer([
    ("num", StandardScaler(), colunas_numericas + ["motivo_preenchido"]),
    ("cat", OneHotEncoder(handle_unknown="ignore"), colunas_texto),
])
modelo_vazado = Pipeline([
    ("pre", pre_vazado),
    ("modelo", LogisticRegression(class_weight="balanced", max_iter=1000)),
]).fit(Xv_treino, yv_treino)
prob_v = modelo_vazado.predict_proba(Xv_teste)[:, 1]
metricas(yv_teste, modelo_vazado.predict(Xv_teste), prob_v, "Modelo COM vazamento")
print("\n=> Desempenho 'bom demais para ser verdade' é um alerta vermelho. Pergunte a cada coluna:")
print("   'eu saberia isso NO MOMENTO de fazer a previsão?'")


# =============================================================================
# 9. SALVANDO O MODELO (para a API da próxima etapa)
# =============================================================================
# O arquivo guarda o pré-processamento + o modelo juntos. Na API, basta carregar
# e chamar predict_proba, sem refazer nenhuma conta.
caminho_modelo = PASTA_MODELOS / "churn_v1.joblib"
joblib.dump(modelo_logistico, caminho_modelo)
print(f"\nModelo salvo em: {caminho_modelo}")
print("CUIDADO: só carregue arquivos .joblib/.pkl de fontes que você confia (podem executar código).")


# =============================================================================
# 10. EXERCÍCIOS (tente você mesmo, sem copiar)
# =============================================================================
# 1) Mude o limiar para 0.35 e calcule precision e recall. Que limiar você escolheria
#    se ligar para um aluno custa pouco, mas perder um aluno custa muito? Por quê?
# 2) Troque max_depth=6 por max_depth=3 e por 12 na Random Forest. O que acontece com
#    as métricas no TREINO e no TESTE? (pista: overfitting = decorar o treino)
# 3) Crie a feature "aulas_por_mes_de_casa = aulas_90d / (tempo_casa_meses + 1)" e
#    veja se o PR-AUC melhora. Lembre: toda feature nova só pode usar informação
#    disponível ANTES da previsão.
# 4) Rode a validação cruzada para a Random Forest e compare média e desvio com
#    a regressão logística.