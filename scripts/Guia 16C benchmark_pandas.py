"""
=============================================================================
PROJETO: GATE4 - Transição de SQL para Pandas
GUIA 16: Benchmark REAL de Pandas (nada de números digitados à mão)
AUTOR: Alessandro Lesina Giordano

O QUE FAZ: gera faturas sintéticas no formato do GATE4 e MEDE, no seu computador:
  1) loop (iterrows) x apply x vetorização
  2) memória por tipo de coluna (object x category x int32...)
  3) CSV x Parquet (tamanho e tempo de leitura)
  4) Pandas x DuckDB lendo o mesmo arquivo Parquet

ANTES DE RODAR (uma vez, com o (.venv) ligado):
    pip install pyarrow duckdb

COMO EXECUTAR (leva alguns minutos; feche programas pesados antes):
    python benchmark_pandas.py

SAÍDA: tabelas no terminal e o arquivo benchmark_resultado.json
       (você pode comparar com os números do Guia 16).
=============================================================================
"""

import json
import os
import platform
import tempfile
import time

import numpy as np
import pandas as pd

try:
    import duckdb
except ImportError:
    duckdb = None


def gerar(n, seed=42):
    """Faturas sintéticas parecidas com gateagora_fatura (dados fictícios)."""
    rng = np.random.default_rng(seed)
    venc = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 600, n), unit="D")
    atraso = np.where(rng.random(n) < 0.70, 0, np.round(rng.lognormal(2.3, 0.8, n))).astype(int)
    pagamento = (venc + pd.to_timedelta(atraso, unit="D")).where(rng.random(n) < 0.80)  # NaT = não pago
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


def medir(funcao, repeticoes=3, limite=1.0):
    """Menor tempo de N execuções (execução única se a primeira já passar de 'limite' segundos)."""
    melhor = None
    for i in range(repeticoes):
        t0 = time.perf_counter()
        funcao()
        t = time.perf_counter() - t0
        melhor = t if melhor is None else min(melhor, t)
        if t > limite:
            break
    return melhor


# --- três jeitos de calcular "dias de atraso" ---------------------------------
def atraso_iterrows(df):
    saida = []
    for _, r in df.iterrows():                       # um objeto Series por linha: o mais lento
        saida.append(max((r.data_pagamento - r.data_vencimento).days, 0) if pd.notna(r.data_pagamento) else 0)
    return saida


def atraso_apply(df):
    return df.apply(lambda r: max((r.data_pagamento - r.data_vencimento).days, 0)
                    if pd.notna(r.data_pagamento) else 0, axis=1)


def atraso_vetor(df):
    return (df["data_pagamento"] - df["data_vencimento"]).dt.days.clip(lower=0).fillna(0)


def soma_loop(df):
    acc = {}
    for e, v in zip(df["empresa_id"], df["valor"]):  # loop Python "limpo", sem iterrows
        acc[e] = acc.get(e, 0.0) + v
    return acc


def soma_groupby(df):
    return df.groupby("empresa_id")["valor"].sum()


def linha(rotulo, valores):
    print(f"  {rotulo:<26}" + "".join(f"{('-' if v is None else f'{v:.4f}s'):>14}" for v in valores))


