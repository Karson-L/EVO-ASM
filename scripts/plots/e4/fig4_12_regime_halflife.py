"""Fig 4.12: Regime vs Alpha half-life.
Usage: python fig4_12.py --data-dir <path>
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
    data_sets = []
    labels = []
    for sd in subdirs:
        df=pd.read_csv(sd/"market.csv")
        r=df["log_return"].dropna().values
        r=r[np.isfinite(r)]
        if len(r)>0: data_sets.append(r); labels.append(sd.name[:25])
    ax.boxplot(data_sets, labels=labels)
    ax.set_ylabel("Return Distribution")
    ax.set_title("Figure 4.12: Return Distributions by Regime")
    fig.savefig(output_dir/"fig4_12_regime_halflife.png");plt.close(fig)
    print("Saved Fig 4.12")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
