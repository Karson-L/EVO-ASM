"""Fig 1.5: Strategy family weight profiles.
Usage: python fig1_5_alpha_heatmap.py --data-dir <path>
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
        data_dir = root / "results" / "e1_no_evolution" / "baseline_seed42"
    else:
        data_dir = root / data_dir
    if output_dir is None:
        output_dir = data_dir / "plots"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data_dir / "market.csv")
    agents_file = data_dir / "agents.csv"
    if not agents_file.exists():
        print("agents.csv not found, skipping Fig 1.5"); return
    agents_df = pd.read_csv(agents_file)
    family_ids = agents_df["ancestor_id"].values
    weights = agents_df[[f"weight_{i}" for i in range(6)]].values
    unique_families = sorted(np.unique(family_ids))
    nf = len(unique_families)
    fam_matrix = np.zeros((nf, 6))
    for fi, fid in enumerate(unique_families):
        fam_matrix[fi] = weights[family_ids == fid].mean(axis=0)

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(fam_matrix.T, aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xlabel("Strategy Family (ancestor_id)"); ax.set_ylabel("Signal Dimension")
    ax.set_title("Figure 1.5: Strategy Family Weight Profiles")
    plt.colorbar(im, ax=ax, label="Mean Weight")
    fig.savefig(output_dir / "fig1_5_alpha_heatmap.png"); plt.close(fig)
    print("Saved fig1_5")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
