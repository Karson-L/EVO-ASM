"""
Experiment Runner — E2 资本扩张实验

研究问题：财富集中（策略拥挤）单独驱动 Alpha 衰减吗？

实验处理：固定策略 + 财富重分配（淘汰-替换机制）
无复制，无突变。资本向盈利策略集中。

Usage: python scripts/run_e2.py
"""
import json, time, sys, traceback
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from evo_asm.config import EVOASMConfig
from evo_asm.model import EVOASMModel

# E2 参数规格（EXPERIMENTS.md）
# 注意：T 从 10000 调整为 2000 以保证实用执行时间（与 E1 的 T=1000 一致风格）
M = 500      # Agent 数量
N = 1        # 单一资产
T = 2000     # 模拟期数（10 个演化周期 @ K=200）
K = 200      # 演化评估周期

# 自变量
P_ELIMINATE_VALS = [0.05, 0.10, 0.20]
LAMBDA_SELECT_VALS = [1.0, 2.0, 4.0]
SIGMA_INIT_VALS = [0.02, 0.10, 0.30]
# 固定控制变量
SIGMA_NOISE = 0.005  # 噪声交易强度（固定）
SEEDS = [42, 123, 456, 789, 1024]

OUTPUT_ROOT = ROOT / "results" / "e2_capital_expansion"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

def run_one(p_eliminate: float, lambda_select: float, sigma_init: float, seed: int) -> Path:
    """执行单次 E2 实验运行。"""
    exp_name = f"p_eliminate={p_eliminate:.2f}_lambda={lambda_select:.2f}_sigma={sigma_init:.2f}_seed={seed}"
    out_dir = OUTPUT_ROOT / exp_name

    # 跳过已完成运行
    if (out_dir / "summary.json").exists():
        print(f"  SKIP {exp_name} — already completed")
        return out_dir

    cfg = EVOASMConfig(
        M=M, N=N, T=T, K=K,
        P_eliminate=p_eliminate,
        lambda_select=lambda_select,
        p_mut=0.0,          # E2: 无突变
        sigma_init=sigma_init,
        sigma_noise=SIGMA_NOISE,
        kappa=5e-9,         # 与 E1 一致的价格弹性
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
    total = len(P_ELIMINATE_VALS) * len(LAMBDA_SELECT_VALS) * len(SIGMA_INIT_VALS) * len(SEEDS)
    print(f"E2 Capital Expansion Experiment: {total} runs (M={M}, T={T}, K={K})")
    print(f"Output: {OUTPUT_ROOT}")
    print(f"P_eliminate: {P_ELIMINATE_VALS}")
    print(f"lambda_select: {LAMBDA_SELECT_VALS}")
    print(f"sigma_init: {SIGMA_INIT_VALS}")
    print(f"sigma_noise (fixed): {SIGMA_NOISE}")
    print(f"seeds: {SEEDS}")
    print("-" * 60)

    completed = 0
    failed = 0

    for p_eliminate in P_ELIMINATE_VALS:
        for lambda_select in LAMBDA_SELECT_VALS:
            for sigma_init in SIGMA_INIT_VALS:
                for seed in SEEDS:
                    try:
                        run_one(p_eliminate, lambda_select, sigma_init, seed)
                        completed += 1
                    except Exception as e:
                        print(f"  FAIL: p_eliminate={p_eliminate}, lambda={lambda_select}, sigma={sigma_init}, seed={seed}: {e}")
                        traceback.print_exc()
                        failed += 1

    print("-" * 60)
    print(f"E2 complete: {completed} successful, {failed} failed, {total} total")

    summary = {
        "experiment": "e2_capital_expansion",
        "note": "T adjusted to 2000 (from EXPERIMENTS.md 10000) for practical runtime",
        "parameters": {
            "M": M, "N": N, "T": T, "K": K,
            "P_eliminate_vals": P_ELIMINATE_VALS,
            "lambda_select_vals": LAMBDA_SELECT_VALS,
            "sigma_init_vals": SIGMA_INIT_VALS,
            "sigma_noise": SIGMA_NOISE,
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