if __name__ == "__main__":
    resultado = {"ambiente": {"python": platform.python_version(), "pandas": pd.__version__,
                              "numpy": np.__version__, "cpus": os.cpu_count(), "sistema": platform.system()}}
    print("Ambiente:", resultado["ambiente"])

    # ---------------------------------------------------------------- 1) loop x vetorização
    print("\n1) Dias de atraso por fatura (menor tempo medido)")
    ns = [1_000, 10_000, 100_000, 1_000_000]
    r1 = {"n": ns, "iterrows": [], "apply": [], "vetor": [], "loop_zip": [], "groupby": []}
    for n in ns:
        df = gerar(n)
        r1["vetor"].append(medir(lambda: atraso_vetor(df)))
        r1["iterrows"].append(medir(lambda: atraso_iterrows(df), repeticoes=1) if n <= 100_000 else None)
        r1["apply"].append(medir(lambda: atraso_apply(df), repeticoes=1) if n <= 100_000 else None)
        r1["loop_zip"].append(medir(lambda: soma_loop(df)))
        r1["groupby"].append(medir(lambda: soma_groupby(df)))
    print("  " + " " * 26 + "".join(f"{n:>14,}" for n in ns))
    for k, nome in [("iterrows", "iterrows"), ("apply", "apply(axis=1)"), ("vetor", "vetorizado"),
                    ("loop_zip", "soma: loop Python (zip)"), ("groupby", "soma: groupby")]:
        linha(nome, r1[k])
    resultado["atraso"] = r1

    # ---------------------------------------------------------------- 2) memória por tipo
    print("\n2) Memória por coluna (1 milhão de linhas, bytes por linha)")
    N = 1_000_000
    df = gerar(N)
    mem = {}

    def bpl(serie):
        return round(serie.memory_usage(index=False, deep=True) / N, 2)

    mem["status"] = {"object": bpl(df["status"].astype(object)), "category": bpl(df["status"].astype("category"))}
    mem["modalidade"] = {"object": bpl(df["modalidade"].astype(object)), "category": bpl(df["modalidade"].astype("category"))}
    try:
        mem["status"]["string[pyarrow]"] = bpl(df["status"].astype("string[pyarrow]"))
        mem["modalidade"]["string[pyarrow]"] = bpl(df["modalidade"].astype("string[pyarrow]"))
    except Exception as e:
        print("  (pyarrow indisponível para string[pyarrow]:", e, ")")
    mem["id"] = {"int64": bpl(df["id"].astype("int64")), "int32": bpl(df["id"].astype("int32"))}
    mem["empresa_id"] = {"int64": bpl(df["empresa_id"].astype("int64")), "int8": bpl(df["empresa_id"].astype("int8"))}
    mem["aluno_id"] = {"int64": bpl(df["aluno_id"].astype("int64")), "int16": bpl(df["aluno_id"].astype("int16"))}
    mem["valor"] = {"float64": bpl(df["valor"].astype("float64")), "float32": bpl(df["valor"].astype("float32")),
                    "int32 (centavos)": bpl((df["valor"] * 100).round().astype("int32"))}
    mem["data_vencimento"] = {"datetime64": bpl(df["data_vencimento"])}
    mem["data_pagamento"] = {"datetime64": bpl(df["data_pagamento"])}
    for col, v in mem.items():
        print(f"  {col:<16}" + "  ".join(f"{k}={b}" for k, b in v.items()))
    resultado["memoria"] = {"n": N, "colunas": mem}

    # ---------------------------------------------------------------- 3) CSV x Parquet
    print("\n3) CSV x Parquet (1 milhão de linhas)")
    arq = {}
    with tempfile.TemporaryDirectory() as tmp:
        csv, pq = os.path.join(tmp, "faturas.csv"), os.path.join(tmp, "faturas.parquet")
        t0 = time.perf_counter(); df.to_csv(csv, index=False); tw_csv = time.perf_counter() - t0
        arq["csv"] = {"mb": round(os.path.getsize(csv) / 1e6, 1), "escrita_s": round(tw_csv, 3),
                      "leitura_total_s": medir(lambda: pd.read_csv(csv, parse_dates=["data_vencimento", "data_pagamento"]), 2, 5),
                      "leitura_2col_s": medir(lambda: pd.read_csv(csv, usecols=["modalidade", "valor"]), 2, 5)}
        try:
            t0 = time.perf_counter(); df.to_parquet(pq, index=False); tw_pq = time.perf_counter() - t0
            arq["parquet"] = {"mb": round(os.path.getsize(pq) / 1e6, 1), "escrita_s": round(tw_pq, 3),
                              "leitura_total_s": medir(lambda: pd.read_parquet(pq)),
                              "leitura_2col_s": medir(lambda: pd.read_parquet(pq, columns=["modalidade", "valor"]))}
        except Exception as e:
            print("  (Parquet indisponível:", e, ") -> pip install pyarrow")
        for k, v in arq.items():
            print(f"  {k:<8} {v['mb']:>7} MB | escrita {v['escrita_s']}s | leitura total {v['leitura_total_s']:.3f}s | 2 colunas {v['leitura_2col_s']:.3f}s")
    resultado["arquivos"] = arq

    # ---------------------------------------------------------------- 4) Pandas x DuckDB
    print("\n4) SELECT modalidade, SUM(valor) ... GROUP BY: Pandas x DuckDB (arquivo Parquet)")
    if duckdb is None:
        print("  (DuckDB não instalado) -> pip install duckdb")
    else:
        r4 = {"n": [], "pandas": [], "duckdb": []}
        for n in [1_000_000, 5_000_000]:
            d = gerar(n)
            with tempfile.TemporaryDirectory() as tmp:
                pq = os.path.join(tmp, "f.parquet")
                d.to_parquet(pq, index=False)
                r4["n"].append(n)
                r4["pandas"].append(medir(lambda: pd.read_parquet(pq, columns=["modalidade", "valor"]).groupby("modalidade")["valor"].sum()))
                r4["duckdb"].append(medir(lambda: duckdb.sql(f"SELECT modalidade, SUM(valor) FROM '{pq}' GROUP BY 1").df()))
            print(f"  {n:>10,} linhas | Pandas {r4['pandas'][-1]:.3f}s | DuckDB {r4['duckdb'][-1]:.3f}s")
            del d
        resultado["duckdb"] = r4

    with open("benchmark_resultado.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)
    print("\nResultado gravado em benchmark_resultado.json")
