"""Fig 3.5: Entropy vs extreme events.
Usage: python fig35.py --data-dir <path>
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
        data_dir = root / "results" / "e3_replication" / "baseline_seed42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = data_dir / "plots"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data_dir / "market.csv")
    entropy = df["strategy_entropy"].dropna().values
    returns = df["log_return"].dropna().values
    returns = returns[np.isfinite(returns)]
    min_len = min(len(entropy), len(returns))
    fig, ax = plt.subplots(figsize=(8,6))
    ax.scatter(entropy[:min_len], np.abs(returns[:min_len]), c="#E6550D", alpha=0.3, s=10)
    ax.set_xlabel("Strategy Entropy");ax.set_ylabel("|Return|")
    ax.set_title("Figure 3.5: Entropy vs Return Magnitude")
    fig.savefig(output_dir/"fig3_5_entropy_extreme.png");plt.close(fig)
    print("Saved Fig 3.5")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
