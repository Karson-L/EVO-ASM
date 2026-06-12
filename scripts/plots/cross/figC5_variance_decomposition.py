"""Fig C.5: Alpha decay mechanism variance decomposition (cross-experiment)."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({"figure.dpi":150,"savefig.dpi":300,"savefig.bbox":"tight",
    "font.size":11,"axes.titlesize":13,"axes.labelsize":12,
    "xtick.labelsize":10,"ytick.labelsize":10,"legend.fontsize":9,
    "lines.linewidth":1.5,"axes.grid":True,"grid.alpha":0.3})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
from pathlib import Path


BASELINE_DIRS = {
    "E1": "results/e1_no_evolution/baseline_seed42",
    "E2": "results/e2_capital_expansion/p_eliminate=0.05_lambda=1.00_sigma=0.02_seed=42",
    "E3": "results/e3_replication/lambda=1.00_sigma=0.02_noise=0.005_seed=42",
    "E4": "results/e4_full_evolution/baseline_seed42",
}



def find_baseline_data(root, exp_key, exp_dir):
    """Find the baseline run for each experiment."""
    p = root / exp_dir
    if (p / "market.csv").exists():
        return p
    # If exp_dir itself doesn't have data, look for subdirs
    if p.exists():
        subs = sorted([d for d in p.iterdir() if d.is_dir() and (d/"market.csv").exists()])
        if subs:
            return subs[0]
    print(f"  DEBUG {exp_key}: looking in {p}, market.csv exists={(p/'market.csv').exists()}")
    return None


def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    out_dir = root / "paper" / "thesis" / "figures" / "cross"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect metrics from each experiment
    metrics = {}
    for label, rel_path in BASELINE_DIRS.items():
        d = find_baseline_data(root, label, rel_path)
        if d is None:
            print(f"WARNING: no data for {label}")
            continue
        market = pd.read_csv(d / "market.csv")
        families_file = d / "families.csv"
        families = pd.read_csv(families_file) if families_file.exists() else None

        metrics[label] = {
            "final_entropy": market["strategy_entropy"].iloc[-1],
            "initial_entropy": market["strategy_entropy"].iloc[0],
            "entropy_drop": market["strategy_entropy"].iloc[0] - market["strategy_entropy"].iloc[-1],
            "final_gini": market["wealth_gini"].iloc[-1] if "wealth_gini" in market.columns else None,
            "final_rho1": market["acf1"].iloc[-1] if "acf1" in market.columns else None,
        }
        if families is not None:
            last_step = families["step"].max()
            fam_last = families[families["step"] == last_step]
            metrics[label]["n_families_end"] = fam_last["family_id"].nunique()
            metrics[label]["dominant_share"] = fam_last["wealth_share"].max() if "wealth_share" in fam_last.columns else None
            metrics[label]["n_extinct"] = (fam_last["phase"] == "extinct").sum()

    print("Metrics collected:")
    for k, v in metrics.items():
        print(f"  {k}: entropy {v['final_entropy']:.4f}, n_families {v.get('n_families_end','?')}")

    # Decomposition: marginal contributions
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Panel 1: Entropy change decomposition
    ax = axes[0, 0]
    labels = list(metrics.keys())
    if len(labels) == 4:
        contribs = {
            "wealth concentration\n(E1->E2)": metrics["E2"]["final_entropy"] - metrics["E1"]["final_entropy"],
            "replication/homogenization\n(E2->E3)": metrics["E3"]["final_entropy"] - metrics["E2"]["final_entropy"],
            "mutation/innovation\n(E3->E4)": metrics["E4"]["final_entropy"] - metrics["E3"]["final_entropy"],
        }
        colors = ["#E6550D", "#3182BD", "#31A354"]
        bars = ax.bar(range(len(contribs)), list(contribs.values()), color=colors, edgecolor="white")
        ax.axhline(y=0, color="grey", lw=0.8)
        ax.set_xticks(range(len(contribs)))
        ax.set_xticklabels(list(contribs.keys()), fontsize=9)
        ax.set_ylabel("$\\Delta H_{strat}$ (marginal contribution)")
        ax.set_title("Decomposition of strategy entropy change")
        for bar, val in zip(bars, contribs.values()):
            ax.text(bar.get_x() + bar.get_width()/2, val + (0.02 if val>=0 else -0.06),
                    f"{val:+.3f}", ha="center", fontsize=9, fontweight="bold")

    # Panel 2: Final entropy across experiments
    ax = axes[0, 1]
    ents = [metrics[l]["final_entropy"] for l in labels]
    colors2 = ["#7fcdbb", "#2c7fb8", "#fd8d3c", "#e31a1c"]
    ax.bar(labels, ents, color=colors2[:len(labels)], edgecolor="white")
    ax.set_ylabel("final $H_{strat}$")
    ax.set_title("Final strategy entropy by experiment")
    for i, v in enumerate(ents):
        ax.text(i, v+0.02, f"{v:.3f}", ha="center", fontweight="bold")

    # Panel 3: Family count at end
    ax = axes[1, 0]
    if all("n_families_end" in metrics[l] for l in labels):
        nfams = [metrics[l]["n_families_end"] for l in labels]
        ax.bar(labels, nfams, color=colors2[:len(labels)], edgecolor="white")
        ax.set_ylabel("families at $t=T$")
        ax.set_title("Surviving strategy families")
        for i, v in enumerate(nfams):
            ax.text(i, v+1, str(v), ha="center", fontweight="bold")

    # Panel 4: Wealth Gini + dominant share
    ax = axes[1, 1]
    x_pos = np.arange(len(labels))
    width = 0.35
    ginis = [metrics[l].get("final_gini", 0) or 0 for l in labels]
    doms = [metrics[l].get("dominant_share", 0) or 0 for l in labels]
    bars1 = ax.bar(x_pos - width/2, ginis, width, label="wealth Gini",
                   color="#3182BD", edgecolor="white")
    bars2 = ax.bar(x_pos + width/2, doms, width, label="dominant family share",
                   color="#E6550D", edgecolor="white")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.set_ylabel("concentration")
    ax.set_title("Wealth concentration vs dominant family share")
    ax.legend(fontsize=9)

    fig.suptitle("Alpha衰减机制的跨实验分解（基线参数，seed=42）",
                 fontsize=15, fontweight="bold")
    fig.tight_layout()
    out = out_dir / "figC5_variance_decomposition.png"
    fig.savefig(out, dpi=300); plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)


