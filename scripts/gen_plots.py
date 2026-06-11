"""图表生成编排器 — 直接导入版本（避免 subprocess 死锁）。"""
import sys, time, importlib, traceback
from pathlib import Path
import argparse

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")

EXP_MAP = {"e1": "e1_no_evolution", "e2": "e2_capital_expansion",
           "e3": "e3_replication", "e4": "e4_full_evolution"}

PLOT_SCRIPTS = {
    "e1_no_evolution": ["fig1_1_price_fundamental","fig1_2_return_distribution","fig1_3_volatility_clustering","fig1_4_entropy_constant","fig1_5_alpha_heatmap","fig1_6_wealth_gini","fig1_7_price_deviation","fig1_8_efficiency_comparison"],
    "e2_capital_expansion": ["fig2_1_crowding_alpha_dualaxis","fig2_2_crowding_alpha_scatter","fig2_3_elasticity_violin","fig2_4_capital_concentration","fig2_5_entropy_by_elimination","fig2_6_gini_efficiency","fig2_7_halflife_boxplot","fig2_8_survival_curve"],
    "e3_replication": ["fig3_1_family_decay","fig3_2_lineage_tree","fig3_3_dominant_stack","fig3_4_efficiency_selection","fig3_5_entropy_extreme","fig3_6_replication_mode","fig3_7_halflife_selection","fig3_8_max_drawdown"],
    "e4_full_evolution": ["fig4_1_alpha_lifecycle","fig4_2_entropy_grid","fig4_3_phase_transition","fig4_4_complexity_evolution","fig4_5_niche_overlap","fig4_6_offspring_survival","fig4_7_halflife_mutation","fig4_8_interaction_network","fig4_9_u_shape_test","fig4_10_regime_shock","fig4_11_full_lineage","fig4_12_regime_halflife"],
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--experiments", nargs="+", default=["e1","e2","e3","e4"])
    p.add_argument("--results-root", type=str, default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    results_root = Path(args.results_root) if args.results_root else (ROOT / "results")
    selected = [EXP_MAP[e] for e in args.experiments if e in EXP_MAP]

    if args.dry_run:
        for name in selected:
            d = results_root / name
            if d.exists():
                n = len([x for x in d.iterdir() if x.is_dir() and not x.name.startswith("_")])
                print(f"[{name}] {n} dirs x {len(PLOT_SCRIPTS[name])} scripts = {n*len(PLOT_SCRIPTS[name])} charts")
        return

    t0 = time.time()
    total_ok, total_fail = 0, 0
    for name in selected:
        exp_dir = results_root / name
        if not exp_dir.exists():
            print(f"[SKIP] {name}")
            continue
        scripts = PLOT_SCRIPTS.get(name, [])
        exp_tag = name.split("_")[0]
        data_dirs = sorted([d for d in exp_dir.iterdir() if d.is_dir() and not d.name.startswith("_")])
        if not data_dirs:
            print(f"[SKIP] {name} - no data dirs")
            continue
        total = len(data_dirs) * len(scripts)
        print(f"\n==== {name}: {len(data_dirs)} dirs x {len(scripts)} scripts = {total} charts ====")
        ok, fail = 0, 0
        for di, ddir in enumerate(data_dirs):
            out_dir = ddir / "plots"
            out_dir.mkdir(parents=True, exist_ok=True)
            for sname in scripts:
                try:
                    mod = importlib.import_module(f"scripts.plots.{exp_tag}.{sname}")
                    importlib.reload(mod)
                    mod.main(str(ddir), str(out_dir))
                    ok += 1
                except Exception as e:
                    fail += 1
                    if fail <= 5:
                        print(f"  FAIL {sname}: {e}")
            if (di + 1) % 10 == 0:
                elapsed = time.time() - t0
                print(f"  [{name}] {di+1}/{len(data_dirs)} done ({ok} ok, {fail} fail) [{elapsed:.0f}s]")
        print(f"[{name}] Done: {ok}/{total} ok, {fail} fail")
        total_ok += ok
        total_fail += fail

    elapsed = time.time() - t0
    print(f"\n==== ALL DONE ({elapsed:.0f}s): {total_ok} ok, {total_fail} fail ====")

if __name__ == "__main__":
    main()
