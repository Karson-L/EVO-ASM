"""Fig C.1: Strategy entropy across all experiments - Cross-experiment."""
Usage: python figC1_entropy_all.py --data-dir <path>
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

EXPERIMENTS = {
    "E1": "e1_no_evolution",
    "E2": "e2_capital_expansion",
    "E3": "e3_replication",
    "E4": "e4_full_evolution",
}

def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    out_dir = output_dir if output_dir else root/"results"/"cross_experiment"/"plots"
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    fig,ax = plt.subplots(figsize=(12,6))
    colors = {"E1":"#3182BD","E2":"#E6550D","E3":"#31A354","E4":"#756BB1"}
    for label, edir in EXPERIMENTS.items():
        edir_path = root/"results"/edir
        subdirs = sorted([d for d in edir_path.iterdir() if d.is_dir() and (d/"market.csv").exists()])
        if subdirs:
            df = pd.read_csv(subdirs[0]/"market.csv")
            ax.plot(df["step"],df["strategy_entropy"],color=colors[label],lw=1.5,label=label,alpha=0.8)
    ax.set_xlabel("Step");ax.set_ylabel("Strategy Entropy H_strat")
    ax.set_title("Figure C.1: Strategy Entropy Across All Experiments")
    ax.legend()
    fig.savefig(out_dir/"figC1_entropy_all.png");plt.close(fig)
    print("Saved Fig C.1")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
