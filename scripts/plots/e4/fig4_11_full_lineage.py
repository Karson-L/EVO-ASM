"""Fig 4.11: Strategy family wealth share stacked area chart."""

import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.size": 11, "axes.titlesize": 14, "axes.labelsize": 12,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 8,
    "lines.linewidth": 1.2, "axes.grid": True, "grid.alpha": 0.25,
})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
from matplotlib import cm

TOP_N = 12

PHASE_COLORS = {
    "exploration": "#17becf",
    "burst": "#FFC107",
    "crowding": "#FF5722",
    "decay": "#9C27B0",
    "extinct": "#607D8B",
    "recovery": "#2ca02c",
}


def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / "results" / "e4_full_evolution" / "p_mut=0.20_lambda=1.00_sigma=0.02_seed=42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = root / "paper" / "thesis" / "figures" / "e4"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    families = pd.read_csv(data_dir / "families.csv")
    agents = pd.read_csv(data_dir / "agents.csv")
    all_steps = sorted(families["step"].unique())
    T_max = int(all_steps[-1])

    # Get top N families by final wealth share
    final = families[families["step"] == all_steps[-1]]
    top_ids = final.nlargest(TOP_N, "wealth_share")["family_id"].tolist()

    # Determine dominant strategy type per family from agents
    weight_cols = [c for c in agents.columns if c.startswith("weight_")]
    family_type = {}
    for fid in top_ids:
        fam_agents = agents[agents["ancestor_id"] == fid]
        if len(fam_agents) == 0:
            family_type[fid] = "mixed"
            continue
        mean_w = fam_agents[weight_cols].mean().values
        mean_w = mean_w / (np.linalg.norm(mean_w) + 1e-8)
        # Classify
        w_mom = mean_w[0]
        w_rev = mean_w[5]
        w_fund = mean_w[4]
        w_vol = mean_w[2]
        if w_mom > 0.35:
            family_type[fid] = "momentum"
        elif w_rev > 0.35:
            family_type[fid] = "reversal"
        elif w_fund > 0.35:
            family_type[fid] = "fundamental"
        elif w_vol > 0.35:
            family_type[fid] = "volatility"
        else:
            family_type[fid] = "mixed"

    # Color mapping for strategy types
    type_colors = {
        "momentum": "#E6550D",
        "reversal": "#3182BD",
        "fundamental": "#31A354",
        "volatility": "#756BB1",
        "mixed": "#636363",
    }

    # Build wealth share matrix: steps x top families
    n_steps = len(all_steps)
    matrix = np.zeros((n_steps, len(top_ids)))
    for i, step in enumerate(all_steps):
        step_data = families[families["step"] == step]
        for j, fid in enumerate(top_ids):
            row = step_data[step_data["family_id"] == fid]
            if len(row) > 0:
                matrix[i, j] = float(row["wealth_share"].iloc[0])

    # Other families
    other_share = 1.0 - matrix.sum(axis=1)
    matrix_full = np.column_stack([matrix, other_share])
    all_labels = [str(fid) for fid in top_ids] + ["other"]

    # Colors
    colors = [type_colors.get(family_type.get(fid, "mixed"), "#AAAAAA") for fid in top_ids]
    colors.append("#E0E0E0")  # other

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.stackplot(
        all_steps,
        *[matrix_full[:, j] for j in range(matrix_full.shape[1])],
        labels=all_labels,
        colors=colors,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.3,
    )

    # Mark evolution generations
    K = 200
    for gen_step in range(K, T_max + 1, K):
        ax.axvline(x=gen_step, color="#333333", linewidth=0.6, linestyle="--", alpha=0.4)

    ax.set_xlim(0, T_max)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("$t$ (trading periods)")
    ax.set_ylabel("wealth share")
    ax.set_title(
        f"Top-{TOP_N} strategy family wealth shares ($P_{{\\text{{mut}}}}=0.20$, "
        f"$\\lambda=1.0$, seed=42)",
        fontweight="bold")

    # Legend with strategy types
    from matplotlib.lines import Line2D
    legend_elements = []
    for stype, color in type_colors.items():
        legend_elements.append(
            Line2D([0], [0], color=color, lw=4, label=stype))
    legend_elements.append(
        Line2D([0], [0], color="#E0E0E0", lw=4, label="other families"))
    legend_elements.append(
        Line2D([0], [0], color="#333333", lw=0.6, linestyle="--",
               label="evolution generation ($K=200$)"))
    ax.legend(handles=legend_elements, loc="center left",
              bbox_to_anchor=(1.01, 0.5), fontsize=9, framealpha=0.9)

    # Annotation
    ax.annotate(
        "early exploration:\nwidespread diversity",
        xy=(200, 0.95), fontsize=10, color="#555555",
        ha="center", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    ax.annotate(
        "mid: dominant\nfamilies emerge",
        xy=(900, 0.95), fontsize=10, color="#555555",
        ha="center", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    ax.annotate(
        "late: few families\ncontrol majority wealth",
        xy=(1700, 0.95), fontsize=10, color="#555555",
        ha="center", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

    fig.tight_layout()
    out = output_dir / "fig4_11_full_lineage.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    sz_mb = out.stat().st_size / 1024 / 1024
    print(f"Saved: {out} ({sz_mb:.1f} MB)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
