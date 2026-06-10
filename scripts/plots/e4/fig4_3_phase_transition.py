"""Fig 4.3: Phase transition heatmap.
Usage: python fig4_3.py --data-dir <path>
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
    subdirs = sorted([d for d in e4r.iterdir() if d.is_dir() and (d/"market.csv").exists()])
    if not subdirs: print("No data"); return
    fig,ax = plt.subplots(figsize=(10,8))
    final_entropy = []
    for sd in subdirs:
        df=pd.read_csv(sd/"market.csv")
        final_entropy.append(df["strategy_entropy"].iloc[-1])
    n = int(np.sqrt(len(final_entropy)))
    if n*n <= len(final_entropy):
        data = np.array(final_entropy[:n*n]).reshape(n,n)
        im = ax.imshow(data,aspect="auto",cmap="viridis")
        plt.colorbar(im,ax=ax,label="Final Entropy")
    ax.set_title("Figure 4.3: Phase Transition Heatmap")
    fig.savefig(output_dir/"fig4_3_phase_transition.png");plt.close(fig)
    print("Saved Fig 4.3")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
