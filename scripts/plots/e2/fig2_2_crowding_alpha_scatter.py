"""Fig 2.2: Crowding-Alpha scatter.
Usage: python fig_22.py --data-dir <path>
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
    if data_dir is None:
        data_dir = root / "results" / "e2_capital_expansion" / "baseline_seed42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = data_dir / "plots"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data_dir / "market.csv")
    fam_file = data_dir / "families.csv"
    if not fam_file.exists():
        print("families.csv not found, skipping Fig 2.2"); return
    fam = pd.read_csv(fam_file)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(fam["wealth_share"], fam["alpha"], c="#3182BD", alpha=0.5, s=20)
    ax.set_xlabel("Crowding C_k"); ax.set_ylabel("Alpha")
    ax.set_title("Figure 2.2: Crowding vs Alpha Scatter")
    r = np.corrcoef(fam["wealth_share"], fam["alpha"])[0, 1]
    ax.text(0.95, 0.95, f"r={r:.3f}", transform=ax.transAxes, ha="right", va="top")
    fig.savefig(output_dir / "fig2_2_crowding_alpha_scatter.png"); plt.close(fig)
    print("Saved Fig 2.2")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
