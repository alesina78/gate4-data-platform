Aqui está a sequência resumida para você revisar todos os arquivos criados para o Guia 18:

src/gate4/g18_m0_gerador.py (Geração - M0)

O que rever: Como o NumPy cria as tabelas do ecossistema (empresas, alunos, cavalos e faturas) de forma reproduzível e como injeta as sujeiras de propósito.

src/gate4/g18_m1_qualidade.py (Qualidade - M1)

O que rever: As regras de auditoria em Pandas que buscam valores nulos, chaves estrangeiras órfãs e status fora do domínio.

src/gate4/g18_m2_limpeza.py (Limpeza - M2)

O que rever: O uso de Expressões Regulares (str.extract com Regex) para converter textos livres (como "2 kg") em números decimais (float).

src/gate4/g18_pipeline.py (Pipeline Principal)

O que rever: Como o script orquestra todas as etapas anteriores em sequência e exporta os resultados consolidados em formato .parquet.

tests/test_g18_pipeline.py (Testes Automatizados)

O que rever: Como o pytest valida de forma automatizada a Regex de limpeza e o relatório do pipeline.