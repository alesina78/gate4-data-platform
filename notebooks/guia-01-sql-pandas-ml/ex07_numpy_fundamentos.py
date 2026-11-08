"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GATE4 Data Platform — Guia 4, Exercício 7                                  ║
║  Arquivo : ex07_numpy_fundamentos.py                                         ║
║  Tema    : NumPy — vetorização, estatísticas e equivalentes Oracle          ║
║  Autor   : Alessandro Esina                                                  ║
║  Projeto : github.com/alesina78/gate4-data-platform                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO
--------
Dominar as operações NumPy que substituem cursores e funções analíticas
Oracle — com exemplos reais dos dados do GATE4.

ANALOGIA CENTRAL
----------------
  Array NumPy   = coluna de uma tabela Oracle
  Vetorização   = operação SQL sobre o conjunto inteiro (sem LOOP/cursor)
  np.where()    = CASE WHEN com 2 saídas
  np.select()   = CASE WHEN com múltiplas saídas
  np.mean()     = AVG()      | np.median()     = MEDIAN()
  np.std(ddof=1)= STDDEV()   | np.percentile() = PERCENTILE_CONT()

COMO RODAR
----------
  source .venv/Scripts/activate
  pip install numpy pandas
  python ex07_numpy_fundamentos.py
"""

import numpy  as np
import pandas as pd
import time

print("=" * 65)
print("GATE4 — Exercício 7: NumPy Fundamentos")
print("=" * 65)


# ─────────────────────────────────────────────────────────────────────────────
# 1. ARRAYS — O QUE SÃO E COMO CRIAR
# ─────────────────────────────────────────────────────────────────────────────
print("\n📦 SEÇÃO 1 — Arrays NumPy")
print("─" * 65)

# Array 1D = uma coluna de tabela
# SQL equivalente: coluna "valor_mensalidade" da tabela alunos
mensalidades = np.array([350.0, 420.0, 300.0, 500.0, 380.0, 450.0, 290.0])

print(f"Array de mensalidades : {mensalidades}")
print(f"Tipo dos elementos    : {mensalidades.dtype}")    # float64 = NUMBER no Oracle
print(f"Número de elementos   : {mensalidades.shape}")   # (7,) = 7 linhas


# ─────────────────────────────────────────────────────────────────────────────
# 2. VETORIZAÇÃO — POR QUE É TUDO
# ─────────────────────────────────────────────────────────────────────────────
print("\n⚡ SEÇÃO 2 — Vetorização vs Loop")
print("─" * 65)
print("Analogia Oracle: SQL de conjunto vs cursor linha a linha")

rng   = np.random.default_rng(seed=42)
grande = rng.random(1_000_000)   # 1 milhão de números

# ── Loop (como um cursor Oracle — lento) ─────────────────────────────────────
inicio = time.perf_counter()
soma_loop = 0.0
for x in grande:
    soma_loop += x * 2
tempo_loop = time.perf_counter() - inicio

# ── Vetorizado (como SQL de conjunto — rápido) ────────────────────────────────
inicio = time.perf_counter()
soma_vet = (grande * 2).sum()
tempo_vet = time.perf_counter() - inicio

ganho = tempo_loop / tempo_vet
print(f"\n1 milhão de números:")
print(f"  Loop       : {tempo_loop:.4f}s")
print(f"  Vetorizado : {tempo_vet:.4f}s")
print(f"  Ganho      : {ganho:.0f}× mais rápido")
print(f"  Resultados iguais? {abs(soma_loop - soma_vet) < 0.001}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. ESTATÍSTICAS — EQUIVALENTES ORACLE
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 SEÇÃO 3 — Estatísticas (equivalentes Oracle)")
print("─" * 65)

# Dados de dias de atraso — distribuição assimétrica (cauda longa)
# A maioria paga em dia; poucos atrasam muito
atrasos = np.array([0,0,0,0,0,0,0,5,8,0,0,0,15,0,0,45,0,0,0,90,0,0,0,180,0])

print(f"\nDados de atraso: {atrasos}")
print()

# np.mean() = AVG(dias_atraso) no Oracle
media = np.mean(atrasos)
print(f"AVG(dias_atraso)              = {media:.1f} dias  → np.mean(atrasos)")

# np.median() = MEDIAN(dias_atraso) no Oracle
mediana = np.median(atrasos)
print(f"MEDIAN(dias_atraso)           = {mediana:.1f} dias  → np.median(atrasos)")
print(f"  → Mediana melhor representa o aluno típico (paga em dia)")
print(f"  → Média ({media:.1f}d) é puxada pelos atrasos grandes")

# np.std(ddof=1) = STDDEV(dias_atraso) no Oracle
# ddof=1 = amostral (N-1), igual ao Oracle; sem ddof=1 usa N (populacional)
desvio = np.std(atrasos, ddof=1)
print(f"\nSTDDEV(dias_atraso)           = {desvio:.1f} dias  → np.std(atrasos, ddof=1)")
print(f"  → ddof=1 é OBRIGATÓRIO para resultado igual ao Oracle!")

# np.percentile() = PERCENTILE_CONT() no Oracle
p25, p75, p90 = np.percentile(atrasos, [25, 75, 90])
print(f"\nPERCENTILE_CONT(0.25)         = {p25:.0f} dias  → np.percentile(atrasos, 25)")
print(f"PERCENTILE_CONT(0.75)         = {p75:.0f} dias  → np.percentile(atrasos, 75)")
print(f"PERCENTILE_CONT(0.90)         = {p90:.0f} dias  → np.percentile(atrasos, 90)")
print(f"IQR (Q3-Q1)                   = {p75-p25:.0f} dias")


# ─────────────────────────────────────────────────────────────────────────────
# 4. np.where() — CASE WHEN COM 2 SAÍDAS
# ─────────────────────────────────────────────────────────────────────────────
print("\n🔀 SEÇÃO 4 — np.where() = CASE WHEN com 2 saídas")
print("─" * 65)

# SQL: CASE WHEN mensalidade >= 400 THEN 'Premium' ELSE 'Básico' END
faixa = np.where(mensalidades >= 400, 'Premium', 'Básico')
print(f"Mensalidades : {mensalidades}")
print(f"Faixas       : {faixa}")
print(f"\nSQL: CASE WHEN valor >= 400 THEN 'Premium' ELSE 'Básico' END")

# SQL: CASE WHEN dias_atraso = 0 THEN 'Em dia' ELSE 'Atrasado' END
status = np.where(atrasos == 0, 'Em dia', 'Atrasado')
em_dia_pct = (atrasos == 0).mean() * 100
print(f"\nStatus de atraso: {np.unique(status, return_counts=True)}")
print(f"Percentual em dia: {em_dia_pct:.0f}%")


# ─────────────────────────────────────────────────────────────────────────────
# 5. np.select() — CASE WHEN COM MÚLTIPLAS SAÍDAS
# ─────────────────────────────────────────────────────────────────────────────
print("\n🎯 SEÇÃO 5 — np.select() = CASE WHEN com múltiplas saídas")
print("─" * 65)

# SQL:
# CASE WHEN dias_atraso = 0   THEN 'Em dia'
#      WHEN dias_atraso <= 15 THEN 'Até 15 dias'
#      WHEN dias_atraso <= 60 THEN 'Até 60 dias'
#      ELSE                        'Mais de 60 dias'
# END AS faixa_atraso

condicoes = [
    atrasos == 0,       # WHEN dias_atraso = 0
    atrasos <= 15,      # WHEN dias_atraso <= 15
    atrasos <= 60,      # WHEN dias_atraso <= 60
]
rotulos = [
    'Em dia',           # THEN 'Em dia'
    'Até 15 dias',      # THEN 'Até 15 dias'
    'Até 60 dias',      # THEN 'Até 60 dias'
]
# A ORDEM IMPORTA: a primeira condição verdadeira vence (igual ao CASE WHEN)
faixa_atraso = np.select(condicoes, rotulos, default='Mais de 60 dias')

print("Dias de atraso → faixa:")
for dias, faixa in zip(atrasos, faixa_atraso):
    print(f"  {dias:>4} dias → {faixa}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. DISTRIBUIÇÕES PARA DADOS SIMULADOS
# ─────────────────────────────────────────────────────────────────────────────
print("\n🎲 SEÇÃO 6 — Distribuições NumPy para dados do GATE4")
print("─" * 65)
print("Analogia: como o M0 (gerador) usa distribuições para simular dados reais")

rng = np.random.default_rng(seed=42)

# Poisson: contagem de eventos discretos (aulas, visitas ao haras)
# lam = média esperada de eventos
aulas_mes = rng.poisson(lam=10, size=50)   # média de 10 aulas por mês
print(f"\nAulas/mês (Poisson lam=10):")
print(f"  Média    : {aulas_mes.mean():.1f}  (esperado: 10)")
print(f"  Min/Max  : {aulas_mes.min()} / {aulas_mes.max()}")

# Lognormal: valores positivos com cauda longa (dias de atraso, faturamento)
# Usada no M0 para gerar dias_atraso realistas
atrasos_sim = np.round(rng.lognormal(mean=2.3, sigma=0.8, size=50))
print(f"\nDias de atraso (Lognormal mean=2.3, sigma=0.8):")
print(f"  Média    : {atrasos_sim.mean():.1f} dias")
print(f"  Mediana  : {np.median(atrasos_sim):.0f} dias")
print(f"  P90      : {np.percentile(atrasos_sim, 90):.0f} dias")
print(f"  → Lognormal gera cauda longa realista (igual a dados reais de inadimplência)")


# ─────────────────────────────────────────────────────────────────────────────
# 7. EXERCÍCIOS PROPOSTOS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("🟡 EXERCÍCIOS PROPOSTOS (implemente abaixo)")
print("=" * 65)
print("""
1. Crie um array com 100 mensalidades aleatórias entre R$300 e R$600.
   Calcule: média, mediana, desvio padrão (amostral) e P90.
   SQL: SELECT AVG(val), MEDIAN(val), STDDEV(val), PERCENTILE_CONT(0.9) FROM t

2. Use np.where() para classificar cada mensalidade em 'Abaixo da média'
   ou 'Acima da média' dinamicamente (usando o np.mean() do array).
   SQL: CASE WHEN val >= AVG(val) OVER () THEN 'Acima' ELSE 'Abaixo' END

3. Use np.select() para criar 4 faixas de mensalidade:
   'Básico' (< 350), 'Standard' (350-449), 'Premium' (450-549), 'VIP' (≥ 550)
   SQL: CASE WHEN val < 350 THEN 'Básico' WHEN ... END

4. Compare o tempo de loop vs vetorizado para somar todas as mensalidades
   multiplicadas por 1.1 (reajuste de 10%).
""")

print("✅ Exercício 7 concluído!")
print("   Próximo: ex08_eda_completo_gate4.py\n")
