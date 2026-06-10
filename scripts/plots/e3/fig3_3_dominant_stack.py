"""Fig 3.3: Dominant strategy stack.
Usage: python fig33.py --data-dir <path>
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
    fam_file = data_dir / "families.csv"
    if not fam_file.exists(): print("No families.csv"); return
    fam = pd.read_csv(fam_file)
    fig, ax = plt.subplots(figsize=(10,5))
    top = fam.nlargest(5, "wealth_share") if "wealth_share" in fam.columns else fam.head(5)
    ax.bar(range(len(top)), top["wealth_share"].values if "wealth_share" in top.columns else [1]*len(top),
           color=["#3182BD","#E6550D","#31A354","#756BB1","#FD8D3C"])
    ax.set_xlabel("Family Rank");ax.set_ylabel("Wealth Share")
    ax.set_title("Figure 3.3: Top Strategy Families by Wealth")
    fig.savefig(output_dir/"fig3_3_dominant_stack.png");plt.close(fig)
    print("Saved Fig 3.3")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
