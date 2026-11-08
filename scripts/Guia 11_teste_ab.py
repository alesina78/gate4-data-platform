"""
Guia 11 — Laboratório Avançado de Estatística Aplicada & Testes A/B (GATE4 Data Platform)
==========================================================================================
Este script implementa uma suíte de testes estatísticos e simulações monte carlo completas
para validação de hipóteses de negócio e modelos de Machine Learning no projeto GATE4.

Tópicos Cobertos:
1. Teste Z de Duas Proporções (Caso de Negócio: Lembrete WhatsApp)
2. Cálculo Formal de Tamanho de Amostra & Poder Estatístico (NormalIndPower)
3. Intervalo de Confiança via Bootstrap Não-Paramétrico (5.000 reamostragens)
4. Simulação de Viés Amostral: Paradoxo de Simpson (Envio Não-Aleatório)
5. Simulação de Regressão à Média (Efeito de Falsas Melhorias)
6. Problema de Múltiplos Testes de Hipótese & Correção de Bonferroni
7. Avaliação de Incerteza em Métricas de ML (Bootstrap de Recall de Churn)
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint, proportion_effectsize
from statsmodels.stats.power import NormalIndPower
from sklearn.metrics import recall_score


def cenario_1_teste_z_proporcoes(x_a: int, n_a: int, x_b: int, n_b: int, alpha: float = 0.05):
    """
    Executa o Teste Z de duas proporções para comparar o Grupo Controle (A) vs Tratamento (B).
    
    Caso de Negócio GATE4:
    - Grupo A (Controle): Sem lembrete de cobrança via WhatsApp antes do vencimento.
    - Grupo B (Tratamento): Com lembrete via WhatsApp.
    - Métrica: Taxa de Inadimplência / Atraso na Fatura.
    """
    print("\n" + "="*80)
    print("1. TESTE Z DE DUAS PROPORÇÕES (Lembrete WhatsApp GATE4)")
    print("="*80)
    
    p_a = x_a / n_a
    p_b = x_b / n_b
    diff_obs = p_a - p_b
    
    print(f"Grupo A (Controle):    {x_a}/{n_a} atrasos ({p_a:.2%})")
    print(f"Grupo B (Tratamento):  {x_b}/{n_b} atrasos ({p_b:.2%})")
    print(f"Diferença Observada (A - B): {diff_obs*100:.2f} p.p. (redução de {((p_a - p_b)/p_a):.2%})")
    
    # Executa Teste Z bicaudal com statsmodels
    count = np.array([x_a, x_b])
    nobs = np.array([n_a, n_b])
    z_stat, p_value = proportions_ztest(count, nobs, alternative='two-sided')
    
    # IC 95% analítico para cada grupo (Método de Wilson)
    ci_a_low, ci_a_high = proportion_confint(x_a, n_a, alpha=alpha, method='wilson')
    ci_b_low, ci_b_high = proportion_confint(x_b, n_b, alpha=alpha, method='wilson')
    
    # IC 95% analítico para a DIFERENÇA de proporções (Aproximação Normal)
    se_diff = np.sqrt((p_a * (1 - p_a) / n_a) + (p_b * (1 - p_b) / n_b))
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_diff_low = diff_obs - z_crit * se_diff
    ci_diff_high = diff_obs + z_crit * se_diff
    
    print(f"\nEstatística Z: {z_stat:.4f}")
    print(f"p-valor:       {p_value:.4f}")
    print(f"IC 95% Grupo A (Wilson):    [{ci_a_low:.2%}, {ci_a_high:.2%}]")
    print(f"IC 95% Grupo B (Wilson):    [{ci_b_low:.2%}, {ci_b_high:.2%}]")
    print(f"IC 95% da Diferença (A - B): [{ci_diff_low*100:.2f} p.p., {ci_diff_high*100:.2f} p.p.]")
    
    print("\n[Conclusão de Negócio]:")
    if p_value < alpha:
        print(f"-> ESTATISTICAMENTE SIGNIFICATIVO (p < {alpha}). O lembrete reduz a inadimplência.")
    else:
        print(f"-> NÃO SIGNIFICATIVO (p >= {alpha}). O IC inclui zero [{ci_diff_low*100:.2f}%, {ci_diff_high*100:.2f}%].")
        print("   Conclusão honesta: A amostra é pequena para confirmar se o efeito é real ou apenas ruído.")
        
    return p_value, (ci_diff_low, ci_diff_high)


def cenario_2_tamanho_amostra_e_poder(p1: float, p2: float, alpha: float = 0.05, power: float = 0.80):
    """
    Calcula o tamanho mínimo de amostra necessário por grupo (N) para detectar uma alteração
    de p1 para p2 com um determinado Poder Estatístico (1 - Beta) e nível de significância (Alpha).
    """
    print("\n" + "="*80)
    print("2. CÁLCULO DE TAMANHO DE AMOSTRA E PODER ESTATÍSTICO")
    print("="*80)
    
    # Tamanho do efeito h de Cohen para proporções
    h = proportion_effectsize(p1, p2)
    
    analysis = NormalIndPower()
    n_req = analysis.solve_power(effect_size=h, alpha=alpha, power=power, ratio=1.0)
    n_req_rounded = int(np.ceil(n_req))
    
    print(f"Taxa Base Esperada (Sem Lembrete): {p1:.2%}")
    print(f"Taxa Alvo com Lembrete:            {p2:.2%}")
    print(f"Efeito Adotado (Queda Absoluta):   {(p1 - p2)*100:.2f} p.p.")
    print(f"Nível de Significância (Alpha):    {alpha:.2%}")
    print(f"Poder Estatístico Alvo (1 - Beta): {power:.2%}")
    print(f"\n-> Tamanho de Amostra Mínimo Necessário: {n_req_rounded} alunos por grupo (Total = {n_req_rounded * 2})")
    
    # Simula o poder real obtido se tivéssemos apenas 120 alunos por grupo
    power_small_sample = analysis.solve_power(effect_size=h, nobs1=120, alpha=alpha, ratio=1.0)
    print(f"-> ALERTA: Com apenas 120 alunos por grupo, o Poder Estatístico real é de apenas {power_small_sample:.2%}.")
    print("   Isso significa que há {(1 - power_small_sample):.2%} de chance de o teste FALHAR em detectar um efeito real (Erro Tipo II).")


def cenario_3_bootstrap_ic(x_a: int, n_a: int, x_b: int, n_b: int, n_bootstrap: int = 5000, seed: int = 42):
    """
    Realiza o cálculo do Intervalo de Confiança por Bootstrap Não-Paramétrico.
    Útil quando não podemos assumir a distribuição normal teórica.
    """
    print("\n" + "="*80)
    print("3. BOOTSTRAP NÃO-PARAMÉTRICO (5.000 Reamostragens)")
    print("="*80)
    
    rng = np.random.default_rng(seed)
    
    # Constrói os vetores originais de 0s e 1s
    grupo_a = np.r_[np.ones(x_a), np.zeros(n_a - x_a)]
    grupo_b = np.r_[np.ones(x_b), np.zeros(n_b - x_b)]
    
    diferencas_bootstrap = []
    for _ in range(n_bootstrap):
        sample_a = rng.choice(grupo_a, size=n_a, replace=True)
        sample_b = rng.choice(grupo_b, size=n_b, replace=True)
        diferencas_bootstrap.append(sample_a.mean() - sample_b.mean())
        
    diferencas_bootstrap = np.array(diferencas_bootstrap)
    
    # Percentis 2.5% e 97.5% para o IC de 95%
    ic_boot_low, ic_boot_high = np.percentile(diferencas_bootstrap, [2.5, 97.5])
    diff_media_boot = diferencas_bootstrap.mean()
    
    print(f"Diferença Média Bootstrap:          {diff_media_boot*100:.2f} p.p.")
    print(f"IC 95% Bootstrap (Percentil 2.5-97.5): [{ic_boot_low*100:.2f} p.p., {ic_boot_high*100:.2f} p.p.]")
    
    if ic_boot_low <= 0 <= ic_boot_high:
        print("-> O Intervalo de Confiança Bootstrap engloba o ZERO. Não há significância estatística a 95%.")
    else:
        print("-> O Intervalo de Confiança Bootstrap EXCLUI o zero. Diferença estatisticamente significativa!")


def cenario_4_paradoxo_de_simpson():
    """
    Demonstra como o envio não-aleatório (sem sorteio) gera viés de seleção e inverte a conclusão.
    """
    print("\n" + "="*80)
    print("4. PARADOXO DE SIMPSON (Perigo do Envio Sem Sorteio Aleatório)")
    print("="*80)
    
    # Simulação:
    # Pontuais: A (4 atrasos em 80 = 5%), B (0 atrasos em 20 = 0%) -> B é melhor
    # Crônicos: A (12 atrasos em 20 = 60%), B (40 atrasos em 80 = 50%) -> B é melhor
    # Sem sorteio, o grupo B recebeu 80% de alunos crônicos!
    
    df_simpson = pd.DataFrame([
        {"Perfil": "Pontual", "Grupo": "A (Sem Lembrete)", "Total": 80, "Atrasos": 4, "Taxa": 0.05},
        {"Perfil": "Pontual", "Grupo": "B (Com Lembrete)", "Total": 20, "Atrasos": 0, "Taxa": 0.00},
        {"Perfil": "Crônico", "Grupo": "A (Sem Lembrete)", "Total": 20, "Atrasos": 12, "Taxa": 0.60},
        {"Perfil": "Crônico", "Grupo": "B (Com Lembrete)", "Total": 80, "Atrasos": 40, "Taxa": 0.50},
    ])
    
    totais = df_simpson.groupby("Grupo")[["Total", "Atrasos"]].sum()
    totais["Taxa Agregada"] = totais["Atrasos"] / totais["Total"]
    
    print("Desagregação por Segmento:")
    print(df_simpson.to_string(index=False))
    
    print("\nAgregação Total (Sem considerar o perfil):")
    print(totais)
    
    print("\n[Lição Prática]:")
    print("-> No total agrupado, B parece PIOR (40% de atraso vs 16% em A).")
    print("-> Mas dentro de CADA subgrupo, B é MELHOR!")
    print("   Isso ocorre porque o lembrete foi enviado predominantemente para quem já atrasava.")
    print("   SEM SORTEIO ALEATÓRIO, mede-se viés de seleção, não o efeito causal do lembrete!")


def cenario_5_regressao_a_media(seed: int = 42):
    """
    Demonstra como selecionar apenas os piores clientes gera uma falsa sensação de melhoria.
    """
    print("\n" + "="*80)
    print("5. REGRESSÃO À MÉDIA (Melhoria Fictícia sem Intervenção)")
    print("="*80)
    
    rng = np.random.default_rng(seed)
    n_alunos = 500
    
    # Mês 1: Atrasos simulados com um componente aleatório alto
    base_atraso = rng.exponential(scale=5, size=n_alunos)
    ruido_m1 = rng.normal(loc=0, scale=4, size=n_alunos)
    atraso_m1 = np.maximum(0, base_atraso + ruido_m1)
    
    # Mês 2: Mesmo comportamento base, novo ruído aleatório (SEM NENHUMA INTERVENÇÃO)
    ruido_m2 = rng.normal(loc=0, scale=4, size=n_alunos)
    atraso_m2 = np.maximum(0, base_atraso + ruido_m2)
    
    # Seleciona os 20% piores do Mês 1
    corte_20pct = np.percentile(atraso_m1, 80)
    indices_piores = np.where(atraso_m1 >= corte_20pct)[0]
    
    media_piores_m1 = atraso_m1[indices_piores].mean()
    media_piores_m2 = atraso_m2[indices_piores].mean()
    
    media_geral_m1 = atraso_m1.mean()
    media_geral_m2 = atraso_m2.mean()
    
    print(f"Média Geral da Turma - Mês 1: {media_geral_m1:.2f} dias | Mês 2: {media_geral_m2:.2f} dias")
    print(f"Os 20% Piores no Mês 1 - Atraso Média Mês 1: {media_piores_m1:.2f} dias")
    print(f"Os Mesmos Alunos no Mês 2 (SEM Lembrete):    {media_piores_m2:.2f} dias")
    print(f"Queda 'Natural' observada: {(media_piores_m1 - media_piores_m2):.2f} dias ({(media_piores_m2/media_piores_m1 - 1):.2%})")
    
    print("\n[Lição Prática]:")
    print("-> Os piores alunos melhoraram SOZINHOS apenas por variação estatística (regressão à média).")
    print("   Se você enviar WhatsApp só para eles e a dívida cair, NÃO significa que o WhatsApp funcionou!")


def cenario_6_multiplos_testes_bonferroni(n_metricas: int = 20, alpha_base: float = 0.05, seed: int = 42):
    """
    Demonstra a inflação de falsos positivos ao testar múltiplas métricas simultaneamente.
    """
    print("\n" + "="*80)
    print("6. MÚLTIPLOS TESTES DE HIPÓTESE & CORREÇÃO DE BONFERRONI")
    print("="*80)
    
    prob_ao_menos_um_falso_positivo = 1 - (1 - alpha_base)**n_metricas
    alpha_bonferroni = alpha_base / n_metricas
    
    print(f"Número de Métricas Testadas em Simultâneo: {n_metricas}")
    print(f"Nível de Significância Individual (Alpha):   {alpha_base:.2%}")
    print(f"Probabilidade TEÓRICA de pelo menos 1 Falso Positivo (Sem Correção): {prob_ao_menos_um_falso_positivo:.2%}")
    print(f"Alpha Corrigido por Bonferroni (Alpha / K):                        {alpha_bonferroni:.4%}")
    
    # Simulação Monte Carlo com 1.000 experimentos sem efeito real
    rng = np.random.default_rng(seed)
    n_exp = 1000
    falsos_positivos_sem_corr = 0
    falsos_positivos_com_corr = 0
    
    for _ in range(n_exp):
        p_valores = []
        for _ in range(n_metricas):
            # Gera dois grupos idênticos (sem efeito)
            g1 = rng.binomial(n=1, p=0.15, size=200)
            g2 = rng.binomial(n=1, p=0.15, size=200)
            _, p = proportions_ztest([g1.sum(), g2.sum()], [200, 200])
            p_valores.append(p)
            
        p_min = min(p_valores)
        if p_min < alpha_base:
            falsos_positivos_sem_corr += 1
        if p_min < alpha_bonferroni:
            falsos_positivos_com_corr += 1
            
    print(f"\n[Resultado da Simulação de 1.000 Experimentos sem efeito]:")
    print(f"-> Experimentos com pelo menos 1 'Achado Falso' (Sem Correção): {falsos_positivos_sem_corr/n_exp:.2%}")
    print(f"-> Experimentos com pelo menos 1 'Achado Falso' (Com Bonferroni):  {falsos_positivos_com_corr/n_exp:.2%}")


def cenario_7_bootstrap_metricas_ml(seed: int = 42):
    """
    Aplica Bootstrap para medir a incerteza do RECALL em um modelo de Machine Learning (Churn GATE4).
    """
    print("\n" + "="*80)
    print("7. INCERTEZA EM MÉTRICAS DE MACHINE LEARNING (Bootstrap no Recall de Churn)")
    print("="*80)
    
    rng = np.random.default_rng(seed)
    
    # Simulando um conjunto de teste pequeno de Churn (30 casos positivos reais)
    y_true = np.ones(30)
    # Modelo acertou 21 casos -> Recall pontual = 70.0%
    y_pred = np.r_[np.ones(21), np.zeros(9)]
    
    recall_pontual = recall_score(y_true, y_pred)
    
    recalls_boot = []
    for _ in range(2000):
        idx = rng.integers(0, len(y_true), size=len(y_true))
        recalls_boot.append(recall_score(y_true[idx], y_pred[idx]))
        
    ic_low, ic_high = np.percentile(recalls_boot, [2.5, 97.5])
    
    print(f"Número de Clientes em Churn no Conjunto de Teste: {len(y_true)}")
    print(f"Recall Observado do Modelo:                        {recall_pontual:.2%}")
    print(f"Intervalo de Confiança 95% do Recall (Bootstrap):  [{ic_low:.2%}, {ic_high:.2%}]")
    
    print("\n[Aplicação no Projeto GATE4]:")
    print("-> Em bases pequenas, o recall varia imenso (neste exemplo, de {:.0f}% a {:.0f}%).".format(ic_low*100, ic_high*100))
    print("-> Se o Modelo A tem Recall 70% e o Modelo B tem Recall 75%, essa diferença PODE SER APENAS RUÍDO!")


if __name__ == "__main__":
    print("="*80)
    print("      GATE4 DATA PLATFORM — EXECUÇÃO COMPLETA DO GUIA 11 (ESTATÍSTICA APLICADA)")
    print("="*80)
    
    # 1. Executa o Teste Z com os dados fictícios do Guia 11 (18/120 vs 9/115)
    cenario_1_teste_z_proporcoes(x_a=18, n_a=120, x_b=9, n_b=115)
    
    # 2. Tamanho de Amostra Mínimo
    cenario_2_tamanho_amostra_e_poder(p1=0.15, p2=0.08)
    
    # 3. IC via Bootstrap
    cenario_3_bootstrap_ic(x_a=18, n_a=120, x_b=9, n_b=115)
    
    # 4. Paradoxo de Simpson
    cenario_4_paradoxo_de_simpson()
    
    # 5. Regressão à Média
    cenario_5_regressao_a_media()
    
    # 6. Múltiplos Testes
    cenario_6_multiplos_testes_bonferroni()
    
    # 7. Incerteza no ML
    cenario_7_bootstrap_metricas_ml()
    
    print("\n" + "="*80)
    print("Execução finalizada com sucesso! Todos os testes estatísticos foram validados.")
    print("="*80)