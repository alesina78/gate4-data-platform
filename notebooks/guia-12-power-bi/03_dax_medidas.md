# Medidas DAX — GATE4 Dashboard

> **Referência rápida** para o portfólio e entrevistas.  
> Cada medida inclui o SQL equivalente para quem vem do mundo Oracle/PostgreSQL.

---

## Conceitos fundamentais

| Conceito DAX | Analogia SQL | Quando usar |
|---|---|---|
| **Medida** | `SELECT SUM(...) GROUP BY <visual>` | Sempre que o número varia por filtro |
| **Coluna calculada** | `ALTER TABLE ... ADD COLUMN` | Categorias para agrupar/filtrar |
| **Contexto de filtro** | `WHERE` implícito do visual | Entender antes de qualquer `CALCULATE` |
| `CALCULATE()` | `SELECT ... WHERE outro_contexto` | Sobrescrever o filtro do visual |
| `VAR ... RETURN` | `WITH cte AS (...)` | Evitar recálculo, melhorar leitura |
| `DIVIDE(a, b)` | `CASE WHEN b = 0 THEN NULL ELSE a/b END` | Todo cálculo de percentual |

---

## Página 1 — Saúde Financeira

### Faturamento total
```dax
-- SQL: SELECT SUM(valor) FROM faturas
Faturamento =
    SUM ( fato_faturas[valor] )
```

### Faturamento mês anterior
```dax
-- SQL: WHERE mes = mes_atual - 1
Fat_Mes_Anterior =
    CALCULATE (
        [Faturamento],
        DATEADD ( dim_data[data], -1, MONTH )
    )
```
> ⚠️ **Requer** dim_data marcada como "Tabela de Datas" no Power BI.

### Variação MoM (Month over Month)
```dax
-- SQL: (atual - anterior) / anterior
Var_MoM =
    DIVIDE (
        [Faturamento] - [Fat_Mes_Anterior],
        [Fat_Mes_Anterior]
    )
-- Formatar como %: formato "▲0.0%;▼0.0%;—"
```

### Acumulado no ano (YTD)
```dax
-- SQL: WHERE data BETWEEN '2024-01-01' AND SYSDATE
Acumulado_Ano =
    TOTALYTD ( [Faturamento], dim_data[data] )
```

### Faturamento mesmo período ano anterior (SPLY)
```dax
Fat_Ano_Anterior =
    CALCULATE (
        [Faturamento],
        SAMEPERIODLASTYEAR ( dim_data[data] )
    )

Var_YoY =
    DIVIDE ( [Faturamento] - [Fat_Ano_Anterior], [Fat_Ano_Anterior] )
```

### Inadimplência %
```dax
-- SQL: SUM(valor) WHERE status = 'ATRASADA' / SUM(valor) total
Inadimplencia_Pct =
    DIVIDE (
        CALCULATE ( [Faturamento], fato_faturas[status] = "ATRASADA" ),
        [Faturamento]
    )
-- Formatar como: "0.0%"
```

### Contas a receber — faixas de atraso
```dax
-- SQL: SUM(valor) WHERE status = 'ATRASADA' AND dias_atraso BETWEEN 1 AND 30
AR_0_30d =
    CALCULATE (
        [Faturamento],
        fato_faturas[status] = "ATRASADA",
        fato_faturas[dias_atraso] >= 0,
        fato_faturas[dias_atraso] <= 30
    )

AR_31_60d =
    CALCULATE (
        [Faturamento],
        fato_faturas[status] = "ATRASADA",
        fato_faturas[dias_atraso] > 30,
        fato_faturas[dias_atraso] <= 60
    )

AR_60_mais =
    CALCULATE (
        [Faturamento],
        fato_faturas[status] = "ATRASADA",
        fato_faturas[dias_atraso] > 60
    )
```

---

## Página 2 — Alunos em Risco

### Alunos ativos (distintos)
```dax
-- SQL: SELECT COUNT(DISTINCT aluno_id) FROM aulas
Alunos_Ativos =
    DISTINCTCOUNT ( fato_aulas[aluno_id] )
```

### Alunos inativos — últimos 60 dias
```dax
-- SQL:
-- SELECT COUNT(*) FROM alunos a
-- WHERE NOT EXISTS (
--   SELECT 1 FROM aulas au
--   WHERE au.aluno_id = a.id AND au.data >= CURRENT_DATE - 60
-- )
Inativos_60d =
    VAR ref = MAX ( dim_data[data] )
    RETURN
    COUNTROWS (
        FILTER (
            dim_aluno,
            CALCULATE (
                COUNTROWS ( fato_aulas ),
                DATESINPERIOD ( dim_data[data], ref, -60, DAY )
            ) = 0
        )
    )

Pct_Inativos =
    DIVIDE ( [Inativos_60d], COUNTROWS ( dim_aluno ) )
```

### Alunos em risco alto (do modelo ML)
```dax
-- Lê a tabela gold.risco_churn que o pipeline Python grava
Alunos_Risco_Alto =
    CALCULATE (
        DISTINCTCOUNT ( risco_churn[aluno_id] ),
        risco_churn[faixa_risco] = "ALTO"
    )
```

---

## Página 3 — Ocupação

### Taxa de ocupação de baias
```dax
-- SQL: baias_ocupadas / total_baias
Ocupacao_Pct =
    DIVIDE (
        CALCULATE ( COUNTROWS ( fato_ocupacao ), fato_ocupacao[ocupada] = TRUE ),
        COUNTROWS ( fato_ocupacao )
    )
```

### Ocupação vs mesmo período semana anterior
```dax
Ocupacao_Semana_Ant =
    CALCULATE (
        [Ocupacao_Pct],
        DATEADD ( dim_data[data], -7, DAY )
    )
```

---

## Regras de ouro para entrevistas

1. **Medida vs Coluna calculada:** medida recalcula a cada filtro (número),
   coluna calculada é fixada na carga (categoria para agrupar).

2. **`CALCULATE` modifica o contexto:** é o `WHERE` que você escolhe,
   independente do que o visual já filtrou.

3. **`DIVIDE` sempre:** nunca use `/` direto em DAX — trata divisão por zero.

4. **`VAR` melhora tudo:** evita recalcular a mesma expressão, documenta a intenção.

5. **Query folding no Power Query:** mantenha as transformações que o PostgreSQL
   consegue fazer (JOIN, WHERE, GROUP BY). Não carregue tudo e filtre no Power BI.

6. **RLS por e-mail:** `[email_haras] = USERPRINCIPALNAME()` filtra toda a estrela
   automaticamente — cada haras vê só os seus dados.
