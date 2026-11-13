-- =============================================================================
-- GATE4 Data Platform · Guia 12
-- Arquivo : 01_dim_data.sql
-- Propósito: Criar e popular a tabela de datas sem buracos (2023–2027)
--
-- Analogia Oracle: equivalente a uma tabela de parâmetros de calendário
-- que você usaria num pacote PL/SQL para cálculo de dias úteis —
-- só que mais completa e integrada ao DW.
--
-- Por que isso importa no Power BI:
-- - Funções de Time Intelligence (TOTALYTD, DATEADD) exigem dim_data
--   marcada como "Tabela de Datas" e SEM buracos (nem fins de semana).
-- - Uma dim_data quebrada é a causa #1 de números errados em relatórios.
-- =============================================================================

-- ── SCHEMA GOLD (crie se não existir) ──────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS gold;

-- ── DROP + RECREATE (seguro para dev; use migration em produção) ───────────
DROP TABLE IF EXISTS gold.dim_data;

CREATE TABLE gold.dim_data (
    -- Chave primária: a própria data (sem surrogate key necessário aqui)
    data                DATE        NOT NULL PRIMARY KEY,

    -- Componentes básicos
    ano                 SMALLINT    NOT NULL,
    trimestre           SMALLINT    NOT NULL,   -- 1 a 4
    mes                 SMALLINT    NOT NULL,   -- 1 a 12
    nome_mes            VARCHAR(20) NOT NULL,   -- 'Janeiro', 'Fevereiro'...
    semana_ano          SMALLINT    NOT NULL,   -- ISO week 1-53
    dia_mes             SMALLINT    NOT NULL,   -- 1 a 31
    dia_semana          SMALLINT    NOT NULL,   -- 0=Domingo ... 6=Sábado
    nome_dia            VARCHAR(15) NOT NULL,

    -- Flags booleanas (muito usadas em filtros DAX e SQL)
    fim_de_semana       BOOLEAN     NOT NULL DEFAULT FALSE,
    primeiro_dia_mes    BOOLEAN     NOT NULL DEFAULT FALSE,
    ultimo_dia_mes      BOOLEAN     NOT NULL DEFAULT FALSE,
    feriado_nacional    BOOLEAN     NOT NULL DEFAULT FALSE,
    nome_feriado        VARCHAR(50),

    -- Chaves de negócio (úteis em OLAP e filtros)
    ano_mes             INTEGER     NOT NULL,   -- ex: 202401
    ano_semana          VARCHAR(10) NOT NULL,   -- ex: '2024-W03'

    -- Metadados
    carregado_em        TIMESTAMP   DEFAULT NOW()
);

COMMENT ON TABLE gold.dim_data IS
    'Tabela de datas sem buracos para DW GATE4. '
    'Deve ser marcada como Tabela de Datas no Power BI. '
    'Atualizada manualmente ou via job anual.';

-- ── POPULATE: gera uma linha por dia (2023-01-01 a 2027-12-31) ─────────────
INSERT INTO gold.dim_data (
    data, ano, trimestre, mes, nome_mes, semana_ano,
    dia_mes, dia_semana, nome_dia,
    fim_de_semana, primeiro_dia_mes, ultimo_dia_mes,
    ano_mes, ano_semana
)
SELECT
    d::DATE                                                      AS data,
    EXTRACT(YEAR  FROM d)::SMALLINT                              AS ano,
    EXTRACT(QUARTER FROM d)::SMALLINT                            AS trimestre,
    EXTRACT(MONTH FROM d)::SMALLINT                              AS mes,
    TO_CHAR(d, 'TMMonth')                                        AS nome_mes,
    EXTRACT(WEEK  FROM d)::SMALLINT                              AS semana_ano,
    EXTRACT(DAY   FROM d)::SMALLINT                              AS dia_mes,
    EXTRACT(DOW   FROM d)::SMALLINT                              AS dia_semana,
    TO_CHAR(d, 'TMDay')                                          AS nome_dia,

    -- Fim de semana: Sábado (6) ou Domingo (0)
    EXTRACT(DOW FROM d) IN (0, 6)                                AS fim_de_semana,

    -- Primeiro dia do mês
    (d::DATE = DATE_TRUNC('month', d)::DATE)                     AS primeiro_dia_mes,

    -- Último dia do mês
    (d::DATE = (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')::DATE) AS ultimo_dia_mes,

    -- Chaves de negócio
    (EXTRACT(YEAR FROM d) * 100 + EXTRACT(MONTH FROM d))::INTEGER AS ano_mes,
    TO_CHAR(d, 'IYYY-"W"IW')                                     AS ano_semana

FROM GENERATE_SERIES(
    '2023-01-01'::DATE,
    '2027-12-31'::DATE,
    '1 day'::INTERVAL
) d;

-- ── FERIADOS NACIONAIS BRASIL (principais — expanda conforme necessário) ────
-- Analogia Oracle: seria um UPDATE num pacote de parâmetros de calendário.

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Confraternização Universal'
WHERE TO_CHAR(data, 'MM-DD') = '01-01';

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Tiradentes'
WHERE TO_CHAR(data, 'MM-DD') = '04-21';

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Dia do Trabalho'
WHERE TO_CHAR(data, 'MM-DD') = '05-01';

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Independência do Brasil'
WHERE TO_CHAR(data, 'MM-DD') = '09-07';

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Nossa Sra. Aparecida'
WHERE TO_CHAR(data, 'MM-DD') = '10-12';

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Finados'
WHERE TO_CHAR(data, 'MM-DD') = '11-02';

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Proclamação da República'
WHERE TO_CHAR(data, 'MM-DD') = '11-15';

UPDATE gold.dim_data SET feriado_nacional = TRUE, nome_feriado = 'Natal'
WHERE TO_CHAR(data, 'MM-DD') = '12-25';

-- ── ÍNDICES ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_dim_data_ano_mes  ON gold.dim_data (ano_mes);
CREATE INDEX idx_dim_data_ano      ON gold.dim_data (ano);
CREATE INDEX idx_dim_data_feriado  ON gold.dim_data (feriado_nacional) WHERE feriado_nacional = TRUE;

-- ── VALIDAÇÃO ───────────────────────────────────────────────────────────────
-- Execute após o INSERT para confirmar que não há buracos
SELECT
    COUNT(*)                                            AS total_dias,
    MIN(data)                                           AS data_inicio,
    MAX(data)                                           AS data_fim,
    COUNT(*) FILTER (WHERE fim_de_semana)               AS fins_de_semana,
    COUNT(*) FILTER (WHERE feriado_nacional)            AS feriados,
    COUNT(*) FILTER (WHERE primeiro_dia_mes)            AS primeiros_dias_mes
FROM gold.dim_data;
-- Esperado: 1827 dias (2023-2027), 522 fins de semana, 8 feriados por ano * 5 anos = 40

-- ── CONSULTA DE EXEMPLO (para validar no Power BI depois) ───────────────────
-- SELECT ano, mes, nome_mes, COUNT(*) AS dias_uteis
-- FROM gold.dim_data
-- WHERE NOT fim_de_semana AND NOT feriado_nacional
-- GROUP BY ano, mes, nome_mes
-- ORDER BY ano, mes;
