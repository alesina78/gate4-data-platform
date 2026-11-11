-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  GATE4 Data Platform — Guia 13, Exercício 15                            ║
-- ║  Arquivo : ex15_8_padroes_gate4.sql                                     ║
-- ║  Tema    : Os 8 padrões SQL que mais caem — Oracle e PostgreSQL         ║
-- ║  Autor   : Alessandro Esina                                              ║
-- ║  Projeto : github.com/alesina78/gate4-data-platform                     ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- OBJETIVO
-- --------
-- Referência completa dos 8 padrões SQL mais cobrados em entrevistas,
-- aplicados às tabelas reais do GATE4, com versões Oracle e PostgreSQL
-- lado a lado e explicação do raciocínio para verbalizar.
--
-- COMO USAR
-- ---------
-- 1. Rode no Postgres local do GATE4 (substitua nomes de colunas se necessário)
-- 2. Para cada padrão: leia o enunciado, feche o arquivo, escreva você mesmo
-- 3. Depois compare com a solução aqui
-- 4. Use o simulador do Guia HTML para treinar com timer
--
-- TABELAS DO GATE4 USADAS
-- -----------------------
--   alunos   (id, nome, modalidade, plano, ativo, dt_matricula, dt_cancelamento)
--   aulas    (id, aluno_id, instrutor_id, data_aula, modalidade, realizada, reagendada)
--   faturas  (id, aluno_id, valor, vencimento, pago_em, esta_atrasada)


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 1 · TOP-N POR GRUPO
-- Pergunta: "Liste os 3 alunos que mais pagaram em cada modalidade do GATE4"
-- ════════════════════════════════════════════════════════════════════════════
-- Raciocínio (diga em voz alta):
-- "É top-N por grupo — uso DENSE_RANK com PARTITION BY modalidade.
--  DENSE_RANK porque com empate todos devem aparecer (1,2,2,3).
--  Se quiser exatamente 3 sem empate, uso ROW_NUMBER."

-- ── Oracle ──────────────────────────────────────────────────────────────────
SELECT * FROM (
    SELECT
        a.modalidade,
        a.id                                        aluno_id,
        a.nome,
        SUM(f.valor)                                total_pago,
        DENSE_RANK() OVER (
            PARTITION BY a.modalidade
            ORDER BY SUM(f.valor) DESC
        )                                           rk
    FROM faturas f
    JOIN alunos  a ON a.id = f.aluno_id
    GROUP BY a.modalidade, a.id, a.nome
) t
WHERE rk <= 3
ORDER BY modalidade, rk;

-- ── PostgreSQL (mesma lógica, CTE para legibilidade) ────────────────────────
WITH ranked AS (
    SELECT
        a.modalidade,
        a.id                                        aluno_id,
        a.nome,
        SUM(f.valor)                                total_pago,
        DENSE_RANK() OVER (
            PARTITION BY a.modalidade
            ORDER BY SUM(f.valor) DESC
        )                                           rk
    FROM faturas f
    JOIN alunos  a ON a.id = f.aluno_id
    GROUP BY a.modalidade, a.id, a.nome
)
SELECT * FROM ranked WHERE rk <= 3 ORDER BY modalidade, rk;

-- ⚠️  PEGADINHA DE ENTREVISTA: ROW_NUMBER vs RANK vs DENSE_RANK
-- ROW_NUMBER : 1,2,3,4    → sem empate, corta exato em N
-- RANK       : 1,2,2,4    → empata e PULA posição 3
-- DENSE_RANK : 1,2,2,3    → empata SEM pular (mais justo para top-N)
-- Sempre pergunte: "Como tratar empates?"


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 2 · GAPS & ISLANDS (Sequências Consecutivas)
-- Pergunta: "Liste alunos com 3 ou mais meses consecutivos de pagamento"
-- ════════════════════════════════════════════════════════════════════════════
-- Raciocínio (diga em voz alta):
-- "Em meses consecutivos, (mês - número_da_linha) é constante.
--  ROW_NUMBER enumera os meses de cada aluno. Subtraindo o ordinal do mês,
--  meses na mesma sequência têm o mesmo 'grp'. Depois GROUP BY + HAVING >= 3."

-- ── Oracle ──────────────────────────────────────────────────────────────────
WITH meses AS (
    SELECT DISTINCT
        aluno_id,
        TRUNC(pago_em, 'MM')                        mes
    FROM faturas
    WHERE pago_em IS NOT NULL
),
grupos AS (
    SELECT
        aluno_id,
        mes,
        mes - ROW_NUMBER() OVER (
            PARTITION BY aluno_id ORDER BY mes
        ) * INTERVAL '1' MONTH                      grp
    FROM meses
)
SELECT
    aluno_id,
    MIN(mes)    inicio,
    MAX(mes)    fim,
    COUNT(*)    meses_seguidos
FROM grupos
GROUP BY aluno_id, grp
HAVING COUNT(*) >= 3
ORDER BY aluno_id, inicio;

