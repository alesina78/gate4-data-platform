"""
=============================================================================
GUIA 16 · Pandas Avançado, Otimização de Performance e DuckDB
-----------------------------------------------------------------------------
Este script implementa o laboratório prático de alta performance para o 
ecossistema GATE4. Ele substitui práticas lentas (como loops e uso excessivo 
de RAM) por técnicas avançadas de engenharia de dados.

Conceitos Demonstrados:
1. Vetorização vs. Loops (iterrows/apply): O ganho de performance usando C/NumPy.
2. Gestão de Memória (Downcasting & Category): Como reduzir drasticamente a RAM.
3. Formato Columnar (Parquet): Leitura seletiva e compressão em relação ao CSV.
4. Motor Analítico Local (DuckDB): Consultas SQL diretas em arquivos Parquet.
=============================================================================
"""

from pathlib import Path
import time
import numpy as np
import pandas as pd

# Importação opcional do DuckDB para consultas SQL ultrarrápidas
try:
    import duckdb
except ImportError:
    duckdb = None


def gerar_faturas_sinteticas(n: int = 500_000, seed: int = 42) -> pd.DataFrame:
    """
    Gera uma massa de dados sintética de faturas no formato do GATE4
    utilizando geradores eficientes do NumPy.
    """
    print(f"ℹ️ Gerando base simulada de {n:,} registros para o benchmark...")
    rng = np.random.default_rng(seed)
    
    # Simula datas de vencimento e atrasos log-normais
    venc = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 600, n), unit="D")
    atraso = np.where(rng.random(n) < 0.70, 0, np.round(rng.lognormal(2.3, 0.8, n))).astype(int)
    pagamento = (venc + pd.to_timedelta(atraso, unit="D")).where(rng.random(n) < 0.80)
    
    return pd.DataFrame({
        "id": np.arange(1, n + 1),
        "empresa_id": rng.integers(1, 6, n),
        "aluno_id": rng.integers(1, 5000, n),
        "status": rng.choice(["PAGO", "PENDENTE", "ATRASADO"], n, p=[0.7, 0.2, 0.1]),
        "modalidade": rng.choice(["Salto", "Adestramento", "Passeio", "Iniciante"], n),
        "valor": np.round(rng.normal(450, 90, n), 2),
        "data_vencimento": venc,
        "data_pagamento": pagamento,
    })


def benchmark_atrasos(df: pd.DataFrame):
    """
    Compara o tempo de processamento entre loops manuais e operações vetorizadas.
    """
    print("\n" + "=" * 60)
    print("⏱️ [LAB 1] Comparativo de Performance: Loop vs Vetorização")
    print("=" * 60)
    
    # Amostra menor para o iterrows não travar a máquina
    df_amostra = df.head(10_000).copy()

    # ABORDAGEM 1: iterrows (O "Cursor com Loop" - Extremamente Lento)
    t0 = time.perf_counter()
    saida_iterrows = []
    for _, r in df_amostra.iterrows():
        dias = (r.data_pagamento - r.data_vencimento).days if pd.notna(r.data_pagamento) else 0
        saida_iterrows.append(max(dias, 0))
    t_iterrows = time.perf_counter() - t0
    print(f"❌ iterrows (10k linhas): {t_iterrows:.4f}s (Evite sempre!)")

    # ABORDAGEM 2: Operação Vetorizada (Executada em código nativo C/NumPy)
    t0 = time.perf_counter()
    _ = (df["data_pagamento"] - df["data_vencimento"]).dt.days.clip(lower=0).fillna(0)
    t_vetor = time.perf_counter() - t0
    print(f"✅ Vetorizado ({len(df):,} linhas): {t_vetor:.4f}s (Processou 50x mais dados quase instantaneamente)")


def analisar_memoria(df: pd.DataFrame):
    """
    Analisa o impacto de escolher os dtypes corretos na memória RAM.
    """
    print("\n" + "=" * 60)
    print("🧠 [LAB 2] Gestão de Memória RAM (Tipos e Dtypes)")
    print("=" * 60)

    # Mede o consumo detalhado coluna por coluna em megabytes
    mem_inicial = df.memory_usage(deep=True).sum() / (1024 ** 2)
    print(f"📦 Uso de RAM Inicial (Tipos Padrão): {mem_inicial:.2f} MB")

    # Otimização de tipos (Downcasting e Category)
    df_otimizado = df.copy()
    df_otimizado["status"] = df_otimizado["status"].astype("category")
    df_otimizado["modalidade"] = df_otimizado["modalidade"].astype("category")
    df_otimizado["empresa_id"] = pd.to_numeric(df_otimizado["empresa_id"], downcast="integer")
    df_otimizado["aluno_id"] = pd.to_numeric(df_otimizado["aluno_id"], downcast="integer")
    # Boa prática financeira: converter float para centavos inteiros (evita erro de arredondamento)
    df_otimizado["valor_centavos"] = (df_otimizado["valor"] * 100).round().astype("int32")

    mem_final = df_otimizado.memory_usage(deep=True).sum() / (1024 ** 2)
    reducao = 100 - (mem_final / mem_inicial * 100)
    
    print(f"🚀 Uso de RAM Otimizado: {mem_final:.2f} MB")
    print(f"📉 Redução de Consumo: {reducao:.1f}% de economia de memória!")
    return df_otimizado


