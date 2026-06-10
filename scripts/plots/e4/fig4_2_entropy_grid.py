"""Fig 4.2: Entropy grid by mutation rate.
Usage: python fig4_2.py --data-dir <path>
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
    subdirs = sorted([d for d in e4r.iterdir() if d.is_dir() and (d/"market.csv").exists()])[:16]
    if not subdirs: print("No data"); return
    n = len(subdirs); cols=4; rows=(n+cols-1)//cols
    fig,axes = plt.subplots(rows,cols,figsize=(16,3*rows))
    axes = axes.flatten() if rows>1 else [axes] if cols==1 else axes
    for i,sd in enumerate(subdirs):
        df=pd.read_csv(sd/"market.csv")
        axes[i].plot(df["step"],df["strategy_entropy"],color="#3182BD",lw=0.8)
        axes[i].set_title(sd.name[:35],fontsize=8)
    for j in range(i+1,len(axes)): axes[j].set_visible(False)
    fig.suptitle("Figure 4.2: Strategy Entropy Across Mutation Rates")
    plt.tight_layout()
    out_dir = output_dir if output_dir else e4r/"baseline_seed42"/"plots"
    out_dir.mkdir(parents=True,exist_ok=True)
    fig.savefig(out_dir/"fig4_2_entropy_grid.png");plt.close(fig)
    print("Saved Fig 4.2")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
