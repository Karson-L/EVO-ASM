import pandas as pd
import numpy as np
import os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(base, 'results', 'e1_no_evolution', 'baseline_seed42', 'market.csv')
print('Reading:', csv_path)
df = pd.read_csv(csv_path)
df['deviation'] = (df['price'] - df['fundamental']).abs() / df['fundamental']
print(f"Steps: {len(df)}")
print(f"Mean deviation: {df['deviation'].mean():.4f}")
print(f"Terminal deviation: {df['deviation'].iloc[-1]:.4f}")
print(f"Last 100 mean: {df['deviation'].iloc[-100:].mean():.4f}")
half = len(df) // 2
print(f"First half mean: {df['deviation'].iloc[:half].mean():.4f}")
print(f"Second half mean: {df['deviation'].iloc[half:].mean():.4f}")
x = np.arange(len(df))
slope = np.polyfit(x, df['deviation'], 1)[0]
print(f"Linear slope per step: {slope:.6f}")
print(f"Slope per 100 steps: {slope*100:.4f}pp")
print(f"Min deviation: {df['deviation'].min():.4f} at step {df['deviation'].idxmin()}")
print(f"Max deviation: {df['deviation'].max():.4f} at step {df['deviation'].idxmax()}")
print(f"First 10: {df['deviation'].iloc[:10].values}")
print(f"Last 10: {df['deviation'].iloc[-10:].values}")
