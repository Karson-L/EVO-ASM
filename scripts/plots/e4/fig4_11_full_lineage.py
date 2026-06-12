"""Fig 4.11: Full strategy family phylogenetic lineage tree (fixed)."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei","Microsoft YaHei","DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({"figure.dpi":150,"savefig.dpi":300,"savefig.bbox":"tight",
    "font.size":8,"axes.titlesize":12,"axes.labelsize":10,
    "xtick.labelsize":7,"ytick.labelsize":8,"legend.fontsize":7,
    "lines.linewidth":0.6,"axes.grid":False})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform
from sklearn.metrics.pairwise import cosine_distances
from collections import defaultdict, Counter

PHASE_COLORS = {
    "exploration": "#17becf",
    "burst": "#FFC107",
    "crowding": "#FF5722",
    "decay": "#9C27B0",
    "extinct": "#607D8B",
    "recovery": "#2ca02c",
}


def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / "results" / "e4_full_evolution" / "p_mut=0.20_lambda=1.00_sigma=0.02_seed=42"
    else:
        data_dir = Path(data_dir)
    if output_dir is None:
        output_dir = root / "paper" / "thesis" / "figures" / "e4"
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)

    agents = pd.read_csv(data_dir / "agents.csv")
    families = pd.read_csv(data_dir / "families.csv")
    all_steps = sorted(agents["step"].unique())
    T_max = int(all_steps[-1])
    weight_cols = [c for c in agents.columns if c.startswith("weight_")]
    print(f"T_max={T_max}, snapshots={len(all_steps)}")

    # Family metadata
    family_ids = sorted(agents["ancestor_id"].unique())
    n_families = len(family_ids)
    family_birth = {}
    family_death = {}
    family_max_size = {}
    for fid in family_ids:
        fam = agents[agents["ancestor_id"] == fid]
        family_birth[fid] = int(fam["step"].min())
        family_death[fid] = int(fam["step"].max())
        family_max_size[fid] = int(fam.groupby("step").size().max())

    alive_at_end = sum(1 for f in family_ids if family_death[f] == T_max)
    print(f"Families: {n_families}, alive at end: {alive_at_end}, extinct: {n_families-alive_at_end}")

    # Family phase lookup
    family_phase = {}
    if families is not None:
        for _, row in families.iterrows():
            family_phase[(int(row["family_id"]), int(row["step"]))] = row["phase"]

    # Family final strategy vectors for clustering
    agents_latest = agents[agents["step"] == all_steps[-1]]
    family_final_vec = {}
    for fid in family_ids:
        fam = agents_latest[agents_latest["ancestor_id"] == fid]
        if len(fam) > 0:
            vec = fam[weight_cols].mean().values.astype(float)
        else:
            last_step = family_death[fid]
            fam = agents[(agents["ancestor_id"] == fid) & (agents["step"] == last_step)]
            vec = fam[weight_cols].mean().values.astype(float) if len(fam) > 0 else np.zeros(len(weight_cols))
        vec = np.nan_to_num(vec)
        family_final_vec[fid] = vec / (np.linalg.norm(vec) + 1e-8)

    # Clustering
    vecs = np.array([family_final_vec[f] for f in family_ids])
    dist = cosine_distances(vecs)
    Z = linkage(squareform(dist, checks=False), method="ward")
    order = leaves_list(Z)
    family_x = {fid: float(px) for px, fid in enumerate(family_ids[o] for o in order)}
    total_x = n_families + 1
    spacing = 1.0

    # Phase bands
    fig, ax = plt.subplots(figsize=(22, 14))
    band_x = total_x + 2.0
    phase_steps = defaultdict(list)
    for s in all_steps:
        phase_counts = Counter()
        for fid in family_ids:
            if family_birth[fid] <= s <= family_death[fid]:
                p = family_phase.get((fid, int(s)), "exploration")
                phase_counts[p] += 1
        if phase_counts:
            dom = phase_counts.most_common(1)[0][0]
            phase_steps[dom].append(int(s))

    for phase, steps_list in phase_steps.items():
        color = PHASE_COLORS.get(phase, "#CCCCCC")
        for s in steps_list:
            ax.fill_betweenx([s-25, s+25], band_x, band_x+0.35, color=color, alpha=0.5)

    ax.text(band_x+0.2, -30, "dominant\nphase", fontsize=7, color="#666666", ha="center")

    # Build reproduction edges
    agent_rows = {}
    for _, row in agents.iterrows():
        agent_rows[(int(row["step"]), int(row["agent_id"]))] = row

    has_parent = agents[agents["parent_id"] >= 0]
    edges = []
    mutation_count = 0

    for _, child_row in has_parent.iterrows():
        child_step = int(child_row["step"])
        parent_aid = int(child_row["parent_id"])
        ancestor = int(child_row["ancestor_id"])

        prev_steps = [s for s in all_steps if s < child_step]
        parent_row = None
        for ps in reversed(prev_steps):
            key = (int(ps), parent_aid)
            if key in agent_rows:
                parent_row = agent_rows[key]
                break

        if parent_row is not None:
            child_vec = child_row[weight_cols].values.astype(float)
            parent_vec = parent_row[weight_cols].values.astype(float)
            diff = np.linalg.norm(child_vec - parent_vec)
            is_mutation = diff > 0.04
            if is_mutation:
                mutation_count += 1
            edges.append((ancestor, int(child_step),
                          int(parent_row["step"]), is_mutation, diff))
        else:
            parent_step = max(ps for ps in prev_steps)
            child_vec = child_row[weight_cols].values.astype(float)
            edges.append((ancestor, int(child_step),
                          int(parent_step), False, 0.0))

    print(f"Edges: {len(edges)}, mutations: {mutation_count}")

    # Determine dominant phase per family
    def get_dominant_phase(fid):
        phases = []
        for s in all_steps:
            if family_birth[fid] <= int(s) <= family_death[fid]:
                p = family_phase.get((fid, int(s)))
                if p:
                    phases.append(p)
        return Counter(phases).most_common(1)[0][0] if phases else "exploration"

    # Draw edges
    for anc, child_step, parent_step, is_mut, diff in edges:
        x_fam = family_x.get(anc, total_x / 2)
        if x_fam is None:
            continue
        if is_mut:
            ax.plot([x_fam, x_fam], [parent_step, child_step],
                    color="#FF6600", linewidth=0.6, alpha=0.7, zorder=3)
            ax.scatter(x_fam, child_step, s=3, color="#FF0000",
                       alpha=0.85, zorder=5, marker="D")
        else:
            ax.plot([x_fam, x_fam], [parent_step, child_step],
                    color="#AAAAAA", linewidth=0.2, alpha=0.35, zorder=1)

    # Family density ribbon for top 30
    top_families = sorted(family_ids, key=lambda f: family_max_size[f], reverse=True)[:30]
    for fid in top_families:
        x = family_x[fid]
        fam_data = agents[agents["ancestor_id"] == fid]
        size_by_step = fam_data.groupby("step").size()
        max_sz = family_max_size[fid]
        phase_color = PHASE_COLORS.get(get_dominant_phase(fid), "#BBBBBB")
        for step_val, sz in size_by_step.items():
            if sz > 1:
                half_w = (sz / max_sz) * spacing * 0.4
                ax.fill_betweenx([int(step_val)-5, int(step_val)+5],
                                 x-half_w, x+half_w, color=phase_color,
                                 alpha=0.25, zorder=0)

    # Birth points
    ax.scatter([family_x[f] for f in family_ids], [0]*n_families,
               s=1.5, color="#333333", alpha=0.5, zorder=3, marker="o")

    # Extinction markers
    extinct_fams = [f for f in family_ids if family_death[f] < T_max]
    if extinct_fams:
        ax.scatter([family_x[f] for f in extinct_fams],
                   [family_death[f] for f in extinct_fams],
                   s=4, color="#E7298A", alpha=0.7, zorder=6, marker="X",
                   label=f"extinction ({len(extinct_fams)})")

    # Grid
    for step in all_steps:
        ax.axhline(y=int(step), color="#E0E0E0", linewidth=0.25, alpha=0.3, zorder=0)
    for step in [0, 400, 800, 1200, 1600, 1999]:
        ax.text(total_x+0.6, step, f"t={step}", fontsize=7, color="#555555", va="center")

    # Styling
    ax.set_xlim(-0.5, band_x+1.2)
    ax.set_ylim(T_max+40, -40)
    ax.set_xlabel("strategy families (clustered by cosine distance)", fontsize=10)
    ax.set_ylabel("$t$", fontsize=10)
    ax.set_title(
        f"Full strategy family phylogenetic tree (E4, $p_{{mut}}=0.20$, "
        f"$\\lambda=1.0$, seed=42)\n"
        f"T={T_max+1} periods, {n_families} families, {len(edges)} reproduction edges, "
        f"{mutation_count} mutation nodes",
        fontsize=13, fontweight="bold")

    from matplotlib.lines import Line2D
    legend_elements = []
    for phase, color in PHASE_COLORS.items():
        legend_elements.append(Line2D([0],[0], marker="o", color="w",
            markerfacecolor=color, markersize=7, label=phase))
    legend_elements.append(Line2D([0],[0], marker="D", color="w",
        markerfacecolor="#FF0000", markersize=7, label=f"mutation ({mutation_count})"))
    if extinct_fams:
        legend_elements.append(Line2D([0],[0], marker="X", color="w",
            markeredgecolor="#E7298A", markerfacecolor="#E7298A",
            markersize=7, label=f"extinct ({len(extinct_fams)})"))
    ax.legend(handles=legend_elements, loc="upper right", fontsize=7,
              ncol=2, framealpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelbottom=False)

    out = output_dir / "fig4_11_full_lineage.png"
    fig.savefig(out, dpi=300); plt.close(fig)
    sz_mb = out.stat().st_size/1024/1024
    print(f"Saved: {out} ({sz_mb:.1f} MB)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    a = p.parse_args(); main(a.data_dir, a.output_dir)

