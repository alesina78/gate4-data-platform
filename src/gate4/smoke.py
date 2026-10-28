import numpy as np, pandas as pd

rng = np.random.default_rng(42)
df = pd.DataFrame({"id": range(1, 6), "valor": rng.integers(100, 500, 5)})
print(df)