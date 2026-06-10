"""
Experiment Runner ? E1 ????????

?? E1 ?????????????
????????????e1_sigma_init={si}_sigma_noise={sn}_seed={seed}

Usage: python scripts/run_e1.py
"""
import json, time, sys, traceback
from pathlib import Path
import numpy as np

# Project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from evo_asm.config import EVOASMConfig
from evo_asm.model import EVOASMModel

# ?? E1 ???? ??
# ????? M, T ?????????????? EXPERIMENTS.md
# ????: M=500, T=10000
M = 200
T = 1000
N = 1
K = 100  # ?????E1 ????P_eliminate=0?

SIGMA_INIT_VALS = [0.02, 0.10, 0.30]
SIGMA_NOISE_VALS = [0.0, 0.005, 0.02]
SEEDS = [42, 123, 456, 789, 1024]

OUTPUT_ROOT = ROOT / "results" / "e1_no_evolution"

def run_one(sigma_init: float, sigma_noise: float, seed: int) -> Path:
    """??????????????"""
    exp_name = f"sigma_init={sigma_init:.2f}_sigma_noise={sigma_noise:.3f}_seed={seed}"
    out_dir = OUTPUT_ROOT / exp_name

    # ????????
    if (out_dir / "summary.json").exists():
        print(f"  SKIP {exp_name} ? already completed")
        return out_dir

    cfg = EVOASMConfig(
        M=M, N=N, T=T, K=K,
        sigma_init=sigma_init,
        sigma_noise=sigma_noise,
        P_eliminate=0.0,  # E1: ???
        lambda_select=0.0,  # ?????
        p_mut=0.0,  # ???
        seed=seed,
        # ????? kappa ??????
        kappa=5e-9,
    )

    model = EVOASMModel(cfg)
    t0 = time.time()
    try:
        model.run(n_steps=T)
    except Exception as e:
        print(f"  ERROR {exp_name}: {e}")
        return out_dir

    elapsed = time.time() - t0
    model.save_results(OUTPUT_ROOT, experiment_name=exp_name)
    print(f"  DONE {exp_name} ? {elapsed:.1f}s")
    return out_dir

def main():
    total = len(SIGMA_INIT_VALS) * len(SIGMA_NOISE_VALS) * len(SEEDS)
    print(f"E1 Experiment Runner: {total} runs ({M} agents x {T} steps)")
    print(f"Output: {OUTPUT_ROOT}")
    print(f"sigma_init: {SIGMA_INIT_VALS}")
    print(f"sigma_noise: {SIGMA_NOISE_VALS}")
    print(f"seeds: {SEEDS}")
    print("-" * 60)

    completed = 0
    failed = 0

    for sigma_init in SIGMA_INIT_VALS:
        for sigma_noise in SIGMA_NOISE_VALS:
            for seed in SEEDS:
                try:
                    run_one(sigma_init, sigma_noise, seed)
                    completed += 1
                except Exception as e:
                    print(f"  FAIL: sigma_init={sigma_init}, sigma_noise={sigma_noise}, seed={seed}: {e}")
                    traceback.print_exc()
                    failed += 1

    print("-" * 60)
    print(f"E1 complete: {completed} successful, {failed} failed, {total} total")

    # ????
    summary = {
        "experiment": "e1_no_evolution",
        "parameters": {
            "M": M, "N": N, "T": T, "K": K,
            "sigma_init_vals": SIGMA_INIT_VALS,
            "sigma_noise_vals": SIGMA_NOISE_VALS,
            "seeds": SEEDS,
        },
        "completed": completed,
        "failed": failed,
        "total": total,
    }
    with open(OUTPUT_ROOT / "_experiment_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary saved to {OUTPUT_ROOT / '_experiment_summary.json'}")

if __name__ == "__main__":
    main()
