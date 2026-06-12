"""Fig 1.1: Price P(t) vs fundamental F(t) - E1 baseline."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({"figure.dpi":150,"savefig.dpi":300,"savefig.bbox":"tight",
    "font.size":11,"axes.titlesize":13,"axes.labelsize":12,
    "xtick.labelsize":10,"ytick.labelsize":10,"legend.fontsize":9,
    "lines.linewidth":1.5,"axes.grid":True,"grid.alpha":0.3})

import pandas as pd, matplotlib.pyplot as plt, numpy as np

def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / "results" / "e1_no_evolution" / "baseline_seed42"
    else:
        data_dir = root / data_dir
    if output_dir is None:
        output_dir = root / "paper" / "thesis" / "figures" / "e1"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_dir / "market.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["step"], df["price"], color="#3182BD", linewidth=1.8,
            label="市场价格 $P(t)$", zorder=3)
    ax.plot(df["step"], df["fundamental"], color="#E6550D", linewidth=1.5,
            linestyle="--", alpha=0.85, label="基础价值 $F(t)$", zorder=2)
    ax.fill_between(df["step"], df["price"], df["fundamental"],
                    where=df["price"] >= df["fundamental"],
                    color="#3182BD", alpha=0.08, interpolate=True)
    ax.fill_between(df["step"], df["price"], df["fundamental"],
                    where=df["price"] < df["fundamental"],
                    color="#E6550D", alpha=0.08, interpolate=True)
    ax.set_xlabel("$t$"); ax.set_ylabel("价格")
    ax.set_title("市场价格与基础价值时序对比（E1 基线，seed=42）")
    ax.legend(loc="upper left", framealpha=0.9)
    p0, p_end = df["price"].iloc[0], df["price"].iloc[-1]
    f0, f_end = df["fundamental"].iloc[0], df["fundamental"].iloc[-1]
    ax.annotate(f"$P_0={p0:.1f}$", xy=(0, p0), xytext=(30, p0+2),
                arrowprops=dict(arrowstyle="->", color="#3182BD"),
                fontsize=8, color="#3182BD")
    ax.annotate(f"$F_T={f_end:.1f}$", xy=(df["step"].iloc[-1], f_end),
                xytext=(df["step"].iloc[-1]-200, f_end+3),
                arrowprops=dict(arrowstyle="->", color="#E6550D"),
                fontsize=8, color="#E6550D")
    out = output_dir / "fig1_1_price_vs_fundamental.png"
    fig.savefig(out, dpi=300); plt.close(fig)
    print(f"Saved: {out}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
