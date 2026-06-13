"""Fig C.5 revised: Within-experiment entropy decomposition.
Decomposes strategy entropy decline within a single E4 run
into crowding (wealth concentration), homogenization (replication/selection),
and innovation (mutation) effects.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({'figure.dpi':150,'savefig.dpi':300,'savefig.bbox':'tight',
    'font.size':11,'axes.titlesize':13,'axes.labelsize':12,
    'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':9,
    'lines.linewidth':1.5,'axes.grid':True,'grid.alpha':0.3})

import pandas as pd, matplotlib.pyplot as plt, numpy as np, math

ROOT = Path(__file__).parent.parent.parent.parent
RUN_DIR = ROOT/"results"/"e4_full_evolution"/"p_mut=0.20_lambda=1.00_sigma=0.02_seed=42"

def main():
    mkt = pd.read_csv(RUN_DIR/"market.csv")
    agt = pd.read_csv(RUN_DIR/"agents.csv", dtype={"agent_id":int,"ancestor_id":int,"parent_id":int})
    
    H_0 = mkt["strategy_entropy"].iloc[0]
    H_T = mkt["strategy_entropy"].iloc[-1]
    F_0 = mkt["n_families"].iloc[0]
    F_T = mkt["n_families"].iloc[-1]
    total_decay = H_T - H_0
    
    # Factor 1: Crowding - within-survivor agent concentration
    crowding = H_T - math.log(F_T)
    
    # Factor 2: Homogenization base - family extinction
    homog_base = math.log(F_T) - math.log(F_0)
    
    # Factor 3: Innovation - how much entropy mutation preserves
    final_agt = agt[agt.step == agt.step.max()]
    nm = final_agt[final_agt.ancestor_id == final_agt.agent_id]
    nm_counts = nm.groupby("ancestor_id").size()
    n_nm = len(nm)
    H_nm = 0.0
    for c in nm_counts.values:
        p = c / n_nm
        if p > 0:
            H_nm -= p * math.log(p)
    innovation = H_T - H_nm
    
    # Pure homogenization (without innovation benefit)
    homogenization = homog_base - innovation
    
    print(f"Total decay: {total_decay:.4f}")
    print(f"Crowding: {crowding:.4f}")
    print(f"Homogenization: {homogenization:.4f}")
    print(f"Innovation: +{innovation:.4f}")
    print(f"Sum: {crowding + homogenization + innovation:.4f}")
    
    # ---- Plot ----
    mechanisms = ["Wealth Concentration\n(Crowding)",
                  "Replication\n(Homogenization)",
                  "Innovation\n(Mutation)"]
    contributions = [crowding, homogenization, innovation]
    colors_bar = ["#E6550D","#3182BD","#31A354"]
    
    fig,ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(mechanisms, contributions, color=colors_bar, width=0.55,
                  edgecolor="white", linewidth=0.8)
    ax.axhline(y=0, color="grey", lw=0.5)
    ax.set_ylabel("Contribution to ΔH (nats)")
    ax.set_title("Figure C.5: Entropy Decomposition — E4 ($p_{mut}=0.20$, $\\sigma=0.02$, seed=42)")
    
    for bar, val in zip(bars, contributions):
        y_pos = val + 0.03 if val >= 0 else val - 0.08
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, f"{val:+.3f}",
                ha='center', va='bottom' if val >= 0 else 'top',
                fontsize=10, fontweight='bold')
    
    ax.text(0.5, 0.02,
            f"Total entropy decline: ΔH = {total_decay:.3f} nats\n"
            f"($F$: {F_0} → {F_T} families, $N$ = 500 agents)",
            transform=ax.transAxes, ha='center', va='bottom', fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
    
    out_dir = ROOT/"results"/"cross_experiment"/"plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir/"figC5_variance_decomposition.png")
    
    paper_dir = ROOT/"paper"/"thesis"/"figures"/"cross"
    paper_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(paper_dir/"figC5_variance_decomposition.png")
    plt.close(fig)
    print(f"Saved to {out_dir/'figC5_variance_decomposition.png'}")
    print(f"Saved to {paper_dir/'figC5_variance_decomposition.png'}")

if __name__ == "__main__":
    main()
