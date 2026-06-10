"""Fig 1.7: Price deviation from fundamental.
Usage: python fig1_7_price_deviation.py --data-dir <path>
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
    price = df["price"].dropna().values
    fundamental = df["fundamental"].dropna().values
    deviation = np.abs(price - fundamental) / fundamental
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["step"].values, deviation * 100, color="#FD8D3C", linewidth=1.2)
    ax.axhline(y=np.mean(deviation) * 100, color="grey", linestyle="--", alpha=0.5,
               label=f"Mean dev={np.mean(deviation)*100:.2f}%%")
    ax.set_xlabel("Step t"); ax.set_ylabel("Price Deviation |P-F|/F (%)")
    ax.set_title("Figure 1.7: Price Deviation from Fundamental")
    ax.legend()
    fig.savefig(output_dir / "fig1_7_price_deviation.png"); plt.close(fig)
    print("Saved fig1_7")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
