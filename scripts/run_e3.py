"""
Experiment Runner — E3 复制机制实验

研究问题：策略模仿（复制）如何导致多样性丧失？

实验处理：策略复制（无突变）+ 财富重分配。
成功策略被克隆，α_k 最低的 agent 被替换。

Usage: python scripts/run_e3.py
"""
import json, time, sys, traceback
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from evo_asm.config import EVOASMConfig
from evo_asm.model import EVOASMModel

# E3 参数规格（EXPERIMENTS.md）
# T 从 10000 调整为 2000 以保证实用执行时间
M = 500
N = 1
T = 2000
K = 200

# 自变量
LAMBDA_SELECT_VALS = [1.0, 3.0]   # 选择强度
SIGMA_INIT_VALS = [0.02, 0.10, 0.30]  # 初始策略多样性
SIGMA_NOISE_VALS = [0.0, 0.005, 0.02]  # 噪声交易冲击
# 固定
P_ELIMINATE = 0.20  # 淘汰概率（固定）
SEEDS = [42, 123, 456, 789, 1024]

OUTPUT_ROOT = ROOT / "results" / "e3_replication"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

def run_one(lambda_select: float, sigma_init: float, sigma_noise: float, seed: int) -> Path:
    """执行单次 E3 实验运行。"""
    exp_name = f"lambda={lambda_select:.2f}_sigma={sigma_init:.2f}_noise={sigma_noise:.3f}_seed={seed}"
    out_dir = OUTPUT_ROOT / exp_name

    if (out_dir / "summary.json").exists():
        print(f"  SKIP {exp_name} — already completed")
        return out_dir

    cfg = EVOASMConfig(
        M=M, N=N, T=T, K=K,
        P_eliminate=P_ELIMINATE,
        lambda_select=lambda_select,
        p_mut=0.0,          # E3: 无突变
        sigma_init=sigma_init,
        sigma_noise=sigma_noise,
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
    total = len(LAMBDA_SELECT_VALS) * len(SIGMA_INIT_VALS) * len(SIGMA_NOISE_VALS) * len(SEEDS)
    print(f"E3 Replication Experiment: {total} runs (M={M}, T={T}, K={K})")
    print(f"Output: {OUTPUT_ROOT}")
    print(f"lambda_select: {LAMBDA_SELECT_VALS}")
    print(f"sigma_init: {SIGMA_INIT_VALS}")
    print(f"sigma_noise: {SIGMA_NOISE_VALS}")
    print(f"P_eliminate (fixed): {P_ELIMINATE}")
    print(f"seeds: {SEEDS}")
    print("-" * 60)

    completed = 0
    failed = 0

    for lambda_select in LAMBDA_SELECT_VALS:
        for sigma_init in SIGMA_INIT_VALS:
            for sigma_noise in SIGMA_NOISE_VALS:
                for seed in SEEDS:
                    try:
                        run_one(lambda_select, sigma_init, sigma_noise, seed)
                        completed += 1
                    except Exception as e:
                        print(f"  FAIL: lambda={lambda_select}, sigma={sigma_init}, noise={sigma_noise}, seed={seed}: {e}")
                        traceback.print_exc()
                        failed += 1

    print("-" * 60)
    print(f"E3 complete: {completed} successful, {failed} failed, {total} total")

    summary = {
        "experiment": "e3_replication",
        "note": "T adjusted to 2000 (from EXPERIMENTS.md 10000) for practical runtime",
        "parameters": {
            "M": M, "N": N, "T": T, "K": K,
            "lambda_select_vals": LAMBDA_SELECT_VALS,
            "sigma_init_vals": SIGMA_INIT_VALS,
            "sigma_noise_vals": SIGMA_NOISE_VALS,
            "P_eliminate": P_ELIMINATE,
            "p_mut": 0.0,
            "kappa": 5e-9,
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
