-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  GATE4 Data Platform — Guia 15, Exercício 12                            ║
-- ║  Arquivo : ex12_dbt_projeto_gate4.sql                                   ║
-- ║  Tema    : Todos os models SQL do projeto dbt GATE4                     ║
-- ║  Autor   : Alessandro Esina                                              ║
-- ║  Projeto : github.com/alesina78/gate4-data-platform                     ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- OBJETIVO
-- --------
-- Arquivo de referência com TODOS os models SQL do projeto dbt GATE4.
-- Na prática, cada bloco abaixo é um arquivo .sql separado na estrutura:
--
--   gate4_dbt/models/
--     sources.yml
--     staging/
--       stg_alunos.sql
--       stg_aulas.sql
--       stg_faturas.sql
--       schema.yml
--     marts/
--       fct_faturamento_mensal.sql
--       fct_inadimplencia_por_modalidade.sql
--       fct_ocupacao_baias.sql
--       fct_abt_churn.sql
--       dim_aluno.sql
--       schema.yml
--
-- COMO USAR
-- ---------
-- 1. pip install dbt-postgres
-- 2. dbt init gate4_dbt
-- 3. Configure profiles.yml com as credenciais do seu Postgres GATE4
-- 4. Copie cada bloco para o arquivo correspondente em models/
-- 5. dbt build  (roda todos os models + testes)
-- 6. dbt docs generate && dbt docs serve  (abre catálogo no browser)
--
-- ANALOGIA ORACLE → dbt
-- ----------------------
-- CREATE OR REPLACE VIEW    = model com materialized='view'   (staging)
-- CREATE TABLE AS SELECT    = model com materialized='table'  (marts)
-- MERGE INTO                = model com materialized='incremental'
-- ORDER BY no ODI/Pentaho   = ref() define a ordem automaticamente
-- CHECK CONSTRAINT          = teste unique / not_null / relationships
-- Wiki de documentação      = dbt docs generate

-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 1 — sources.yml (YAML, não SQL — salve como sources.yml)
-- ════════════════════════════════════════════════════════════════════════════
-- version: 2
-- sources:
--   - name: gate4
--     schema: public
--     description: "Tabelas operacionais do sistema GATE4 (Django + PostgreSQL)"
--     tables:
--       - name: alunos
--         description: "Cadastro de alunos do haras"
--       - name: aulas
--         description: "Registro de aulas ministradas"
--       - name: faturas
--         description: "Faturas de mensalidade por aluno"
--       - name: cavalos
--         description: "Cadastro de cavalos e carga de trabalho"
--       - name: baias
--         description: "Ocupação de baias por período"


-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 2 — stg_alunos.sql
-- Camada: staging | Materialização: view
-- Responsabilidade: limpar e tipar o cadastro de alunos
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: models/staging/stg_alunos.sql

select
    -- Renomeação para padrão snake_case
    id                              as aluno_id,
    nome,
    modalidade,
    plano,
    empresa_id,

    -- Conversão de tipos (Analogia Oracle: TO_DATE, TO_NUMBER)
    dt_matricula::date              as dt_matricula,
    dt_cancelamento::date           as dt_cancelamento,
    atualizado_em::timestamp        as atualizado_em,

    -- Flag booleana de status ativo
    ativo,

    -- Tempo de casa em dias (para features do modelo de churn)
    -- Analogia Oracle: TRUNC(SYSDATE) - TRUNC(dt_matricula)
    (current_date - dt_matricula::date) as dias_de_casa

from {{ source('gate4', 'alunos') }}


-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 3 — stg_aulas.sql
-- Camada: staging | Materialização: view
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: models/staging/stg_aulas.sql

select
    id                              as aula_id,
    aluno_id,
    instrutor_id,
    cavalo_id,
    empresa_id,

    data_aula::date                 as data_aula,
    duracao_min::integer            as duracao_min,

    -- Flags de status
    realizada,
    cancelada,
    reagendada,

    -- Mês de referência para agregações
    -- Analogia Oracle: TRUNC(data_aula, 'MM')
    date_trunc('month', data_aula::date)::date as mes_ref

from {{ source('gate4', 'aulas') }}


-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 4 — stg_faturas.sql
-- Camada: staging | Materialização: view
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: models/staging/stg_faturas.sql

select
    id                              as fatura_id,
    aluno_id,
    empresa_id,

    -- Conversão de tipos
    valor::numeric(12, 2)           as valor,
    vencimento::date                as vencimento,
    pago_em::date                   as pago_em,
    atualizado_em::timestamp        as atualizado_em,

    -- Coluna calculada: está atrasada?
    -- Analogia Oracle: CASE WHEN pago_em IS NULL AND vencimento < SYSDATE THEN 1 ELSE 0 END
    (pago_em is null and vencimento < current_date) as esta_atrasada,

    -- Dias de atraso (NULL se em dia ou paga)
    case
        when pago_em is null and vencimento < current_date
        then (current_date - vencimento)
        else null
    end                             as dias_em_atraso,

    -- Mês de referência da fatura
    date_trunc('month', vencimento::date)::date as mes_ref

from {{ source('gate4', 'faturas') }}


-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 5 — fct_faturamento_mensal.sql
-- Camada: marts | Materialização: table
-- Responsabilidade: faturamento + inadimplência por mês e empresa
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: models/marts/fct_faturamento_mensal.sql

