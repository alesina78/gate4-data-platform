-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  GATE4 Data Platform — Guia 15, Exercício 14                             ║
-- ║  Arquivo : ex14_dbt_testes_singulares.sql                                ║
-- ║  Tema    : Testes Singulares (Regras de Auditoria e Negócio) no dbt      ║
-- ║  Autor   : Alessandro Lesina Giordano                                    ║
-- ║  Projeto : github.com/alesina78/gate4-data-platform                      ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- OBJETIVO & CONCEITO
-- -------------------
-- Testes singulares (Singular Tests) validam regras de negócio complexas,
-- reconciliações financeiras e consistência entre múltiplas tabelas.
--
--   * 0 linhas retornadas  → PASS (dados íntegros conforme a regra).
--   * >= 1 linha retornada → FAIL (o dbt exibe os registros ofensores).
--
-- Analogia Oracle/PL-SQL: Equivale às queries de batimento e auditoria pós-carga
-- em rotinas ETL, porém executadas automaticamente como gates de qualidade no DAG.
--
-- ESTRUTURA EM PRODUÇÃO
-- ---------------------
-- Em um projeto dbt Core real, cada bloco abaixo reside em um arquivo .sql
-- individual dentro da pasta `tests/`:
--   tests/
--     ├── assert_faturas_valor_positivo.sql
--     ├── assert_faturamento_reconciliado.sql
--     ├── assert_inadimplencia_percentual_valido.sql
--     ├── assert_churn_sem_data_futura.sql
--     ├── assert_aulas_sem_aluno_ativo.sql
--     └── assert_abt_churn_features_validas.sql
--
-- COMANDOS DE EXECUÇÃO
-- --------------------
--   dbt test --select test_type:singular   → Executa apenas os testes singulares.
--   dbt test --store-failures             → Grava as linhas com erro no banco para análise.


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 1: assert_faturas_valor_positivo.sql
-- ----------------------------------------------------------------------------
-- Regra de Negócio : Todo título financeiro emitido deve ter valor > R$ 0,00.
-- Impacto          : Faturas zeradas ou negativas distorcem o ticket médio e
--                    podem indicar estornos mal lançados no sistema transacional.
-- Severidade       : error (bloqueia publicação no BI).
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_faturas_valor_positivo.sql

select
    fatura_id,
    aluno_id,
    empresa_id,
    valor,
    'Fatura com valor inválido (zero ou negativo)' as motivo
from {{ ref('stg_faturas') }}
where valor <= 0


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 2: assert_faturamento_reconciliado.sql
-- ----------------------------------------------------------------------------
-- Regra de Negócio : A receita agregada no Data Mart (`fct_faturamento_mensal`)
--                    deve bater exatamente com a tabela origem (`gate4.faturas`).
-- Impacto          : Previne duplicação de receita causada por JOINs cartesianos
--                    (fan-out) ou perda de registros por filtros indevidos.
-- Severidade       : error (auditoria contábil obrigatória).
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_faturamento_reconciliado.sql

with
soma_mart as (
    select coalesce(sum(faturado), 0) as total_mart
    from {{ ref('fct_faturamento_mensal') }}
),
soma_fonte as (
    select coalesce(sum(valor), 0) as total_fonte
    from {{ source('gate4', 'faturas') }}
)

-- Tolerância de R$ 0,01 para evitar falsos positivos por arredondamento decimal
select
    m.total_mart,
    f.total_fonte,
    abs(m.total_mart - f.total_fonte) as diferenca,
    'Mart diverge da fonte — verificar duplicatas (fan-out) ou filtros' as motivo
from soma_mart m
cross join soma_fonte f
where abs(m.total_mart - f.total_fonte) > 0.01


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 3: assert_inadimplencia_percentual_valido.sql
-- ----------------------------------------------------------------------------
-- Regra de Negócio : Taxa de inadimplência mensal deve estar entre 0% e 100%.
-- Impacto          : Valores fora dessa faixa indicam erro na fórmula de razão
--                    (ex.: numerador maior que denominador por filtro divergente).
-- Severidade       : error.
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_inadimplencia_percentual_valido.sql

select
    mes,
    empresa_id,
    pct_inadimplencia,
    'Percentual de inadimplência fora do intervalo válido' as motivo
from {{ ref('fct_faturamento_mensal') }}
where pct_inadimplencia < 0
   or pct_inadimplencia > 100


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 4: assert_churn_sem_data_futura.sql
-- ----------------------------------------------------------------------------
-- Regra de Negócio : Cancelamentos registrados não podem ter data futura.
-- Impacto          : Datas futuras quebram janelas temporais da ABT de churn e
--                    causam data leakage no treinamento do modelo de ML.
-- Severidade       : warn (alerta equipe operacional para corrigir cadastro).
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_churn_sem_data_futura.sql

select
    aluno_id,
    empresa_id,
    dt_cancelamento,
    'Data de cancelamento no futuro — revisar lançamento no ERP' as motivo
from {{ ref('stg_alunos') }}
where dt_cancelamento > current_date


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 5: assert_aulas_sem_aluno_ativo.sql
-- ----------------------------------------------------------------------------
-- Regra de Negócio : Não deve haver aulas lançadas após 30 dias da data de
--                    cancelamento do contrato (janela de carência/reposição).
-- Impacto          : Indica falha no bloqueio de agenda do sistema operacional
--                    ou aulas ministradas sem cobertura contratual/financeira.
-- Severidade       : warn.
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_aulas_sem_aluno_ativo.sql

select
    au.aula_id,
    au.aluno_id,
    au.data_aula,
    a.dt_cancelamento,
    'Aula registrada mais de 30 dias após cancelamento do aluno' as motivo
from {{ ref('stg_aulas') }} au
inner join {{ ref('stg_alunos') }} a
    on a.aluno_id = au.aluno_id
where a.dt_cancelamento is not null
  and au.data_aula > (a.dt_cancelamento + interval '30 days')


-- ════════════════════════════════════════════════════════════════════════════
-- TESTE 6: assert_abt_churn_features_validas.sql
-- ----------------------------------------------------------------------------
-- Regra de Negócio : Sanity check (limites físicos e operacionais) das features
--                    que alimentam o modelo HistGradientBoostingClassifier.
-- Impacto          : Impede que outliers extremos ou bugs de agregação degradem
--                    a calibração e as predições em produção.
-- Severidade       : error.
-- ════════════════════════════════════════════════════════════════════════════

-- Arquivo: tests/assert_abt_churn_features_validas.sql

select
    aluno_id,
    aulas_90d,
    reagendamentos_90d,
    dias_atraso_medio,
    case
        when aulas_90d < 0           then 'aulas_90d negativo'
        when aulas_90d > 300         then 'aulas_90d impossível (> 300 aulas em 90 dias)'
        when reagendamentos_90d < 0  then 'reagendamentos_90d negativo'
        when dias_atraso_medio < 0   then 'dias_atraso_medio negativo'
        when dias_atraso_medio > 365 then 'dias_atraso_medio > 1 ano (outlier extremo)'
    end as motivo
from {{ ref('fct_abt_churn') }}
where aulas_90d < 0
   or aulas_90d > 300
   or reagendamentos_90d < 0
   or dias_atraso_medio < 0
   or dias_atraso_medio > 365
