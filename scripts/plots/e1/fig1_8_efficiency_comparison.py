"""Fig 1.8: Market efficiency across sigma_noise conditions.
Usage: python fig1_8_efficiency_comparison.py --data-dir <path>
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({'figure.dpi':150,'savefig.dpi':300,'savefig.bbox':'tight',
    'font.size':11,'axes.titlesize':13,'axes.labelsize':12,
    'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':9,
    'lines.linewidth':1.5,'axes.grid':True,'grid.alpha':0.3})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
from scipy import stats

def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    output_dir = Path(output_dir) if output_dir else None
    e1_root = root / "results" / "e1_no_evolution"
    subdirs = sorted([d for d in e1_root.iterdir() if d.is_dir() and (d / "market.csv").exists()])
    if not subdirs:
        print("No valid experiment directories found"); return

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#3182BD", "#E6550D", "#31A354"]
    for i, sd in enumerate(subdirs[:3]):
        df = pd.read_csv(sd / "market.csv")
        acf1 = df["acf1"].dropna().values
        label = sd.name.replace("_", " ")[:45]
        ax.plot(df["step"].values, acf1, color=colors[i % 3], linewidth=1.2, alpha=0.8, label=label)
    ax.axhline(y=0, color="grey", linewidth=0.5)
    ax.set_xlabel("Step t"); ax.set_ylabel("Rolling ACF(1)")
    ax.set_title("Figure 1.8: Market Efficiency ACF(1) Comparison")
    ax.legend(fontsize=8)
    out_dir = output_dir if output_dir else e1_root / "baseline_seed42" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "fig1_8_efficiency_comparison.png"); plt.close(fig)
    print("Saved fig1_8")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