-- ── PostgreSQL ──────────────────────────────────────────────────────────────
WITH meses AS (
    SELECT DISTINCT
        aluno_id,
        DATE_TRUNC('month', pago_em)::date          mes
    FROM faturas
    WHERE pago_em IS NOT NULL
),
grupos AS (
    SELECT
        aluno_id,
        mes,
        (mes - (ROW_NUMBER() OVER (
            PARTITION BY aluno_id ORDER BY mes
        ) * INTERVAL '1 month')::integer)           grp
        -- Alternativa mais legível:
        -- mes - make_interval(months => ROW_NUMBER() OVER (...))
    FROM meses
)
SELECT
    aluno_id,
    MIN(mes)    inicio,
    MAX(mes)    fim,
    COUNT(*)    meses_seguidos
FROM grupos
GROUP BY aluno_id, grp
HAVING COUNT(*) >= 3
ORDER BY aluno_id, inicio;


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 3 · "QUEM NÃO FEZ X" — NOT EXISTS
-- Pergunta: "Liste alunos sem nenhuma aula nos últimos 60 dias"
-- ════════════════════════════════════════════════════════════════════════════
-- Raciocínio: "Existem 3 formas. Prefiro NOT EXISTS:
--   seguro com NULLs, sargável, e deixa clara a intenção."

-- ── Oracle ──────────────────────────────────────────────────────────────────
-- ✅ NOT EXISTS (preferido)
SELECT a.id, a.nome, a.modalidade
FROM alunos a
WHERE a.ativo = 1
  AND NOT EXISTS (
      SELECT 1 FROM aulas x
      WHERE x.aluno_id = a.id
        AND x.data_aula >= SYSDATE - 60
  );

-- ⚠️  NOT IN: perigoso com NULLs
-- Se qualquer linha de aulas.aluno_id for NULL → retorna 0 linhas SILENCIOSAMENTE
-- SELECT id FROM alunos WHERE id NOT IN (SELECT aluno_id FROM aulas WHERE ...)

-- ── PostgreSQL ──────────────────────────────────────────────────────────────
SELECT a.id, a.nome, a.modalidade
FROM alunos a
WHERE a.ativo
  AND NOT EXISTS (
      SELECT 1 FROM aulas x
      WHERE x.aluno_id = a.id
        AND x.data_aula >= CURRENT_DATE - 60
  );

-- Alternativa com LEFT JOIN (mesma performance, diferente estilo):
SELECT a.id, a.nome
FROM alunos a
LEFT JOIN aulas x
  ON x.aluno_id = a.id AND x.data_aula >= CURRENT_DATE - 60
WHERE a.ativo
  AND x.id IS NULL;


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 4 · COORTE E RETENÇÃO
-- Pergunta: "De cada mês de entrada, quantos alunos continuam ativos?"
-- ════════════════════════════════════════════════════════════════════════════
-- Raciocínio: "Coorte = mês de primeira atividade.
--  Uso MIN(mes) OVER (PARTITION BY aluno_id) para calcular a coorte.
--  Mes_N = diferença em meses entre mes_atual e coorte."

-- ── Funciona igual em Oracle e PostgreSQL (troque DATE_TRUNC e AGE) ─────────
WITH atividade AS (
    SELECT DISTINCT
        aluno_id,
        DATE_TRUNC('month', data_aula)::date        mes
    FROM aulas
),
com_coorte AS (
    SELECT
        aluno_id,
        mes,
        MIN(mes) OVER (PARTITION BY aluno_id)       coorte
    FROM atividade
)
SELECT
    coorte,
    (EXTRACT(YEAR  FROM AGE(mes, coorte)) * 12
     + EXTRACT(MONTH FROM AGE(mes, coorte)))::int   mes_n,
    COUNT(DISTINCT aluno_id)                        alunos_ativos
FROM com_coorte
GROUP BY 1, 2
ORDER BY 1, 2;

-- Oracle: substitua AGE(mes, coorte) por MONTHS_BETWEEN(mes, coorte)
-- Oracle: substitua DATE_TRUNC por TRUNC(data_aula, 'MM')


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 5 · ACUMULADO E MÉDIA MÓVEL
-- ════════════════════════════════════════════════════════════════════════════

