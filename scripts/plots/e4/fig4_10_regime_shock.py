"""Fig 4.10: Regime shock comparison.
Usage: python fig4_10.py --data-dir <path>
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
        data_dir = root / "results" / "e4_full_evolution" / "baseline_seed42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = data_dir / "plots"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data_dir / "market.csv")
    root = Path(__file__).parent.parent.parent.parent
    e4r = root / "results" / "e4_full_evolution"
    subdirs = sorted([d for d in e4r.iterdir() if d.is_dir() and (d/"market.csv").exists()])[:5]
    if len(subdirs) < 2: print("Need 2+ dirs"); return
    fig,ax = plt.subplots(figsize=(10,5))
    colors = ["#3182BD","#E6550D","#31A354","#756BB1","#FD8D3C"]
    for i,sd in enumerate(subdirs):
        df=pd.read_csv(sd/"market.csv")
        ax.plot(df["step"],df["strategy_entropy"],color=colors[i],lw=1.2,alpha=0.8,label=sd.name[:35])
    ax.set_xlabel("Step");ax.set_ylabel("Strategy Entropy")
    ax.set_title("Figure 4.10: Regime Shock Effects on Entropy")
    ax.legend(fontsize=7)
    fig.savefig(output_dir/"fig4_10_regime_shock.png");plt.close(fig)
    print("Saved Fig 4.10")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
