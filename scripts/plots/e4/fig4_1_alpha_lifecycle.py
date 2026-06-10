"""Fig 4.1: Alpha lifecycle.
Usage: python fig4_1.py --data-dir <path>
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
    fam_file = data_dir / "families.csv"
    if not fam_file.exists(): print("Skip"); return
    fam = pd.read_csv(fam_file)
    fig,ax1 = plt.subplots(figsize=(10,5))
    t = np.arange(len(fam))
    ax1.plot(t,fam["alpha"].values if "alpha" in fam.columns else fam["wealth_share"].values,color="#3182BD",lw=1.2)
    ax1.set_xlabel("Step");ax1.set_ylabel("Alpha",color="#3182BD")
    if "wealth_share" in fam.columns:
        ax2=ax1.twinx();ax2.plot(t,fam["wealth_share"].values,color="#E6550D",lw=1.2,alpha=0.6)
        ax2.set_ylabel("Crowding",color="#E6550D")
    ax1.set_title("Figure 4.1: Alpha Lifecycle")
    fig.savefig(output_dir/"fig4_1_alpha_lifecycle.png");plt.close(fig)
    print("Saved Fig 4.1")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
