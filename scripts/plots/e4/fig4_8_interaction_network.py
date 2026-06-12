"""Fig 4.8: Strategy interaction network (colour-corrected)."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({"figure.dpi":150,"savefig.dpi":300,"savefig.bbox":"tight",
    "font.size":10,"axes.titlesize":12,"axes.labelsize":11,
    "xtick.labelsize":9,"ytick.labelsize":9,"legend.fontsize":9,
    "lines.linewidth":1.5,"axes.grid":False})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
import networkx as nx

TOP_N = 25
POS_THRESH = 0.3    # lowered from 0.5
NEG_THRESH = -0.15  # lowered from -0.3

PHASE_COLORS = {
    "exploration": "#17becf",
    "burst": "#FFC107",
    "crowding": "#FF5722",
    "decay": "#9C27B0",
    "extinct": "#607D8B",
    "recovery": "#2ca02c",
}


def build_family_network(agents, families, step_val):
    weight_cols = [f"weight_{i}" for i in range(6)]
    ag = agents[agents["step"] == step_val].copy()
    ag["family_id"] = ag["ancestor_id"]

    fam_w = ag.groupby("family_id")[weight_cols].mean()
    fam_wealth = ag.groupby("family_id")["wealth"].sum()
    live_ids = set(fam_w.index)

    fam_info = families[families["step"] == step_val].copy()
    fam_info = fam_info[fam_info["family_id"].isin(live_ids)]
    fam_info = fam_info.set_index("family_id")

    if len(fam_info) < 2:
        return None

    w = fam_w.loc[fam_info.index].values
    w = w - w.mean(axis=0, keepdims=True)
    w = w / (np.linalg.norm(w, axis=1, keepdims=True) + 1e-10)
    sim = w @ w.T

    top_n = min(TOP_N, len(fam_info))
    top_ids = fam_info["wealth_share"].nlargest(top_n).index.tolist()
    idx_map = {fid: i for i, fid in enumerate(fam_info.index)}

    G = nx.Graph()
    for fid in top_ids:
        info = fam_info.loc[fid]
        G.add_node(fid, wealth_share=info["wealth_share"],
                   phase=info["phase"], n_agents=int(info["n_agents"]))

    for i, ia in enumerate(top_ids):
        for j, jb in enumerate(top_ids):
            if i >= j:
                continue
            s = sim[idx_map[ia], idx_map[jb]]
            if s > POS_THRESH:
                G.add_edge(ia, jb, weight=s, color="blue")
            elif s < NEG_THRESH:
                G.add_edge(ia, jb, weight=abs(s), color="red")

    return G


def draw_network(G, ax, title):
    pos = nx.spring_layout(G, k=2.5, seed=42, iterations=500)
    node_sizes = [max(G.nodes[n]["wealth_share"] * 18000, 80) for n in G.nodes]
    node_colors = [PHASE_COLORS.get(G.nodes[n]["phase"], "#888888") for n in G.nodes]

    # Edges: red (competition) first, then blue (complementary)
    for etype, ecolor, lw_mult in [("red", "#d62728", 4.0), ("blue", "#1f77b4", 2.5)]:
        edges = [(u, v) for u, v, d in G.edges(data=True) if d["color"] == etype]
        if not edges:
            continue
        widths = [G[u][v]["weight"] * lw_mult for u, v in edges]
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=ecolor,
                               width=widths, alpha=0.5, ax=ax)

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                           edgecolors="#333333", linewidths=0.8, alpha=0.95, ax=ax)

    labels = {n: str(n) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=5, font_color="white",
                            font_weight="bold", ax=ax)

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_axis_off()

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PHASE_COLORS["exploration"],
               markersize=8, label="exploration"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PHASE_COLORS["burst"],
               markersize=8, label="burst"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PHASE_COLORS["crowding"],
               markersize=8, label="crowding"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PHASE_COLORS["decay"],
               markersize=8, label="decay"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PHASE_COLORS["extinct"],
               markersize=8, label="extinct"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PHASE_COLORS["recovery"],
               markersize=8, label="recovery"),
        Line2D([0], [0], color="#d62728", lw=2, label="competition (red)"),
        Line2D([0], [0], color="#1f77b4", lw=2, label="complement (blue)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left",
              fontsize=6, framealpha=0.85, ncol=2)


def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / "results" / "e4_full_evolution" / "baseline_seed42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = root / "paper" / "thesis" / "figures" / "e4"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)

    agents = pd.read_csv(data_dir / "agents.csv")
    families = pd.read_csv(data_dir / "families.csv")
    steps = sorted(families["step"].unique())

    # Use three snapshots: early (step with most phase diversity), mid, late-1
    # Pick step with highest number of non-extinct families
    best_step = steps[0]
    best_n = 0
    for s in steps:
        fam_s = families[families["step"] == s]
        n_alive = (fam_s["phase"] != "extinct").sum()
        if n_alive > best_n:
            best_n = n_alive
            best_step = s

    # Pick 3 diverse snapshots
    idxs = [0, len(steps)//2, -1]
    n_snapshots = len(idxs)
    fig, axes = plt.subplots(1, n_snapshots, figsize=(8*n_snapshots, 8))
    if n_snapshots == 1:
        axes = [axes]

    for ax, si in zip(axes, idxs):
        step = steps[si]
        G = build_family_network(agents, families, int(step))
        if G is None or len(G.nodes) < 2:
            ax.text(0.5, 0.5, f"step={step}: insufficient data", transform=ax.transAxes, ha="center")
            continue
        fam_s = families[families["step"] == step]
        n_alive = (fam_s["phase"] != "extinct").sum()
        draw_network(G, ax, f"$t={step}$ (alive families: {n_alive})")

    fig.suptitle("策略交互网络的时序演化（E4 基线，seed=42）", fontsize=15, fontweight="bold")
    fig.tight_layout()
    out = output_dir / "fig4_8_interaction_network.png"
    fig.savefig(out, dpi=300); plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
