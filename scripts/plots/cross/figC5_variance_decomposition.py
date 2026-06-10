"""Fig C.5: Mechanism contribution variance decomposition - Cross-experiment."""
Usage: python figC5_variance_decomposition.py --data-dir <path>
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
    final_entropies = {}
    for label, edir in EXPERIMENTS.items():
        edir_path = root/"results"/edir
        subdirs = sorted([d for d in edir_path.iterdir() if d.is_dir() and (d/"market.csv").exists()])
    if subdirs:
        df = pd.read_csv(subdirs[0]/"market.csv")
        final_entropies[label] = df["strategy_entropy"].iloc[-1]
    mechanisms = ["Crowding","Homogenization","Innovation"]
    contributions = [final_entropies.get("E2",0)-final_entropies.get("E1",0),
                     final_entropies.get("E3",0)-final_entropies.get("E2",0),
                     final_entropies.get("E4",0)-final_entropies.get("E3",0)]
    fig,ax = plt.subplots(figsize=(8,5))
    colors_bar = ["#E6550D","#3182BD","#31A354"]
    ax.bar(mechanisms, contributions, color=colors_bar)
    ax.axhline(y=0,color="grey",lw=0.5)
    ax.set_ylabel("Delta Strategy Entropy")
    ax.set_title("Figure C.5: Mechanism Contribution to Entropy Change")
    fig.savefig(out_dir/"figC5_variance_decomposition.png");plt.close(fig)
    print("Saved Fig C.5")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
