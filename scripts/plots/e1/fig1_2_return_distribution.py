"""
Fig 1.2: Return distribution vs normal.
Usage: python fig1_2_return_distribution.py --data-dir results/e1_no_evolution/baseline_seed42
"""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import matplotlib; matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams.update({'figure.dpi':150,'savefig.dpi':300,'savefig.bbox':'tight',
    'font.size':11,'axes.titlesize':13,'axes.labelsize':12,
    'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':9,
    'lines.linewidth':1.5,'axes.grid':True,'grid.alpha':0.3})

import pandas as pd, matplotlib.pyplot as plt, numpy as np
from scipy import stats

def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / 'results' / 'e1_no_evolution' / 'baseline_seed42'
    else:
        data_dir = root / data_dir
    if output_dir is None:
        output_dir = data_dir / 'plots'
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data_dir / 'market.csv')
    r = df['log_return'].dropna().values
    r = r[np.isfinite(r)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    ax.hist(r, bins=60, density=True, alpha=0.6, color='#3182BD', edgecolor='white', label='Empirical')
    x = np.linspace(r.min(), r.max(), 200)
    mu, sigma = r.mean(), r.std(ddof=1)
    ax.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=1.5, label=f'Normal sigma={sigma:.4f}')
    ax.set_xlabel('Log Return r(t)'); ax.set_ylabel('Density')
    ax.set_title('Return Distribution'); ax.legend()
    ax = axes[1]
    stats.probplot(r, dist='norm', plot=ax)
    ax.get_lines()[0].set_markerfacecolor('#3182BD')
    ax.get_lines()[0].set_markeredgecolor('#3182BD'); ax.get_lines()[0].set_markersize(2)
    ax.get_lines()[1].set_color('#E6550D')
    ax.set_title('Q-Q Plot vs Normal'); ax.set_xlabel('Theoretical Quantiles'); ax.set_ylabel('Sample Quantiles')
    from scipy import stats as st2
    jb = st2.jarque_bera(r)
    skew, kurt = st2.skew(r), st2.kurtosis(r)
    text = f'N={len(r)} skew={skew:.3f} kurt={kurt:.3f} JB={jb.statistic:.1f} p<0.001'
    fig.text(0.5, 0.01, text, ha='center', fontsize=9, color='grey')
    fig.suptitle('Figure 1.2: Return Distribution vs Normal', y=0.98)
    plt.tight_layout(rect=[0,0.04,1,0.95])
    fig.savefig(output_dir / 'fig1_2_return_distribution.png'); plt.close(fig)
    print(f'Saved fig1_2')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', type=str, default=None)
    p.add_argument('--output-dir', type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
