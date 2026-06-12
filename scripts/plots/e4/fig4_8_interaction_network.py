# -*- coding: utf-8 -*-
"""Fig 4.8: Strategy interaction network.

节点大小表示财富占比，边表示策略间的竞争（红色）或互补（蓝色）关系。
网络结构随时间从分散的小团体演化为围绕少数核心家族的星形结构。

Usage: python fig4_8_interaction_network.py --data-dir <path>
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({'figure.dpi':150,'savefig.dpi':300,'savefig.bbox':'tight',
    'font.size':10,'axes.titlesize':12,'axes.labelsize':11,
    'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,
    'lines.linewidth':1.5,'axes.grid':False})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
import networkx as nx

TOP_N = 30          # show top N families by wealth
POS_THRESH = 0.5    # similarity above this = complementary (blue)
NEG_THRESH = -0.3   # similarity below this = competitive (red)


def build_family_network(agents, families):
    """Aggregate agent weight vectors by family (ancestor_id), compute
    pairwise cosine similarity, and return a networkx graph with edge
    colour / width attributes."""
    weights_cols = [f"weight_{i}" for i in range(6)]
    agents = agents.copy()
    agents["family_id"] = agents["ancestor_id"]

    # per-family aggregates (only families present in agents)
    fam_w = agents.groupby("family_id")[weights_cols].mean()
    fam_wealth = agents.groupby("family_id")["wealth"].sum()
    live_ids = set(fam_w.index)

    # merge with families.csv metadata
    fam_info = families[["family_id","wealth_share","phase","n_agents"]].copy()
    fam_info = fam_info[fam_info["family_id"].isin(live_ids)]
    fam_info = fam_info.set_index("family_id")

    # centre then normalise weight vectors (allows negative cosine)
    w = fam_w.values
    w = w - w.mean(axis=0, keepdims=True)
    w = w / (np.linalg.norm(w, axis=1, keepdims=True) + 1e-10)
    sim = w @ w.T   # cosine similarity (signed)

    # select top families by wealth_share
    top_ids = fam_info["wealth_share"].nlargest(min(TOP_N, len(fam_info))).index.tolist()
    top_idx = [list(fam_w.index).index(fid) for fid in top_ids]

    G = nx.Graph()
    for fid in top_ids:
        info = fam_info.loc[fid]
        G.add_node(fid, wealth_share=info["wealth_share"],
                   phase=info["phase"], n_agents=int(info["n_agents"]))

    # add edges
    for i, ia in enumerate(top_ids):
        for j, jb in enumerate(top_ids):
            if i >= j:
                continue
            s = sim[top_idx[i], top_idx[j]]
            if s > POS_THRESH:
                G.add_edge(ia, jb, weight=s, color="blue")
            elif s < NEG_THRESH:
                G.add_edge(ia, jb, weight=abs(s), color="red")

    return G


def draw_network(G, ax, title):
    """Draw the network on the given axes."""
    pos = nx.spring_layout(G, k=1.8, seed=42, iterations=300)
    node_sizes = [G.nodes[n]["wealth_share"] * 18000 for n in G.nodes]

    # node colours by phase
    phase_colors = {"crowding": "#2ca02c", "extinct": "#d62728",
                    "growing": "#1f77b4", "stable": "#ff7f0e"}
    node_colors = [phase_colors.get(G.nodes[n]["phase"], "#888888") for n in G.nodes]

    # draw edges - red first, then blue on top for cleaner look
    for edge_type, edge_color in [("red", "#d62728"), ("blue", "#1f77b4")]:
        edges = [(u, v) for u, v, d in G.edges(data=True) if d["color"] == edge_type]
        if not edges:
            continue
        widths = [G[u][v]["weight"] * 3.0 for u, v in edges]
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=edge_color,
                               width=widths, alpha=0.45, ax=ax)

    # draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                           edgecolors="#333333", linewidths=0.6, alpha=0.9, ax=ax)

    # labels: family_id
    labels = {n: str(n) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=6, font_color="white",
                            font_weight="bold", ax=ax)

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_axis_off()

    # custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ca02c',
               markersize=10, label='拥挤期 (crowding)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#1f77b4',
               markersize=10, label='成长期 (growing)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff7f0e',
               markersize=10, label='稳定期 (stable)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#d62728',
               markersize=10, label='灭绝期 (extinct)'),
        Line2D([0], [0], color='#d62728', lw=2, label='竞争 (competition)'),
        Line2D([0], [0], color='#1f77b4', lw=2, label='互补 (complement)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left',
              fontsize=7, framealpha=0.8, ncol=2)


def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / "results" / "e4_full_evolution" / "baseline_seed42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = data_dir / "plots"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)

    agents_file = data_dir / "agents.csv"
    families_file = data_dir / "families.csv"
    if not agents_file.exists():
        print("agents.csv not found in %s" % data_dir); return

    agents = pd.read_csv(agents_file)
    families = pd.read_csv(families_file)

    # Check for multi-step: use families to get available steps
    steps = sorted(families["step"].unique())
    print("Available steps in families.csv: %d" % len(steps))

    if len(steps) == 1:
        # single snapshot
        step = steps[0]
        fam_step = families[families["step"] == step]
        ag_step = agents[agents["step"] == step]
        G = build_family_network(ag_step, fam_step)
        fig, ax = plt.subplots(figsize=(12, 10))
        draw_network(G, ax, "策略交互网络 (step=%d)" % step)
        fig.savefig(output_dir / "fig4_8_interaction_network.png")
        plt.close(fig)
        print("Saved Fig 4.8 -> %s" % (output_dir / "fig4_8_interaction_network.png"))
    else:
        # multi-step: pick early, mid, late snapshots
        n_steps = len(steps)
        idxs = [0, n_steps // 2, n_steps - 1]
        fig, axes = plt.subplots(1, 3, figsize=(24, 8))
        for ax, si in zip(axes, idxs):
            step = steps[si]
            fam_step = families[families["step"] == step]
            ag_step = agents[agents["step"] == step]
            G = build_family_network(ag_step, fam_step)
            draw_network(G, ax, "step=%d" % step)
        fig.suptitle("策略交互网络的时间演化", fontsize=15, fontweight="bold")
        fig.tight_layout()
        fig.savefig(output_dir / "fig4_8_interaction_network.png")
        plt.close(fig)
        print("Saved Fig 4.8 -> %s" % (output_dir / "fig4_8_interaction_network.png"))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
