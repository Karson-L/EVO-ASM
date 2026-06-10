"""
Fig 1.1: Price P(t) vs fundamental F(t).
Usage: python fig1_1_price_fundamental.py --data-dir <path>
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

def main(data_dir=None, output_dir=None):
    root = Path(__file__).parent.parent.parent.parent
    if data_dir is None:
        data_dir = root / 'results' / 'e1_no_evolution' / 'sigma_init=0.10_sigma_noise=0.005_seed=42'
    else:
        data_dir = root / data_dir
    if output_dir is None:
        output_dir = data_dir / 'plots'
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_dir / 'market.csv')
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['step'], df['price'], color='#3182BD', linewidth=1.2, label='Price P(t)')
    ax.plot(df['step'], df['fundamental'], color='#E6550D', linewidth=1.0, alpha=0.8, label='Fundamental F(t)')
    ax.set_xlabel('Step t'); ax.set_ylabel('Price')
    ax.set_title('Figure 1.1: Price vs Fundamental Value (No Evolution Baseline)')
    ax.legend(loc='upper right')
    mean_price = df['price'].mean()
    ax.axhline(y=mean_price, color='grey', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.text(df['step'].max() * 0.98, mean_price * 1.02, f'Mean P={mean_price:.1f}', ha='right', fontsize=9, color='grey')
    fig.savefig(output_dir / 'fig1_1_price_vs_fundamental.png'); plt.close(fig)
    print(f'Saved fig1_1')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', type=str, default=None)
    p.add_argument('--output-dir', type=str, default=None)
    a = p.parse_args()
    main(a.data_dir, a.output_dir)
