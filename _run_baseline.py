import sys, json, time
from pathlib import Path

ROOT = Path(r"c:\seelf\大三下\主修毕设")
sys.path.insert(0, str(ROOT))

from evo_asm.config import EVOASMConfig
from evo_asm.model import EVOASMModel
import pandas as pd

M, N, T, K = 500, 1, 2000, 200
OUT = ROOT / "results" / "e4_full_evolution" / "baseline_seed42"

# Remove old CSV files
for old_csv in OUT.glob("*.csv"):
    old_csv.unlink()
for old_json in OUT.glob("summary.json"):
    old_json.unlink()

cfg = EVOASMConfig(
    M=M, N=N, T=T, K=K,
    P_eliminate=0.20,
    lambda_select=2.0,
    p_mut=0.10,
    sigma_init=0.10,
    sigma_noise=0.005,
    kappa=5e-9,
    seed=42,
)

model = EVOASMModel(cfg)
t0 = time.time()
model.run(n_steps=T)
elapsed = time.time() - t0
print(f"Simulation done in {elapsed:.1f}s")

model.save_results(OUT, experiment_name="baseline_seed42")
print("Results saved to:", OUT)

fam = pd.read_csv(OUT / "families.csv")
print("families.csv steps:", sorted(fam["step"].unique()))
print("families.csv phases:", fam["phase"].value_counts().to_dict())