def comparar_csv_parquet(df: pd.DataFrame, data_dir: Path):
    """
    Compara o tamanho em disco e a velocidade de leitura entre CSV e Parquet.
    """
    print("\n" + "=" * 60)
    print("📁 [LAB 3] Armazenamento: CSV vs. Parquet (Formato Columnar)")
    print("=" * 60)

    csv_path = data_dir / "faturas_teste.csv"
    parquet_path = data_dir / "faturas_teste.parquet"

    # Escrita CSV
    t0 = time.perf_counter()
    df.to_csv(csv_path, index=False)
    t_csv_write = time.perf_counter() - t0
    tamanho_csv = csv_path.stat().st_size / (1024 ** 2)

    # Escrita Parquet (Comprimido via Snappy)
    t0 = time.perf_counter()
    df.to_parquet(parquet_path, compression="snappy", index=False)
    t_pq_write = time.perf_counter() - t0
    tamanho_pq = parquet_path.stat().st_size / (1024 ** 2)

    print(f"📄 CSV    -> Tamanho: {tamanho_csv:.1f} MB | Escrita: {t_csv_write:.2f}s")
    print(f"parquet -> Tamanho: {tamanho_pq:.1f} MB | Escrita: {t_pq_write:.2f}s ({(tamanho_csv/tamanho_pq):.1f}x menor!)")

    # Leitura Seletiva (Apenas 2 colunas)
    t0 = time.perf_counter()
    _ = pd.read_csv(csv_path, usecols=["modalidade", "valor"])
    t_csv_read = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = pd.read_parquet(parquet_path, columns=["modalidade", "valor"])
    t_pq_read = time.perf_counter() - t0

    print(f"⚡ Leitura de apenas 2 colunas:")
    print(f"   • CSV: {t_csv_read:.3f}s")
    print(f"   • Parquet (Colunar): {t_pq_read:.3f}s ({(t_csv_read/t_pq_read):.1f}x mais rápido)")


def executar_duckdb(parquet_path: Path):
    """
    Demonstra o uso do DuckDB para rodar SQL analítico direto no arquivo Parquet.
    """
    print("\n" + "=" * 60)
    print("🦆 [LAB 4] Consultas Analíticas com DuckDB (SQL direto no arquivo)")
    print("=" * 60)

    if duckdb is None:
        print("⚠️ Biblioteca duckdb não instalada. Execute: pip install duckdb")
        return

    t0 = time.perf_counter()
    # O DuckDB lê o arquivo Parquet diretamente do disco usando processamento paralelo
    resultado = duckdb.sql(f"""
        SELECT 
            modalidade,
            COUNT(*) as total_faturas,
            ROUND(SUM(valor), 2) as faturamento_total,
            ROUND(AVG(valor), 2) as ticket_medio
        FROM '{parquet_path}'
        GROUP BY modalidade
        ORDER BY faturamento_total DESC
    """).df()
    t_duckdb = time.perf_counter() - t0

    print(f"⏱️ Consulta SQL executada em {t_duckdb:.4f} segundos:")
    print(resultado)
    print("=" * 60)
    print("🏁 [Guia 16] Laboratório de Performance concluído com êxito!")


def main():
    print("🚀 [Guia 16] Iniciando suíte completa de performance do GATE4...")
    
    root_dir = Path(__file__).resolve().parents[2]
    data_dir = root_dir / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = data_dir / "faturas_teste.parquet"

    # Gera o dataset de teste (200 mil linhas para rodar rápido e sem travar)
    df = gerar_faturas_sinteticas(n=200_000)

    # Executa os laboratórios
    benchmark_atrasos(df)
    analisar_memoria(df)
    comparar_csv_parquet(df, data_dir)
    
    if not parquet_path.exists():
        df.to_parquet(parquet_path, index=False)
        
    executar_duckdb(parquet_path)


if __name__ == "__main__":
    main()