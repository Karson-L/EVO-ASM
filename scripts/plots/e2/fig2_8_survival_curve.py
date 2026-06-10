"""Fig 2.8: Strategy family survival curve.
Usage: python fig_28.py --data-dir <path>
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
    agents_file = data_dir / "agents.csv"
    if not agents_file.exists():
        print("agents.csv not found, skipping Fig 2.8"); return
    agents = pd.read_csv(agents_file)
    fig, ax = plt.subplots(figsize=(8, 6))
    if "age" in agents.columns:
        ages = agents["age"].dropna().values
        ax.hist(ages, bins=30, color="#31A354", alpha=0.7, edgecolor="white")
        ax.set_xlabel("Agent Age"); ax.set_ylabel("Count")
    ax.set_title("Figure 2.8: Agent Survival Distribution")
    fig.savefig(output_dir / "fig2_8_survival_curve.png"); plt.close(fig)
    print("Saved Fig 2.8")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
