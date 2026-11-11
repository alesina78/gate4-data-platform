# 🗄️ Guia 13 — SQL Avançado para Entrevistas

> **Trilha:** D — BI, SQL Avançado & Carreira · **Projeto:** GATE4 Data Platform  
> **Autor:** Alessandro Esina · [github.com/alesina78](https://github.com/alesina78)  
> **Pré-requisito:** Certificação Oracle SQL (1Z0-007) + 25 anos de SQL em produção ✅

---

## 🎯 Objetivo

Converter domínio Oracle/PL-SQL em respostas rápidas, seguras e bem explicadas
em entrevistas — com foco nas diferenças de sintaxe PostgreSQL e nos
8 padrões que mais caem.

---

## 📁 Arquivos

| Arquivo | Tema | Dificuldade |
|---|---|---|
| `ex15_8_padroes_gate4.sql` | Os 8 padrões completos: Oracle + PostgreSQL lado a lado | ⭐⭐⭐ |

---

## 🔴→🔵 Oracle → PostgreSQL (referência rápida)

| Oracle | PostgreSQL | Observação |
|---|---|---|
| `TRUNC(data, 'MM')` | `DATE_TRUNC('month', data)::date` | Cast com `::date` necessário |
| `SYSDATE` | `CURRENT_DATE` / `NOW()` | DATE vs TIMESTAMP |
| `NVL(col, 0)` | `COALESCE(col, 0)` | COALESCE também existe no Oracle |
| `CONNECT BY LEVEL <= n` | `generate_series(1, n)` | Para calendários e sequências |
| `ROWNUM` | `ROW_NUMBER() OVER(...)` ou `LIMIT` | ROWNUM não existe no PG |
| `ROWID` | `ctid` | Identificador físico da linha |
| `MONTHS_BETWEEN(d1,d2)` | `EXTRACT(MONTH FROM AGE(d1,d2))` | AGE() retorna intervalo |
| `SUM(CASE WHEN c THEN v END)` | `SUM(v) FILTER (WHERE c)` | FILTER é padrão SQL:2003 |
| `LISTAGG(col,',')` | `STRING_AGG(col, ',' ORDER BY col)` | Agregação de strings |
| `MERGE INTO` | `INSERT ... ON CONFLICT DO UPDATE` | Upsert no PostgreSQL |

---

## 🎯 Os 8 Padrões — resumo rápido

| # | Padrão | Dificuldade | Funções-chave |
|---|---|---|---|
| 1 | Top-N por grupo | Fácil | `DENSE_RANK() OVER (PARTITION BY)` |
| 2 | Gaps & Islands | Difícil | `ROW_NUMBER()` + subtração de intervalo |
| 3 | Quem NÃO fez X | Fácil | `NOT EXISTS` (nunca `NOT IN` com NULLs) |
| 4 | Coorte & Retenção | Difícil | `MIN(mes) OVER (PARTITION BY aluno_id)` |
| 5 | Acumulado & Média Móvel | Fácil | `SUM() OVER (ROWS BETWEEN)` |
| 6 | Remover Duplicados | Médio | `ROW_NUMBER()` + `ctid`/`ROWID` |
| 7 | Pivô | Médio | `FILTER (WHERE)` / `CASE WHEN` |
| 8 | Calendário sem lacunas | Fácil | `generate_series` / `CONNECT BY LEVEL` |

---

## ⚠️ Pegadinhas mais frequentes

| Pegadinha | Consequência | Solução |
|---|---|---|
| `NOT IN` com NULL na subconsulta | Retorna 0 linhas silenciosamente | Use `NOT EXISTS` |
| `RANK` em vez de `DENSE_RANK` | Pula posições em empate | Pergunte ao entrevistador como tratar empates |
| `RANGE` implícito com `ORDER BY` | Acumulado inconsistente com empates | Use `ROWS BETWEEN` explicitamente |
| Função na coluna do `WHERE` | Não usa índice (Seq Scan) | Reescreva como range sargável |
| `CONNECT BY` no PostgreSQL | Erro de sintaxe | Use `generate_series()` |

---

## 🎯 Roteiro de 5 passos para entrevista

```
① Repita o problema com suas palavras
② Pergunte: empates? NULLs? duplicatas? período?
③ Declare o padrão ("é top-N por grupo — uso janela com PARTITION BY")
④ Escreva e teste mentalmente com 3 linhas imaginárias
⑤ Comente desempenho (qual índice ajudaria, qual o plano esperado)

Pensar em voz alta vale mais do que acertar em silêncio.
```

---

## 🗺️ Trilha de estudos

```
Guia 13 — SQL Avançado para Entrevistas  ✅ Este módulo
Guia 12 — Power BI e Storytelling        🔜 Próximo
Guia 9  — Currículo, LinkedIn, Vagas     🔜 A seguir
Guia 17 — Vagas Reais e Simulados        🔜 Depois
```
