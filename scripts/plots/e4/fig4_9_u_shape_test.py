"""Fig 4.9: Strategy complexity-survival U-shape with phase coloring."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({"figure.dpi":150,"savefig.dpi":300,"savefig.bbox":"tight",
    "font.size":11,"axes.titlesize":13,"axes.labelsize":12,
    "xtick.labelsize":10,"ytick.labelsize":10,"legend.fontsize":8,
    "lines.linewidth":1.5,"axes.grid":True,"grid.alpha":0.3})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
from scipy import stats
from collections import defaultdict

PHASE_COLORS = {
    "exploration": "#17becf",
    "burst": "#FFC107",
    "crowding": "#FF5722",
    "decay": "#9C27B0",
    "extinct": "#607D8B",
    "recovery": "#2ca02c",
}


def main(data_dir=None, output_dir=None):
    T_max = 2000  # E4 runs for 2000 periods
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / "results" / "e4_full_evolution" / "p_mut=0.20_lambda=1.00_sigma=0.02_seed=42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = root / "paper" / "thesis" / "figures" / "e4"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)

    families = pd.read_csv(data_dir / "families.csv")
    agents = pd.read_csv(data_dir / "agents.csv")
    weight_cols = [c for c in agents.columns if c.startswith("weight_")]

    # Per-family: complexity = L1-norm of weights, survival = family lifespan
    family_data = {}
    for fid in families["family_id"].unique():
        fam = agents[agents["ancestor_id"] == fid]
        if len(fam) == 0:
            continue
        complexity = np.mean([np.linalg.norm(
            fam[fam["step"]==s][weight_cols].values, ord=1, axis=1).mean()
            for s in fam["step"].unique() if len(fam[fam["step"]==s]) > 0])
        lifespan = fam["step"].max() - fam["step"].min()
        # Dominant phase
        fam_info = families[families["family_id"] == fid]
        phases = fam_info["phase"].value_counts()
        dom_phase = phases.index[0] if len(phases) > 0 else "exploration"
        final_wealth = fam[fam["step"]==fam["step"].max()]["wealth"].sum()
        family_data[fid] = {
            "complexity": complexity, "lifespan": lifespan,
            "phase": dom_phase, "final_wealth": final_wealth,
        }

    # Also grab per-family alpha vs entropy from market data
    df_market = pd.read_csv(data_dir / "market.csv")

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Top-left: complexity vs lifespan scatter with phase colors
    ax = axes[0, 0]
    for phase in ["exploration","burst","crowding","decay","extinct","recovery"]:
        pts = [(d["complexity"], d["lifespan"]) for fid, d in family_data.items()
               if d["phase"] == phase]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, c=PHASE_COLORS[phase], alpha=0.5, s=12, label=phase)
    # Quadratic fit
    all_x = np.array([d["complexity"] for d in family_data.values()])
    all_y = np.array([d["lifespan"] for d in family_data.values()])
    coeffs = np.polyfit(all_x, all_y, 2)
    xs_fit = np.linspace(all_x.min(), all_x.max(), 100)
    ax.plot(xs_fit, np.polyval(coeffs, xs_fit), "k--", lw=2, label="quadratic fit")
    ax.set_xlabel("strategy complexity ($L_1$ norm)")
    ax.set_ylabel("family lifespan (periods)")
    ax.set_title("Complexity-lifespan U-shape by phase")
    ax.legend(fontsize=6, ncol=3)

    # Top-right: |return| vs entropy with phase coloring of families
    ax = axes[0, 1]
    entropy = df_market["strategy_entropy"].dropna().values
    returns = df_market["log_return"].dropna().values
    returns = returns[np.isfinite(returns)]
    min_len = min(len(entropy), len(returns))
    # Color by entropy level: low=red (crowding), high=green (diverse)
    colors = plt.cm.RdYlGn(entropy[:min_len] / entropy[:min_len].max())
    ax.scatter(entropy[:min_len], np.abs(returns[:min_len]),
               c=colors, alpha=0.3, s=10)
    # Quadratic fit
    x = entropy[:min_len]; y = np.abs(returns[:min_len])
    coeffs2 = np.polyfit(x, y, 2)
    xs2 = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs2, np.polyval(coeffs2, xs2), "k--", lw=2)
    ax.set_xlabel("strategy entropy $H_{strat}$")
    ax.set_ylabel("$|r(t)|$")
    ax.set_title("Diversity-extreme event U-shape (E4)")

    # Bottom-left: Alpha vs family complexity
    ax = axes[1, 0]
    cs = [d["complexity"] for d in family_data.values()]
    alphas = []
    for fid in family_data:
        fam = families[families["family_id"] == fid]
        alphas.append(fam["alpha"].dropna().mean())
    ax.scatter(cs, alphas, c="#3182BD", alpha=0.4, s=10)
    ax.set_xlabel("strategy complexity ($L_1$ norm)")
    ax.set_ylabel("mean Alpha")
    ax.set_title("Mean Alpha vs strategy complexity")
    # Add loess-like trend
    sort_idx = np.argsort(cs)
    cs_sorted = np.array(cs)[sort_idx]
    al_sorted = np.array(alphas)[sort_idx]
    window = max(5, len(cs)//20)
    trend = np.convolve(al_sorted, np.ones(window)/window, mode="same")
    ax.plot(cs_sorted, trend, "r-", lw=2)

    # Bottom-right: survival probability by complexity bin
    ax = axes[1, 1]
    bins = np.percentile(all_x, np.linspace(0, 100, 8))
    bin_centers = (bins[:-1] + bins[1:]) / 2
    survival_rates = []
    for i in range(len(bins)-1):
        mask = (all_x >= bins[i]) & (all_x < bins[i+1])
        surv = all_y[mask].mean() / T_max if mask.sum() > 2 else 0
        survival_rates.append(surv)
    ax.bar(range(len(bin_centers)), survival_rates, color="#3182BD", alpha=0.7)
    ax.set_xticks(range(len(bin_centers)))
    ax.set_xticklabels([f"{b:.1f}" for b in bin_centers], fontsize=7)
    ax.set_xlabel("complexity bin center")
    ax.set_ylabel("mean survival rate")
    ax.set_title("Survival rate by complexity bin")

    fig.suptitle("策略复杂度、多样性与生存分析（E4, $p_{mut}=0.20$, $\\lambda=1.0$）",
                 fontsize=15, fontweight="bold")
    fig.tight_layout()
    out = output_dir / "fig4_9_u_shape_test.png"
    fig.savefig(out, dpi=300); plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)

