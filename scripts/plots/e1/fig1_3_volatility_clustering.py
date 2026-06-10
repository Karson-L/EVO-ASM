"""Fig 1.3: Volatility clustering ACF.
Usage: python fig1_3_volatility_clustering.py --data-dir <path>
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
    r = df["log_return"].dropna().values
    r = r[np.isfinite(r)]
    abs_r = np.abs(r)
    max_lag = min(50, len(abs_r) // 4)
    acf_vals = [np.corrcoef(abs_r[lag:], abs_r[:-lag])[0, 1] for lag in range(1, max_lag + 1)]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#3182BD" if v > 0.05 else "#E6550D" for v in acf_vals]
    ax.bar(range(1, max_lag + 1), acf_vals, color=colors, alpha=0.7, width=0.8)
    ax.axhline(y=0, color="grey", linewidth=0.5)
    n = len(abs_r); sig = 1.96 / np.sqrt(n)
    ax.axhline(y=sig, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axhline(y=-sig, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Lag"); ax.set_ylabel("Autocorrelation of |r(t)|")
    ax.set_title("Figure 1.3: Volatility Clustering (ACF of Absolute Returns)")
    fig.savefig(output_dir / "fig1_3_volatility_clustering.png"); plt.close(fig)
    print("Saved fig1_3")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
