"""Fig 3.2: Strategy lineage tree.
Usage: python fig3_2_lineage_tree.py --data-dir <path>
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
                            'font.size': 9, 'axes.titlesize': 12, 'axes.labelsize': 10,
                            'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 9,
                            'lines.linewidth': 1.2, 'axes.grid': True, 'grid.alpha': 0.3})

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.metrics.pairwise import cosine_distances
from collections import defaultdict, Counter


def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / "results" / "e3_replication" / "lambda=1.00_sigma=0.02_noise=0.000_seed=42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = data_dir / "plots"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agents_file = data_dir / "agents.csv"
    families_file = data_dir / "families.csv"
    if not agents_file.exists():
        print("Skip: no agents.csv")
        return

    agents = pd.read_csv(agents_file)
    families = pd.read_csv(families_file) if families_file.exists() else None

    all_steps = sorted(agents["step"].unique())
    if len(all_steps) > 1:
        agents_latest = agents[agents["step"] == all_steps[-1]]
    else:
        agents_latest = agents

    family_ids = sorted(agents_latest["ancestor_id"].unique())
    n_families = len(family_ids)

    if n_families < 2:
        print("Too few families")
        return

    # Build per-family feature vectors from strategy weights
    weight_cols = [c for c in agents.columns if c.startswith("weight_")]
    family_features = {}
    family_phase = {}
    family_wealth = {}
    family_size = {}

    for fid in family_ids:
        fam_agents = agents_latest[agents_latest["ancestor_id"] == fid]
        if len(fam_agents) == 0:
            continue
        vec = fam_agents[weight_cols].mean().values.astype(float)
        vec = np.nan_to_num(vec)
        norm = np.linalg.norm(vec) + 1e-8
        vec = vec / norm
        family_features[fid] = vec
        family_size[fid] = len(fam_agents)
        family_wealth[fid] = fam_agents["wealth"].sum()

    if families is not None:
        for _, row in families.iterrows():
            fid = row["family_id"]
            if fid in family_phase:
                continue
            family_phase[fid] = row.get("phase", "unknown")
            if fid not in family_size:
                family_size[fid] = row.get("n_agents", 0)
                family_wealth[fid] = row.get("total_wealth", 0)

    # Cosine distance + Ward linkage
    fid_list = sorted(family_features.keys())
    feat_matrix = np.array([family_features[f] for f in fid_list])
    dist_matrix = cosine_distances(feat_matrix)
    np.fill_diagonal(dist_matrix, 0.0)
    Z = linkage(squareform(dist_matrix), method='ward')

    # Phase color mapping
    phase_color_map = {
        "expanding": "#1B9E77", "stable": "#7570B3",
        "decay": "#D95F02", "extinct": "#E7298A",
        "decaying": "#D95F02", "exploration": "#66A61E",
        "recovery": "#E6AB02", "crowding": "#A6761D",
        "burst": "#E41A1C"
    }

    # --- Figure ---
    fig = plt.figure(figsize=(18, max(10, n_families * 0.07)))
    gs = fig.add_gridspec(1, 2, width_ratios=[3.5, 1.5], wspace=0.3,
                          left=0.05, right=0.98)

    # Panel 1: Dendrogram
    ax_dend = fig.add_subplot(gs[0])

    top_families = set()
    if family_wealth:
        top20 = sorted(family_wealth.items(), key=lambda x: x[1], reverse=True)[:20]
        top_families = {fid for fid, _ in top20}

    leaf_labels = []
    for fid in fid_list:
        if fid in top_families:
            phase = family_phase.get(fid, "??")
            leaf_labels.append(f"F{fid}\n({phase[:4]})")
        else:
            leaf_labels.append("")

    dendro = dendrogram(Z, labels=leaf_labels,
                        leaf_font_size=6, leaf_rotation=90,
                        link_color_func=lambda k: '#AAAAAA',
                        ax=ax_dend, above_threshold_color='#CCCCCC',
                        color_threshold=0.7 * max(Z[:, 2]))

    for i, label in enumerate(ax_dend.get_xticklabels()):
        try:
            fid = fid_list[i]
            phase = family_phase.get(fid, "unknown")
            label.set_color(phase_color_map.get(phase, "#999999"))
        except Exception:
            pass
        label.set_fontsize(6)

    ax_dend.set_title("Strategy Family Phylogenetic Tree (E3)\n"
                      "(Clustered by strategy weight similarity)", fontsize=12)
    ax_dend.set_ylabel("Strategy Distance", fontsize=10)
    ax_dend.tick_params(axis='y', labelsize=8)

    cutoff = 0.7 * max(Z[:, 2])
    ax_dend.axhline(y=cutoff, c='red', ls='--', lw=1.5, alpha=0.6)
    ax_dend.annotate("Cluster cutoff", (0.02, cutoff * 1.02), fontsize=8,
                     color='red', alpha=0.7, xycoords=('axes fraction', 'data'))

    # Panel 2: Info panel
    ax_info = fig.add_subplot(gs[1])
    ax_info.axis('off')

    y_pos = 0.96
    ax_info.text(0.05, y_pos, "Family Phase Legend:", fontsize=10,
                 fontweight='bold', transform=ax_info.transAxes,
                 verticalalignment='top')
    y_pos -= 0.05

    for phase, color in phase_color_map.items():
        count = sum(1 for f in family_ids if family_phase.get(f, "") == phase)
        if count > 0:
            ax_info.plot([0.08], [y_pos + 0.01], 'o', color=color, markersize=12,
                         transform=ax_info.transAxes, clip_on=False)
            ax_info.text(0.14, y_pos, f"{phase} ({count})", fontsize=8,
                         transform=ax_info.transAxes, verticalalignment='center')
            y_pos -= 0.035

    # Clustering
    n_clusters = min(6, max(2, n_families // 50))
    clusters = fcluster(Z, n_clusters, criterion='maxclust')
    cluster_map = {fid_list[i]: clusters[i] for i in range(len(fid_list))}
    cluster_phases = defaultdict(list)
    for fid, cl in cluster_map.items():
        cluster_phases[cl].append(family_phase.get(fid, "unknown"))

    y_pos -= 0.02
    ax_info.text(0.05, y_pos, f"Strategy Clusters (n={n_clusters}):",
                 fontsize=10, fontweight='bold', transform=ax_info.transAxes,
                 verticalalignment='top')
    y_pos -= 0.05

    for cl in sorted(cluster_phases.keys()):
        phases_in_cl = dict(Counter(cluster_phases[cl]))
        dom_phase = max(phases_in_cl, key=phases_in_cl.get)
        clr = phase_color_map.get(dom_phase, "#999999")
        ax_info.plot([0.08], [y_pos + 0.01], 's', color=clr, markersize=10,
                     transform=ax_info.transAxes, clip_on=False)
        ax_info.text(0.14, y_pos,
                     f"Cluster {cl}: n={len(cluster_phases[cl])} (dominant: {dom_phase})",
                     fontsize=8, transform=ax_info.transAxes,
                     verticalalignment='center')
        y_pos -= 0.03

    # Statistics
    y_pos -= 0.03
    ax_info.text(0.05, y_pos, "Statistics:", fontsize=10, fontweight='bold',
                 transform=ax_info.transAxes, verticalalignment='top')
    y_pos -= 0.04

    stats = [
        f"Total Families: {n_families}",
        f"Time Steps: {all_steps[0]} - {all_steps[-1]}",
        f"Strategy Clusters: {len(cluster_phases)}",
        f"Avg Family Wealth: {np.mean(list(family_wealth.values())):.1f}",
        f"Median Family Size: {np.median(list(family_size.values())):.0f}",
        "",
        "Top 10 Families by Wealth:",
    ]
    top10 = sorted(family_wealth.items(), key=lambda x: x[1], reverse=True)[:10]
    for fid, w in top10:
        phase = family_phase.get(fid, "?")
        stats.append(f"  F{fid}: {w:,.0f} ({phase})")

    for line in stats:
        ax_info.text(0.05, y_pos, line, fontsize=7, fontfamily='monospace',
                     transform=ax_info.transAxes, verticalalignment='top')
        y_pos -= 0.025

    fig.savefig(output_dir / "fig3_2_lineage_tree.png", dpi=300)
    plt.close(fig)
    print(f"Saved Fig 3.2 ({n_families} families, {len(cluster_phases)} clusters)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)
