"""
Experiment Runner — E4 复制+突变实验（完整演化）

研究问题：突变能否维持策略多样性以对抗 Alpha 衰减？

实验处理：达尔文式全循环（淘汰-替换 + 策略复制 + 突变）。
策略协同演化，完整检验 AMH 核心命题。

Usage: python scripts/run_e4.py
"""
import json, time, sys, traceback
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from evo_asm.config import EVOASMConfig
from evo_asm.model import EVOASMModel

# E4 参数规格（EXPERIMENTS.md）
M = 500
N = 1
T = 2000     # 从10000调整为2000（与E2/E3一致）
K = 200

# 自变量
P_MUT_VALS = [0.05, 0.10, 0.20, 0.40]      # 突变率
LAMBDA_SELECT_VALS = [1.0, 2.0, 3.0, 5.0]   # 选择强度
SIGMA_INIT_VALS = [0.02, 0.10, 0.30]         # 初始策略多样性
# 固定
P_ELIMINATE = 0.20
SIGMA_NOISE = 0.005
SEEDS = [42, 123, 456, 789, 1024]

OUTPUT_ROOT = ROOT / "results" / "e4_full_evolution"

def run_one(p_mut: float, lambda_select: float, sigma_init: float, seed: int) -> Path:
    """执行单次 E4 实验运行。"""
    exp_name = f"p_mut={p_mut:.2f}_lambda={lambda_select:.2f}_sigma={sigma_init:.2f}_seed={seed}"
    out_dir = OUTPUT_ROOT / exp_name

    if (out_dir / "summary.json").exists():
        print(f"  SKIP {exp_name} — already completed")
        return out_dir

    cfg = EVOASMConfig(
        M=M, N=N, T=T, K=K,
        P_eliminate=P_ELIMINATE,
        lambda_select=lambda_select,
        p_mut=p_mut,
        sigma_init=sigma_init,
        sigma_noise=SIGMA_NOISE,
        kappa=5e-9,
        seed=seed,
    )

    model = EVOASMModel(cfg)
    t0 = time.time()
    try:
        model.run(n_steps=T)
    except Exception as e:
        print(f"  ERROR {exp_name}: {e}")
        traceback.print_exc()
        return out_dir

    elapsed = time.time() - t0
    model.save_results(OUTPUT_ROOT, experiment_name=exp_name)
    print(f"  DONE {exp_name} — {elapsed:.1f}s")
    return out_dir

def main():
    total = len(P_MUT_VALS) * len(LAMBDA_SELECT_VALS) * len(SIGMA_INIT_VALS) * len(SEEDS)
    print(f"E4 Full Evolution Experiment: {total} runs (M={M}, T={T}, K={K})")
    print(f"Output: {OUTPUT_ROOT}")
    print(f"p_mut: {P_MUT_VALS}")
    print(f"lambda_select: {LAMBDA_SELECT_VALS}")
    print(f"sigma_init: {SIGMA_INIT_VALS}")
    print(f"P_eliminate (fixed): {P_ELIMINATE}")
    print(f"sigma_noise (fixed): {SIGMA_NOISE}")
    print(f"seeds: {SEEDS}")
    print("-" * 60)

    completed = 0
    failed = 0

    for p_mut in P_MUT_VALS:
        for lambda_select in LAMBDA_SELECT_VALS:
            for sigma_init in SIGMA_INIT_VALS:
                for seed in SEEDS:
                    try:
                        run_one(p_mut, lambda_select, sigma_init, seed)
                        completed += 1
                    except Exception as e:
                        print(f"  FAIL: p_mut={p_mut}, lambda={lambda_select}, sigma={sigma_init}, seed={seed}: {e}")
                        traceback.print_exc()
                        failed += 1

    print("-" * 60)
    print(f"E4 complete: {completed} successful, {failed} failed, {total} total")

    summary = {
        "experiment": "e4_full_evolution",
        "parameters": {
            "M": M, "N": N, "T": T, "K": K,
            "p_mut_vals": P_MUT_VALS,
            "lambda_select_vals": LAMBDA_SELECT_VALS,
            "sigma_init_vals": SIGMA_INIT_VALS,
            "P_eliminate": P_ELIMINATE,
            "sigma_noise": SIGMA_NOISE,
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