-- ── Oracle e PostgreSQL (mesma sintaxe) ─────────────────────────────────────
SELECT
    DATE_TRUNC('month', vencimento)::date           mes,
    SUM(valor)                                      fat_mes,

    -- Acumulado (use ROWS para garantir linha a linha)
    SUM(SUM(valor)) OVER (
        ORDER BY DATE_TRUNC('month', vencimento)
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                               fat_acumulado,

    -- Média móvel 3 meses
    AVG(SUM(valor)) OVER (
        ORDER BY DATE_TRUNC('month', vencimento)
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    )                                               media_3m,

    -- Variação % em relação ao mês anterior (LAG)
    ROUND(100.0 * (
        SUM(valor) - LAG(SUM(valor)) OVER (ORDER BY DATE_TRUNC('month', vencimento))
    ) / NULLIF(LAG(SUM(valor)) OVER (ORDER BY DATE_TRUNC('month', vencimento)), 0), 1)
                                                    var_pct_mes_anterior

FROM faturas
GROUP BY 1
ORDER BY 1;

-- ⚠️  ROWS vs RANGE:
-- Sem moldura explícita + ORDER BY → RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
-- RANGE agrupa linhas com mesmo valor de ORDER BY (pode acumular "de golpe")
-- ROWS é linha a linha: sempre use ROWS para comportamento previsível


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 6 · REMOVER DUPLICADOS
-- ════════════════════════════════════════════════════════════════════════════

-- ── Oracle ──────────────────────────────────────────────────────────────────
-- Mantém o registro de menor ROWID por email (mais antigo, geralmente)
DELETE FROM alunos
WHERE ROWID NOT IN (
    SELECT MIN(ROWID)
    FROM alunos
    GROUP BY email
);

-- ── PostgreSQL ──────────────────────────────────────────────────────────────
-- ctid é o equivalente do ROWID no PostgreSQL
DELETE FROM alunos
WHERE ctid IN (
    SELECT ctid FROM (
        SELECT
            ctid,
            ROW_NUMBER() OVER (
                PARTITION BY email
                ORDER BY id  -- mantém o de menor id (mais antigo)
            ) rn
        FROM alunos
    ) t
    WHERE rn > 1
);

-- Verificar antes de deletar (boa prática):
SELECT email, COUNT(*), MIN(id) id_manter
FROM alunos
GROUP BY email
HAVING COUNT(*) > 1;


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 7 · PIVÔ COM AGREGAÇÃO CONDICIONAL
-- ════════════════════════════════════════════════════════════════════════════

-- ── Oracle (portátil — funciona em qualquer banco) ───────────────────────────
SELECT
    instrutor_id,
    SUM(CASE WHEN modalidade = 'Salto'       THEN 1 ELSE 0 END) salto,
    SUM(CASE WHEN modalidade = 'Dressage'    THEN 1 ELSE 0 END) dressage,
    SUM(CASE WHEN modalidade = 'Hipismo'     THEN 1 ELSE 0 END) hipismo,
    SUM(CASE WHEN modalidade = 'Equoterapia' THEN 1 ELSE 0 END) equoterapia,
    COUNT(*)                                                     total
FROM aulas
GROUP BY instrutor_id
ORDER BY total DESC;

-- ── PostgreSQL (FILTER — mais limpo, padrão SQL:2003) ────────────────────────
SELECT
    instrutor_id,
    COUNT(*) FILTER (WHERE modalidade = 'Salto')        salto,
    COUNT(*) FILTER (WHERE modalidade = 'Dressage')     dressage,
    COUNT(*) FILTER (WHERE modalidade = 'Hipismo')      hipismo,
    COUNT(*) FILTER (WHERE modalidade = 'Equoterapia')  equoterapia,
    COUNT(*)                                             total
FROM aulas
GROUP BY instrutor_id
ORDER BY total DESC;

-- Em entrevista sobre PIVOT dinâmico:
-- "PIVOT nativo não existe no PostgreSQL. Para colunas dinâmicas precisaria
--  de SQL procedural ou crosstab (tablefunc). Se as modalidades são fixas,
--  FILTER ou CASE WHEN é o padrão recomendado e portátil."


-- ════════════════════════════════════════════════════════════════════════════
-- PADRÃO 8 · CALENDÁRIO SEM LACUNAS
-- Pergunta: "Liste dias de 2026 com zero aulas (que GROUP BY esconderia)"
-- ════════════════════════════════════════════════════════════════════════════

-- ── Oracle ──────────────────────────────────────────────────────────────────
SELECT
    cal.dia,
    COUNT(a.id)                                     total_aulas,
    NVL(SUM(a.duracao_min), 0)                      minutos_totais
FROM (
    -- Calendário: todos os dias de 2026
    SELECT DATE '2026-01-01' + LEVEL - 1 dia
    FROM dual
    CONNECT BY LEVEL <= 365
) cal
LEFT JOIN aulas a ON TRUNC(a.data_aula) = cal.dia
GROUP BY cal.dia
ORDER BY cal.dia;

-- ── PostgreSQL ──────────────────────────────────────────────────────────────
SELECT
    cal.dia::date,
    COUNT(a.id)                                     total_aulas,
    COALESCE(SUM(a.duracao_min), 0)                 minutos_totais
FROM generate_series(
    DATE '2026-01-01',
    DATE '2026-12-31',
    INTERVAL '1 day'
) cal(dia)
LEFT JOIN aulas a ON a.data_aula::date = cal.dia::date
GROUP BY cal.dia
ORDER BY cal.dia;

-- Uso prático no GATE4:
-- Dias com 0 aulas → ver padrões de sazonalidade
-- Feriados e fins de semana identificados
-- Mesmo padrão do Guia 2 (séries temporais com asfreq() no Pandas)