select
    f.mes_ref                                       as mes,
    f.empresa_id,

    -- Totais financeiros
    sum(f.valor)                                    as faturado,

    -- FILTER = WHERE dentro do agregado (PostgreSQL)
    -- Analogia Oracle: SUM(CASE WHEN esta_atrasada THEN valor ELSE 0 END)
    coalesce(
        sum(f.valor) filter (where f.esta_atrasada), 0
    )                                               as em_atraso,

    -- Percentual de inadimplência
    -- NULLIF evita divisão por zero (Analogia Oracle: NULLIF(faturado, 0))
    round(
        100.0 * coalesce(
            sum(f.valor) filter (where f.esta_atrasada), 0
        ) / nullif(sum(f.valor), 0),
        1
    )                                               as pct_inadimplencia,

    -- Contagem de alunos faturados
    count(distinct f.aluno_id)                      as alunos_faturados,
    count(*)                                        as total_faturas

-- ref() garante que stg_faturas roda ANTES deste model
from {{ ref('stg_faturas') }} f
group by 1, 2
order by 1 desc, 2


-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 6 — fct_inadimplencia_por_modalidade.sql
-- Camada: marts | Materialização: table
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: models/marts/fct_inadimplencia_por_modalidade.sql

select
    f.mes_ref                                       as mes,
    a.modalidade,
    a.plano,

    sum(f.valor)                                    as faturado,
    coalesce(
        sum(f.valor) filter (where f.esta_atrasada), 0
    )                                               as em_atraso,
    round(
        100.0 * coalesce(
            sum(f.valor) filter (where f.esta_atrasada), 0
        ) / nullif(sum(f.valor), 0),
        1
    )                                               as pct_inadimplencia,
    count(distinct f.aluno_id)                      as alunos

-- JOIN entre dois models — dbt garante a ordem de execução
from      {{ ref('stg_faturas') }} f
left join {{ ref('stg_alunos') }}  a on a.aluno_id = f.aluno_id
group by 1, 2, 3
order by 1 desc, pct_inadimplencia desc


-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 7 — fct_abt_churn.sql
-- Camada: marts | Materialização: INCREMENTAL
-- Responsabilidade: ABT para o modelo de churn (Guia 10)
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: models/marts/fct_abt_churn.sql

-- Configuração de materialização incremental
-- Analogia Oracle: MERGE INTO gold.abt_churn USING ... ON (unique_key)
{{ config(
    materialized='incremental',
    unique_key='aluno_mes_key'
) }}

with aulas_90d as (
    -- Agrega aulas dos últimos 90 dias por aluno
    -- Analogia Oracle: subconsulta com GROUP BY e filtro de data
    select
        aluno_id,
        count(*)                                    as total_aulas,
        count(*) filter (where realizada)           as aulas_realizadas,
        count(*) filter (where reagendada)          as reagendamentos
    from {{ ref('stg_aulas') }}
    where data_aula >= current_date - 90
    group by 1
),

financeiro as (
    -- Agrega métricas financeiras por aluno
    select
        aluno_id,
        avg(dias_em_atraso)                         as dias_atraso_medio,
        max(vencimento)                             as ultima_fatura,
        count(*) filter (where esta_atrasada)       as faturas_atrasadas
    from {{ ref('stg_faturas') }}
    group by 1
)

select
    a.aluno_id,
    a.modalidade,
    a.plano,
    a.empresa_id,
    a.dias_de_casa,

    -- Chave única: aluno + mês de referência
    a.aluno_id::text || '_' ||
        date_trunc('month', current_date)::text     as aluno_mes_key,
    date_trunc('month', current_date)::date         as mes_ref,

    -- Features de frequência (últimos 90 dias)
    coalesce(au.total_aulas, 0)                     as aulas_90d,
    coalesce(au.aulas_realizadas, 0)                as aulas_realizadas_90d,
    coalesce(au.reagendamentos, 0)                  as reagendamentos_90d,

    -- Features financeiras
    coalesce(f.dias_atraso_medio, 0)                as dias_atraso_medio,
    f.ultima_fatura,
    coalesce(f.faturas_atrasadas, 0)                as faturas_atrasadas,

    -- Label (target do modelo)
    -- Analogia Oracle: CASE WHEN dt_cancelamento IS NOT NULL THEN 1 ELSE 0 END
    (a.dt_cancelamento is not null)::integer        as churn,

    current_timestamp                               as atualizado_em

from      {{ ref('stg_alunos') }}  a
left join aulas_90d                au on au.aluno_id = a.aluno_id
left join financeiro               f  on f.aluno_id  = a.aluno_id
where a.ativo

-- Bloco incremental: só processa registros atualizados recentemente
-- Na primeira run (full refresh): processa tudo
-- Runs seguintes: processa só o que mudou
{% if is_incremental() %}
    and a.atualizado_em > (
        select max(atualizado_em) from {{ this }}
    )
{% endif %}


-- ════════════════════════════════════════════════════════════════════════════
-- BLOCO 8 — dim_aluno.sql
-- Camada: marts | Materialização: table
-- Responsabilidade: dimensão de alunos para o modelo estrela do Power BI
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: models/marts/dim_aluno.sql

select
    aluno_id,
    nome,
    modalidade,
    plano,
    empresa_id,
    dt_matricula,
    dt_cancelamento,
    ativo,
    dias_de_casa,

    -- Segmentação por tempo de casa (para o Power BI)
    -- Analogia Oracle: CASE WHEN dias_de_casa BETWEEN ...
    case
        when dias_de_casa < 90   then 'Novo (< 3 meses)'
        when dias_de_casa < 365  then 'Em adaptação (3-12 meses)'
        when dias_de_casa < 730  then 'Consolidado (1-2 anos)'
        else                          'Veterano (2+ anos)'
    end                             as segmento_permanencia

from {{ ref('stg_alunos') }}
