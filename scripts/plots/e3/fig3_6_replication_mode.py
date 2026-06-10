"""Fig 3.6: Replication mode comparison.
Usage: python fig36.py --data-dir <path>
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
    root = Path(__file__).parent.parent.parent.parent
    e3r = root / "results" / "e3_replication"
    subdirs = sorted([d for d in e3r.iterdir() if d.is_dir() and (d / "market.csv").exists()])
    if len(subdirs) < 2: print("Need 2+ directories"); return
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    for ax_i, sd in enumerate(subdirs[:2]):
        df = pd.read_csv(sd/"market.csv")
        axes[ax_i].plot(df["step"],df["strategy_entropy"],color="#3182BD",lw=1.2)
        axes[ax_i].set_title(sd.name[:40]); axes[ax_i].set_xlabel("Step")
        axes[ax_i].set_ylabel("Entropy")
    fig.suptitle("Figure 3.6: Entropy Under Different Replication Modes")
    plt.tight_layout()
    fig.savefig(output_dir/"fig3_6_replication_mode.png");plt.close(fig)
    print("Saved Fig 3.6")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
