-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  GATE4 Data Platform — Guia 15, Exercício 14                            ║
-- ║  Arquivo : ex14_dbt_testes_singulares.sql                               ║
-- ║  Tema    : Testes singulares (SQL customizado) do projeto dbt GATE4     ║
-- ║  Autor   : Alessandro Esina                                              ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- OBJETIVO
-- --------
-- Testes singulares são queries SQL que retornam linhas quando algo está errado.
-- Se a query retorna 0 linhas → PASSOU.
-- Se retorna qualquer linha  → FALHOU (mostra as linhas problemáticas).
--
-- Analogia Oracle: queries de auditoria que você já escreve para validar dados.
-- A diferença é que o dbt as executa automaticamente a cada dbt build.
--
-- LOCALIZAÇÃO
-- -----------
-- Cada bloco abaixo é um arquivo .sql separado em:
--   tests/
--     assert_faturas_valor_positivo.sql
--     assert_faturamento_reconciliado.sql
--     assert_inadimplencia_percentual_valido.sql
--     assert_churn_sem_data_futura.sql
--     assert_aulas_sem_aluno_ativo.sql


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 1: assert_faturas_valor_positivo.sql
-- Falha se existir fatura com valor zero ou negativo
-- Analogia Oracle: query de auditoria antes de publicar o relatório financeiro
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_faturas_valor_positivo.sql

select
    fatura_id,
    aluno_id,
    valor,
    'Fatura com valor inválido (zero ou negativo)' as motivo
from {{ ref('stg_faturas') }}
where valor <= 0

-- Se retornar linhas: há faturas com erro de cadastro → revisar na fonte


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 2: assert_faturamento_reconciliado.sql
-- Verifica se a soma do mart bate com a soma da tabela crua
-- Este é o teste que teria pego o faturamento duplicado (Exercício 41)
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_faturamento_reconciliado.sql

with
soma_mart as (
    -- Total faturado no mart (agregado)
    select sum(faturado) as total_mart
    from {{ ref('fct_faturamento_mensal') }}
),
soma_fonte as (
    -- Total faturado na tabela crua (referência)
    select sum(valor) as total_fonte
    from {{ source('gate4', 'faturas') }}
)

-- Falha se a diferença absoluta for maior que R$ 0.01
-- (tolerância para arredondamento de ponto flutuante)
select
    total_mart,
    total_fonte,
    abs(total_mart - total_fonte) as diferenca,
    'Mart diverge da fonte — verificar duplicatas ou filtros incorretos' as motivo
from soma_mart, soma_fonte
where abs(total_mart - coalesce(total_fonte, 0)) > 0.01


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 3: assert_inadimplencia_percentual_valido.sql
-- Percentual de inadimplência deve estar entre 0 e 100
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_inadimplencia_percentual_valido.sql

select
    mes,
    empresa_id,
    pct_inadimplencia,
    'Percentual de inadimplência fora do intervalo 0-100' as motivo
from {{ ref('fct_faturamento_mensal') }}
where pct_inadimplencia < 0
   or pct_inadimplencia > 100


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 4: assert_churn_sem_data_futura.sql
-- Aluno não pode ter data de cancelamento no futuro
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_churn_sem_data_futura.sql

select
    aluno_id,
    dt_cancelamento,
    'Data de cancelamento no futuro — erro de cadastro' as motivo
from {{ ref('stg_alunos') }}
where dt_cancelamento > current_date


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 5: assert_aulas_sem_aluno_ativo.sql
-- Não deve haver aulas registradas para alunos cancelados
-- (além de 30 dias após o cancelamento — tolerância para aulas pendentes)
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_aulas_sem_aluno_ativo.sql

select
    au.aula_id,
    au.aluno_id,
    au.data_aula,
    a.dt_cancelamento,
    'Aula registrada mais de 30 dias após cancelamento do aluno' as motivo
from      {{ ref('stg_aulas') }}   au
left join {{ ref('stg_alunos') }}  a  on a.aluno_id = au.aluno_id
where a.dt_cancelamento is not null
  and au.data_aula > a.dt_cancelamento + 30


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 6: assert_abt_churn_features_validas.sql
-- Features da ABT devem estar em faixas razoáveis
-- Valores absurdos indicam bug no model de agregação
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_abt_churn_features_validas.sql

select
    aluno_id,
    aulas_90d,
    reagendamentos_90d,
    dias_atraso_medio,
    case
        when aulas_90d < 0           then 'aulas_90d negativo'
        when aulas_90d > 300         then 'aulas_90d impossível (> 300 em 90 dias)'
        when reagendamentos_90d < 0  then 'reagendamentos negativos'
        when dias_atraso_medio < 0   then 'dias_atraso_medio negativo'
        when dias_atraso_medio > 365 then 'dias_atraso_medio > 1 ano (suspeito)'
    end as motivo
from {{ ref('fct_abt_churn') }}
where aulas_90d < 0
   or aulas_90d > 300
   or reagendamentos_90d < 0
   or dias_atraso_medio < 0
   or dias_atraso_medio > 365
