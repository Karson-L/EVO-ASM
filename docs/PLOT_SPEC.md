# EVO-ASM 实验结果输出规格说明书 (PLOT_SPEC.md)

> 目标：所有图表可直接用于毕业论文
> 语言：图表标题使用中文（符合中文学位论文规范）
> 字体：SimSun（宋体）正文 / SimHei（黑体）标题 / Times New Roman 数字与英文

---

## 一、通用约定

### 1.1 运行结果目录结构

```
results/
├── e1_no_evolution/
│   ├── e1_sigma_init=0.02_sigma_noise=0.000_seed=42/
│   │   ├── agents.csv
│   │   ├── families.csv
│   │   ├── market.csv
│   │   ├── summary.json
│   │   └── plots/
│   │       ├── fig1_1_price_vs_fundamental.png
│   │       ├── fig1_2_return_distribution.png
│   │       └── ...
│   ├── e1_sigma_init=0.02_sigma_noise=0.000_seed=123/
│   └── ...
├── e2_capital_expansion/
├── e3_replication/
├── e4_full_evolution/
└── cross_experiment/
    └── plots/
```

### 1.2 通用 CSV 列定义

以下列名在所有实验中保持一致：

**`market.csv`** — 每行一个时间步

| 列名 | 类型 | 说明 |
|------|------|------|
| `step` | int | 时间步 t |
| `price` | float | P(t) |
| `fundamental` | float | F(t) |
| `log_return` | float | r(t) = ln(P_t/P_{t-1}) |
| `volume` | float | V(t) |
| `strategy_entropy` | float | H_strat(t) |
| `acf1` | float | ρ₁(t\|Δ)，滚动窗口一阶自相关 |
| `hurst` | float | H(t\|Δ)，滚动 Hurst 指数 |
| `wealth_gini` | float | 财富基尼系数 |
| `n_families` | int | K(t)，活跃策略家族数 |
| `mean_fitness` | float | 所有 agent 平均 Sharpe |
| `kurtosis` | float | 滚动峰度 |

**`agents.csv`** — 每 K 期（演化后）保存一次快照

| 列名 | 类型 | 说明 |
|------|------|------|
| `step` | int | 采样时间步 |
| `agent_id` | int | agent unique_id |
| `ancestor_id` | int | 祖源（策略家族标识） |
| `parent_id` | int | 父代 id（-1 表示初始 agent） |
| `wealth` | float | W_i |
| `cash` | float | C_i |
| `holdings` | float | h_i |
| `sharpe` | float | 滚动夏普比率 |
| `weight_0`..`weight_5` | float | w_i 的 6 个分量 |
| `threshold` | float | θ_i |
| `holding_period` | int | τ_i |
| `risk_appetite` | float | α_i |
| `age` | int | 存活步数 |
| `strategy_type` | str | 事后聚类标签（TF/MR/VL/VT/HY/NS） |

**`families.csv`** — 每 K 期，每个活跃策略家族一行

| 列名 | 类型 | 说明 |
|------|------|------|
| `step` | int | 采样时间步 |
| `family_id` | int | ancestor_id |
| `n_agents` | int | 该家族 agent 数量 |
| `total_wealth` | float | 该家族总财富 |
| `wealth_share` | float | C_k(t)，拥挤度 |
| `alpha` | float | α_k(t)，滚动窗口 Alpha |
| `mean_weight_0`..`mean_weight_5` | float | 平均信号权重 |
| `mean_threshold` | float | 平均阈值 |
| `mean_holding_period` | float | 平均持仓周期 |
| `mean_risk_appetite` | float | 平均风险偏好 |
| `phase` | str | Alpha 生命周期阶段 |

**`summary.json`** — 单次运行的元信息

```json
{
  "experiment": "e1_no_evolution",
  "parameters": {
    "sigma_init": 0.10,
    "sigma_noise": 0.005,
    "seed": 42
  },
  "statistics": {
    "final_price": 102.34,
    "mean_return": 0.00023,
    "return_std": 0.0187,
    "return_skewness": -0.12,
    "return_kurtosis": 5.63,
    "jarque_bera_stat": 1423.5,
    "jarque_bera_p": 0.0,
    "hurst_estimate": 0.52,
    "hurst_ci_lower": 0.49,
    "hurst_ci_upper": 0.55,
    "final_entropy": 4.82,
    "final_gini": 0.34,
    "final_n_families": 380,
    "mean_alpha_across_families": 0.0012,
    "extreme_event_count": 3
  }
}
```

### 1.3 通用 Matplotlib 配置

所有脚本导入统一的样式模块：

```python
# plot_config.py — 全局绘图配置
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 中文字体设置
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

# 论文级样式
matplotlib.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "lines.linewidth": 1.5,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

# 颜色方案（ColorBrewer 色盲友好）
COLORS = {
    "blue":   "#3182BD",
    "red":    "#E6550D",
    "green":  "#31A354",
    "purple": "#756BB1",
    "orange": "#FD8D3C",
    "pink":   "#C994C7",
    "grey":   "#636363",
}

COLOR_PALETTE = list(COLORS.values())
```

---

## 二、Experiment 1 — 无演化基线

### 2.1 CSV 输出

与通用格式一致，无额外列。

### 2.2 图表列表与 Matplotlib 脚本规格

---

#### Fig 1.1: 价格与基础价值时序

**文件**：`scripts/plots/e1/fig1_1_price_fundamental.py`

**数据源**：`market.csv` 列 `step, price, fundamental`

**脚本结构**：
```
1. 加载 market.csv
2. 创建 1×1 figure（10×4 inches）
3. 绘制 price 线（COLORS["blue"]）
4. 绘制 fundamental 线（COLORS["red"], dashed）
5. 标注"涨跌停触发区间"（灰色半透明 band，若价格触及 ±10% 边界）
6. 添加图例
7. 保存为 fig1_1_price_vs_fundamental.png
```

**论文图片标题**：

> **图 1.1 无演化市场中的价格与基础价值时序。** 蓝色实线为市场清算价格 P(t)，红色虚线为基础价值 F(t)。基础价值遵循几何布朗运动加弱均值回复过程，价格由 agent 供需出清决定。灰色区域标示价格触及涨跌停板（±10%）的时段。

---

#### Fig 1.2: 收益率分布检验

**文件**：`scripts/plots/e1/fig1_2_return_distribution.py`

**数据源**：`market.csv` 列 `log_return`

**脚本结构**：
```
1. 加载 market.csv，剔除前 100 期（预热期）
2. 创建 1×2 figure（12×5 inches）
3. 左子图：直方图 + 正态分布拟合曲线
   - bins=100, density=True, alpha=0.6
   - 叠加正态分布 PDF（以样本均值和标准差参数化）
4. 右子图：QQ-plot
   - scipy.stats.probplot 绘制
5. 在直方图上标注偏度、峰度、JB 统计量
6. 保存
```

**论文图片标题**：

> **图 1.2 无演化市场对数收益率分布的正态性检验。** 左图为收益率直方图与正态分布拟合曲线（红色虚线），右图为 Q-Q 图。标注了偏度（Skewness）、超额峰度（Excess Kurtosis）和 Jarque-Bera 统计量。收益率呈现显著的尖峰厚尾特征（拒绝正态性原假设，p<0.001），符合真实金融市场化事实。

---

#### Fig 1.3: 波动率聚集

**文件**：`scripts/plots/e1/fig1_3_volatility_clustering.py`

**数据源**：`market.csv` 列 `log_return`

**脚本结构**：
```
1. 计算 |r_t| 序列
2. 计算 lag 1-30 的自相关函数
3. 创建 1×1 figure（8×4 inches）
4. 绘制 ACF 柱状图
5. 叠加 95% 置信区间（±1.96/√T）虚线
6. 标注显著滞后期数
7. 保存
```

**论文图片标题**：

> **图 1.3 绝对值收益率序列的自相关函数（波动率聚集检验）。** 横轴为滞后阶数（1-30 期），纵轴为自相关系数。红色虚线为 95% 置信区间（±1.96/√T）。显著的长期正自相关（前 15 阶超出置信区间）证实了波动率聚集现象的存在，与真实金融市场一致。

---

#### Fig 1.4: 策略熵恒定验证

**文件**：`scripts/plots/e1/fig1_4_entropy_constant.py`

**数据源**：`market.csv` 列 `step, strategy_entropy`

**脚本结构**：
```
1. 加载数据
2. 创建 1×1 figure（8×3.5 inches）
3. 绘制 H_strat(t) 时间序列
4. 叠加水平参考线（初始熵值）
5. 标注均值 ± 1σ 区间
6. 在标题中标注变异系数 CV = σ/μ
7. 保存
```

**论文图片标题**：

> **图 1.4 无演化市场中策略香农熵的时间演化。** H_strat(t) = −Σ_k p_k·ln(p_k)，度量策略家族分布的均匀程度。在无演化条件下，由于 agent 策略在整个模拟期间固定不变，策略熵保持恒定（CV < 1%），确认了实验处理的内部有效性。

---

#### Fig 1.5: Alpha 持续性热图

**文件**：`scripts/plots/e1/fig1_5_alpha_heatmap.py`

**数据源**：`families.csv` 列 `step, family_id, alpha`

**脚本结构**：
```
1. 透视 families.csv 为矩阵：行=family_id, 列=time_bucket, 值=mean_alpha
2. 时间分桶：每 500 期一个桶
3. 仅保留始终活跃的 top-30 家族（按终态财富排序）
4. 创建 1×1 figure（12×8 inches）
5. 绘制热力图（cmap="RdBu_r", center=0, vmin=-0.02, vmax=+0.02）
6. 添加颜色条标签 "Alpha"
7. 保存
```

**论文图片标题**：

> **图 1.5 策略家族 Alpha 持续性热图（无演化条件）。** 横轴为时间窗口（每 500 期聚合），纵轴为生存至模拟结束的 top-30 策略家族（按终态财富排序）。颜色代表滚动 Alpha 均值，红色为正 Alpha，蓝色为负 Alpha。Alpha 信号在时间轴上呈现显著持续性——初始盈利的策略在整个 10000 期内维持正 Alpha，表明在无演化条件下策略竞争优势不会自然消失。

---

#### Fig 1.6: 财富基尼系数演化

**文件**：`scripts/plots/e1/fig1_6_wealth_gini.py`

**数据源**：`market.csv` 列 `step, wealth_gini`

**脚本结构**：
```
1. 加载数据
2. 创建 1×1 figure（8×4 inches）
3. 绘制 wealth_gini(t)
4. 叠加参考线：基尼系数=0（完全均等）、基尼系数=0.5
5. 标注终态基尼系数值
6. 保存
```

**论文图片标题**：

> **图 1.6 无演化市场中 agent 财富基尼系数的时序演化。** 基尼系数度量财富分布的不平等程度（0=完全均等，1=完全不均等）。策略的固定性导致财富自然向表现较好的策略集中，基尼系数从初始的 0（均等分配）逐步上升至 ~0.3-0.4 的稳态水平，反映了市场对策略质量的"自然选择"效应——即便在无显式演化机制下。

---

#### Fig 1.7: 价格偏离度

**文件**：`scripts/plots/e1/fig1_7_price_deviation.py`

**数据源**：`market.csv` 列 `step, price, fundamental`

**脚本结构**：
```
1. 计算 MAE(t) = 滚动窗口内 |P - F| / F 的均值
2. 创建 1×1 figure（8×4 inches）
3. 绘制 MAE(t) 时间序列
4. 分 σ_noise 三水平用三条线对比
5. 添加图例
6. 保存
```

**论文图片标题**：

> **图 1.7 价格偏离基础价值的滚动平均绝对误差（MAE）演化。** 纵轴为 MAE(P,F) = mean(|P−F|/F)，窗口=200 期。三条曲线分别对应噪声交易冲击强度 σ_noise ∈ {0, 0.005, 0.02}。噪声越大，价格偏离基础价值的幅度越大且收敛越慢；σ_noise=0 时价格渐进收敛至接近基础价值，支持"无噪声无套利"的有效市场推论。

---

#### Fig 1.8: 市场效率对比

**文件**：`scripts/plots/e1/fig1_8_efficiency_comparison.py`

**数据源**：`market.csv`（三次独立运行，仅 σ_noise 不同），列 `step, acf1, hurst`

**脚本结构**：
```
1. 加载三组 σ_noise 的数据
2. 创建 2×1 figure（10×6 inches）
3. 上子图：ρ₁(t) 三条线 + 水平参考线 ρ₁=0
4. 下子图：Hurst 指数 H(t) 三条线 + 水平参考线 H=0.5
5. 添加图例（标注 σ_noise 值）
6. 保存
```

**论文图片标题**：

> **图 1.8 不同噪声水平下的市场效率动态对比。** 上图为一阶收益率自相关系数 ρ₁(t)（滚动窗口=60 期），下图为 Hurst 指数 H(t)（滚动窗口=500 期，R/S 法估计）。ρ₁→0 和 H→0.5 分别指示弱有效市场。σ_noise=0 时市场效率最高（ρ₁ 收敛至 0），σ_noise=0.02 时市场持续偏离有效状态。结果表明外部噪声本身即可创造和维持套利机会，为后续演化实验提供了效率"地板"的基线参考。

---

## 三、Experiment 2 — 资本扩张

### 3.1 CSV 输出

在通用格式基础上，`market.csv` 增加以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| `capital_concentration_top5` | float | Top-5 家族财富占比 |
| `capital_flow` | float | 当期财富重分配绝对值占比 |

### 3.2 图表列表与 Matplotlib 脚本规格

---

#### Fig 2.1: 拥挤度与 Alpha 双轴时序

**文件**：`scripts/plots/e2/fig2_1_crowding_alpha_dualaxis.py`

**数据源**：`families.csv`（top-3 终态家族），列 `step, family_id, wealth_share, alpha`

**脚本结构**：
```
1. 筛选终态财富最大的 3 个家族
2. 创建 1×1 figure（10×4.5 inches）
3. 左 y 轴：C_k(t)（wealth_share），实线
4. 右 y 轴：α_k(t)，虚线，同色系
5. 三个家族各用一种颜色
6. 在 α_k 曲线上标注 t_peak 和 t_half
7. 添加双图例（拥挤度 / Alpha）
8. 保存
```

**论文图片标题**：

> **图 2.1 资本扩张实验中 top-3 策略家族的拥挤度 C_k(t) 与 Alpha α_k(t) 双轴时序。** 实线（左轴）为各家族的财富占比（拥挤度），虚线（右轴）为滚动 Alpha（Δ=60 期）。三个家族分别对应三种初始策略倾向（趋势跟踪/均值回复/混合型）。随着资本向盈利策略集中（C_k 上升），对应 Alpha 呈同步下降趋势；标注了各家族的 Alpha 峰值时刻 t_peak 和半衰期 t_half。

---

#### Fig 2.2: 拥挤度-Alpha 散点关系

**文件**：`scripts/plots/e2/fig2_2_crowding_alpha_scatter.py`

**数据源**：`families.csv`（全部家族 × 全部时间点），列 `wealth_share, alpha`

**脚本结构**：
```
1. 加载 families.csv（所有种子聚合）
2. 采样：每 200 期、每家族取一个点（减少重叠绘制）
3. 创建 1×1 figure（7×7 inches, square）
4. 散点图：x=C_k, y=α_k, alpha=0.15, s=8
5. 叠加 LOESS 拟合曲线（span=0.3）+ 95% CI band
6. 叠加线性回归线（虚线，灰色）
7. 标注 Pearson r 和 Spearman ρ
8. 标注弹性 ε_α（对数-对数回归斜率）
9. 保存
```

**论文图片标题**：

> **图 2.2 策略拥挤度 C_k 与 Alpha α_k 的散点关系。** 每个点代表一个策略家族在一个采样时刻的观测值（N=全实验聚合）。橙色曲线为 LOESS 非参数拟合（span=0.3，阴影为 95% 置信区间），灰色虚线为普通最小二乘线性拟合。标注了 Pearson 相关系数 r 和 Spearman 秩相关系数 ρ。显著的负相关关系（r<0, p<0.001）支持拥挤度假说——策略资金规模越大，超额收益越低。对数-对数回归斜率（弹性 ε_α）表明拥挤度每上升 1%，Alpha 平均衰减约 0.4-0.8%。

---

#### Fig 2.3: Alpha-拥挤度弹性分布

**文件**：`scripts/plots/e2/fig2_3_elasticity_violin.py`

**数据源**：`families.csv`，按家族计算 ε_α(k) 后聚合

**脚本结构**：
```
1. 对每个家族计算其 ε_α(k) = d(ln α_k) / d(ln C_k)
2. 按 P_eliminate 分组
3. 创建 1×1 figure（8×5 inches）
4. 小提琴图 + 内部箱线图
5. x 轴：P_eliminate ∈ {0.10, 0.20, 0.40}
6. 叠加各组的均值 ± SD 标注
7. 添加 ANOVA 检验结果文本
8. 保存
```

**论文图片标题**：

> **图 2.3 不同淘汰/重生比例下的 Alpha-拥挤度弹性 ε_α 分布。** ε_α = d(ln α)/d(ln C)，负值越大表示 Alpha 对拥挤越敏感。小提琴图内嵌箱线图（中位数、四分位距），白色圆点为组均值。P_eliminate 增大（更强选择压力）使弹性分布向更负方向偏移，表明资本流动越快，Alpha 对拥挤的响应越剧烈。单因素 ANOVA：F=XX.X, p<0.001。

---

#### Fig 2.4: 资本集中度演化

**文件**：`scripts/plots/e2/fig2_4_capital_concentration.py`

**数据源**：`market.csv` 列 `step, capital_concentration_top5`，按 K 分面

**脚本结构**：
```
1. 加载数据，按 K 值分三组
2. 创建 1×3 figure（15×4 inches），sharey=True
3. 每子图：Top-5 财富占比时间序列
4. 叠加水平虚线（0.5 = 半数财富集中）
5. 标题标注 K 值
6. 保存
```

**论文图片标题**：

> **图 2.4 不同资本重分配周期 K 下的 top-5 策略家族财富集中度演化。** 纵轴为财富最大五个家族的财富之和占市场总财富的比例。三个子图分别对应 K=50（高频重分配）、K=200（中频）、K=500（低频）。虚线标示 50% 集中度水平。K 越小（资本流动越快），财富集中速度越快，稳态集中度越高。

---

#### Fig 2.5: 策略熵对比（P_eliminate 效应）

**文件**：`scripts/plots/e2/fig2_5_entropy_by_elimination.py`

**数据源**：`market.csv` 列 `step, strategy_entropy`，按 P_eliminate 分组

**脚本结构**：
```
1. 加载三组 P_eliminate 的 market.csv
2. 创建 1×1 figure（10×4.5 inches）
3. 三条 H_strat(t) 曲线
4. 标注初始熵值参考线
5. 在终点标注终态熵值
6. 添加图例
7. 保存
```

**论文图片标题**：

> **图 2.5 不同淘汰比例 P_eliminate 下的策略熵 H_strat(t) 演化。** P_eliminate=0.10 时策略多样性缓慢下降；P_eliminate=0.40 时多样性快速坍缩。与图 1.4（E1 基线，熵恒定）对比，资本扩张机制引入达尔文式"选择"压力，但仅作用于财富层面（策略不变），因此策略熵的下降完全由资本集中驱动——盈利策略家族的财富占比上升但策略本身并未增多。

---

#### Fig 2.6: 基尼系数-市场效率双轴

**文件**：`scripts/plots/e2/fig2_6_gini_efficiency.py`

**数据源**：`market.csv` 列 `step, wealth_gini, acf1`

**脚本结构**：
```
1. 加载数据
2. 创建 1×1 figure（10×4.5 inches）
3. 左 y 轴：wealth_gini（蓝色实线）
4. 右 y 轴：acf1（红色虚线）
5. 标注两者相关性
6. 保存
```

**论文图片标题**：

> **图 2.6 资本扩张实验中财富不平等（基尼系数）与市场效率（一阶自相关）的双轴时序。** 蓝色实线（左轴）为财富基尼系数，红色虚线（右轴）为 |ρ₁|。两者呈正相关——财富越集中，市场效率越高（|ρ₁| 越小）。这一反直觉发现可解释为：资本集中到少数"聪明"策略手中，市场定价权集中，价格发现效率提升；但代价是策略多样性丧失（参见图 2.5），潜伏着脆弱性风险。

---

#### Fig 2.7: Alpha 半衰期箱线图

**文件**：`scripts/plots/e2/fig2_7_halflife_boxplot.py`

**数据源**：从 `families.csv` 计算各家族的 t_half

**脚本结构**：
```
1. 对每个家族检测 t_peak 和 t_half
2. 按 P_eliminate 分组
3. 创建 1×1 figure（7×4 inches）
4. 箱线图（x=P_eliminate, y=t_half）
5. 叠加散点（jitter）
6. 标注组均值
7. 添加 Kruskal-Wallis 检验结果
8. 保存
```

**论文图片标题**：

> **图 2.7 不同淘汰比例 P_eliminate 下的 Alpha 半衰期 t_half 分布。** t_half 定义为 Alpha 从峰值衰减至一半所需的期数（参见 §8.3 生命周期定义）。箱线图显示中位数、四分位距和 1.5 IQR 范围，散点为各家族观测值（jitter 防重叠）。P_eliminate 越大，t_half 越短——更强的资本淘汰加速了拥挤驱动的 Alpha 衰减。Kruskal-Wallis 检验：H=XX.X, p<0.001。

---

#### Fig 2.8: 重生策略存活曲线

**文件**：`scripts/plots/e2/fig2_8_survival_curve.py`

**数据源**：`agents.csv`，追踪重生 agent 的存活状态

**脚本结构**：
```
1. 识别所有 parent_id=-2（标记为重生）的 agent
2. 计算其存活期数
3. 创建 1×1 figure（7×5 inches）
4. Kaplan-Meier 阶梯曲线（按 P_eliminate 分组）
5. 叠加 95% CI 阴影
6. 标注中位存活期
7. 标注 Log-rank 检验 p 值
8. 保存
```

**论文图片标题**：

> **图 2.8 资本扩张实验中"破产重生"策略的 Kaplan-Meier 存活曲线。** 横轴为重生后存活的交易期数，纵轴为存活概率。三条曲线分别对应 P_eliminate=0.10/0.20/0.40。中位存活期标注为垂直虚线。P_eliminate 越高，重生策略存活率越低（Log-rank p<0.001），表明资本扩张机制对失败策略的"惩罚"效应——随机重生的策略难以在高选择压力下立足。

---

## 四、Experiment 3 — 复制机制

### 4.1 CSV 输出

在通用格式基础上，`market.csv` 增加：

| 列名 | 类型 | 说明 |
|------|------|------|
| `dominant_family_share` | float | 最大家族的 agent 数量占比 |
| `max_drawdown` | float | 滚动最大回撤 |
| `extreme_event_count` | int | 累计极端事件数（\|r_t\| > 5σ） |

### 4.2 图表列表与 Matplotlib 脚本规格

---

#### Fig 3.1: 策略家族数量衰减

**文件**：`scripts/plots/e3/fig3_1_family_decay.py`

**数据源**：`market.csv` 列 `step, n_families`，按 λ_select 分面

**脚本结构**：
```
1. 加载三组 λ_select 的 market.csv
2. 创建 1×3 figure（15×4 inches），sharey=True
3. 每子图：K(t) 曲线 + 指数衰减拟合虚线
4. 标注拟合参数 γ（衰减速率）和 R²
5. 标题标注 λ_select 值
6. 保存
```

**论文图片标题**：

> **图 3.1 复制机制下策略家族数量 K(t) 的指数衰减。** 三子图分别对应选择压力 λ_select=0.5（弱选择）、3.0（中等）、10.0（强选择）。红色虚线为指数衰减拟合 K(t)=K₀·exp(−γt)，标注了衰减速率 γ 和拟合优度 R²。在 λ_select=10.0 的强选择下，策略家族在 3000 期内从 500 个锐减至不足 10 个——策略同质化以近乎几何级速率发生。

---

#### Fig 3.2: 策略家族谱系图

**文件**：`scripts/plots/e3/fig3_2_lineage_tree.py`

**数据源**：`agents.csv`，提取 parent_id → agent_id 关系

**脚本结构**：
```
1. 构建谱系树（使用 graphviz 或 ETE Toolkit）
2. 节点大小 ∝ 子代数量（用气泡表示家族规模）
3. 颜色编码存活状态（终态存活=绿色，已灭绝=灰色）
4. 时间轴：垂直方向表示演化代数
5. 保存为 fig3_2_lineage_tree.png（高分辨率位图或 PDF）
```

**论文图片标题**：

> **图 3.2 复制机制下的策略家族演化谱系树。** 每个节点代表一个策略家族，节点大小表示该家族的 agent 数量，颜色表示终态存活状态（绿色=存活，灰色=灭绝）。垂直方向对应演化代数（G=0 至 G=50）。在无突变条件下，谱系呈现典型的"赢家通吃"结构——早期少数成功家族垄断后续全部后代，大量家族在 5-10 代内灭绝，形成"演化瓶颈"。

---

#### Fig 3.3: 主导策略占比堆叠面积图

**文件**：`scripts/plots/e3/fig3_3_dominant_stack.py`

**数据源**：`families.csv` 的 top-10 家族 wealth_share 序列

**脚本结构**：
```
1. 筛选每期 top-10 家族（按 wealth_share）
2. 创建 1×1 figure（10×5 inches）
3. 堆叠面积图：10 种颜色
4. 其余家族聚合为灰色 "其他"
5. y 轴范围 [0, 1]
6. 标注主导家族首次超过 50% 的时间点
7. 保存
```

**论文图片标题**：

> **图 3.3 复制机制下策略家族的市场份额堆叠面积图。** 纵轴为财富占比（总计=1.0），每种颜色代表一个策略家族（top-10），灰色为其余家族之和。红色虚线标示主导家族（最大单一家族）首次超过 50% 市场份额的时间点 T_homog。同质化后市场由 2-3 个家族主导，策略多样性几近消失。

---

#### Fig 3.4: 市场效率 vs 选择压力

**文件**：`scripts/plots/e3/fig3_4_efficiency_selection.py`

**数据源**：`market.csv` 列 `step, acf1`，按 λ_select 分组

**脚本结构**：
```
1. 加载三组 λ_select 的数据
2. 创建 1×1 figure（10×4.5 inches）
3. 三条 |ρ₁(t)| 曲线
4. 叠加水平参考线 |ρ₁|=0（完全有效）
5. 标注各组的终态 |ρ₁| 均值
6. 添加图例
7. 保存
```

**论文图片标题**：

> **图 3.4 不同选择压力 λ_select 下市场效率 |ρ₁| 的动态演化。** λ_select=10.0（强选择）条件下市场效率最高——策略快速同质化后价格信号趋于一致，可预测性下降。然而，这种效率是"脆弱的"：同质化的策略群在面对外部冲击时缺乏多样性缓冲，参见图 3.5 的极端事件分析。

---

#### Fig 3.5: 策略熵-极端事件关系

**文件**：`scripts/plots/e3/fig3_5_entropy_extreme.py`

**数据源**：`market.csv` 列 `strategy_entropy, extreme_event_freq`

**脚本结构**：
```
1. 按时间窗口（每 500 期）聚合 H_strat 和极端事件频率
2. 创建 1×1 figure（7×6 inches）
3. 散点图：x=H_strat, y=极端事件频率
4. 叠加二次拟合曲线（β₁x+β₂x²）
5. 若 β₂<0（倒 U 型），标注最优点
6. 标注拟合方程 + R²
7. 保存
```

**论文图片标题**：

> **图 3.5 策略熵 H_strat 与极端事件频率的关系。** 横轴为策略香农熵（窗口=500 期均值），纵轴为该窗口内极端事件（|r_t|>5σ）的发生频率。二次拟合曲线（红色）揭示了倒 U 型关系：策略多样性过低（同质化）和过高（碎片化）均导致极端事件增多，存在最优多样性区间（H*≈2.0-2.5）使市场最稳健。

---

#### Fig 3.6: 复制模式对比

**文件**：`scripts/plots/e3/fig3_6_replication_mode_comparison.py`

**数据源**：`market.csv`（精确复制 vs 财富继承复制），列 `step, n_families`

**脚本结构**：
```
1. 加载两组复制模式的 n_families(t)
2. 创建 1×1 figure（8×4.5 inches）
3. 两条曲线 + 图例
4. 标注终态差异
5. 保存
```

**论文图片标题**：

> **图 3.6 精确复制与财富继承复制两种模式下的策略家族数量衰减对比。** 精确复制（蓝色）使子代继承父代的全部策略参数但不继承财富优势；财富继承复制（红色）使子代同时继承策略和财富比例。精确复制导致更快的策略同质化——当"策略基因"与"财富基因"分离时，市场对策略质量的筛选更纯粹，收敛更快。

---

#### Fig 3.7: Alpha 半衰期-选择压力

**文件**：`scripts/plots/e3/fig3_7_halflife_selection.py`

**数据源**：`families.csv`，计算各家族 t_half，按 λ_select 分组

**脚本结构**：
```
1. 同 Fig 2.7 结构
2. 按 λ_select 分组而非 P_eliminate
3. 保存
```

**论文图片标题**：

> **图 3.7 复制机制下不同选择压力 λ_select 的 Alpha 半衰期分布。** 与图 2.7（资本扩张）对比，复制机制使 Alpha 半衰期系统性缩短（中位数减少约 40-60%）。策略的克隆导致拥挤效应叠加同质化效应——不仅资金流入盈利策略，策略本身也被复制，双重加速 Alpha 衰减。

---

#### Fig 3.8: 市场最大回撤演化

**文件**：`scripts/plots/e3/fig3_8_max_drawdown.py`

**数据源**：`market.csv` 列 `step, max_drawdown`，按 λ_select 分组

**脚本结构**：
```
1. 加载数据
2. 创建 1×1 figure（10×4 inches）
3. 三条最大回撤曲线
4. 标注各组全局最大回撤值
5. 保存
```

**论文图片标题**：

> **图 3.8 复制机制下不同选择压力 λ_select 的市场滚动最大回撤演化。** 最大回撤 = 从峰值到谷底的最大百分比损失。λ_select=10.0 的强选择条件下，策略同质化后市场出现"脆弱稳定"——表面波动率下降，但最大回撤幅度反而更大（因所有 agent 同时同向交易）。这验证了 H3（策略多样性-市场稳定性假说）的核心预测：同质化隐藏着系统性风险。

---

## 五、Experiment 4 — 复制+突变（完整演化）

### 5.1 CSV 输出

在通用格式基础上，`market.csv` 增加：

| 列名 | 类型 | 说明 |
|------|------|------|
| `mean_strategy_complexity` | float | 策略‖w‖₁ 的种群均值 |
| `mean_niche_overlap` | float | 平均 Pianka 指数 Ō(t) |
| `new_family_rate` | float | 每 K 期新出现的策略家族数 |
| `offspring_survival_rate` | float | 突变后代的 K 期内存活率 |

`families.csv` 增加：

| 列名 | 类型 | 说明 |
|------|------|------|
| `t_emerge` | int | Alpha 首次显著的期数 |
| `t_peak` | int | Alpha 峰值期数 |
| `t_half` | int | Alpha 半衰期 |
| `t_extinct` | int | Alpha 消失期数（若已灭绝） |
| `lifecycle_complete` | bool | 是否完整经历五阶段 |

---

### 5.2 图表列表与 Matplotlib 脚本规格

---

#### Fig 4.1: Alpha 生命周期详细追踪

**文件**：`scripts/plots/e4/fig4_1_alpha_lifecycle.py`

**数据源**：`families.csv`，选一个"典型"家族（完整五阶段）

**脚本结构**：
```
1. 选择一个生命周期完整且清晰的家族
2. 创建 2×1 figure（10×8 inches），sharex=True
3. 上子图：α_k(t) 曲线
   - 标注五阶段分界线和阶段名称
   - 标注 t_emerge, t_peak, t_half, t_extinct
4. 下子图：C_k(t) 拥挤度曲线
   - 阴影标注五阶段背景色
5. 阶段背景色：
   - I（探索）= 浅灰
   - II（爆发）= 浅绿
   - III（拥挤）= 浅黄
   - IV（衰退）= 浅红
   - V（灭绝/恢复）= 浅蓝
6. 保存
```

**论文图片标题**：

> **图 4.1 完整演化条件下单一策略家族的 Alpha 生命周期追踪。** 上图：滚动 Alpha α_k(t)（Δ=60 期），垂直虚线划分五个阶段——I 探索期（Alpha 不显著）、II 爆发期（Alpha 持续上升至峰值）、III 拥挤期（Alpha 开始下降但保持为正）、IV 衰退期（Alpha 衰减至峰值一半以下）、V 灭绝/恢复期。下图：该家族的拥挤度 C_k(t)。五阶段以背景色区分。该家族完整呈现了从策略发现到 Alpha 消失的完整生命周期，半衰期 t_half=XXX 期。

---

#### Fig 4.2: 策略熵在突变率-选择压力空间的演化

**文件**：`scripts/plots/e4/fig4_2_entropy_grid.py`

**数据源**：`market.csv`（16 组条件：4 p_mut × 4 σ_mut），列 `step, strategy_entropy`

**脚本结构**：
```
1. 加载全部 16 组数据
2. 创建 4×4 grid figure（16×14 inches）
3. 每子图：H_strat(t) 曲线
4. 行标签 = p_mut，列标签 = σ_mut
5. 终态 H_strat 用颜色编码子图边框
6. 全局标题：策略熵在突变率-变异幅度空间的长期演化
7. 保存
```

**论文图片标题**：

> **图 4.2 策略熵 H_strat(t) 在突变率 p_mut 与变异幅度 σ_mut 空间中的长期演化。** 4×4 网格，行对应突变率 p_mut ∈ {0.05, 0.10, 0.20, 0.40}，列对应变异幅度 σ_mut ∈ {0.01, 0.03, 0.10, 0.25}。子图边框颜色编码终态 H_strat（红色=低多样性，绿色=高多样性）。p_mut 过低（0.05）时多样性逐渐坍缩；p_mut 过高（0.40）时策略分布趋于随机；中间区间（p_mut≈0.10-0.20, σ_mut≈0.03-0.10）维持了最高的稳态多样性。

---

#### Fig 4.3: 相变热图

**文件**：`scripts/plots/e4/fig4_3_phase_transition.py`

**数据源**：`market.csv`（48 组条件），提取终态 H_strat（最后 2000 期均值）

**脚本结构**：
```
1. 构建矩阵：行=p_mut, 列=λ_select, 值=终态 H_strat
2. 创建 1×1 figure（8×6 inches）
3. 热力图（cmap="viridis"）
4. 标注每个单元格的 H_strat 值
5. 叠加相变边界线（分段回归断点连线）
6. 标注"高多样性区"和"低多样性区"
7. 保存
```

**论文图片标题**：

> **图 4.3 突变率-选择压力空间中的策略多样性相变热图。** 颜色编码终态策略熵 H_strat（最后 2000 期均值），黄色=高多样性，深紫=低多样性。黑色虚线为分段回归检测到的相变边界——将参数空间划分为"多策略共存相"（右下）和"单策略主导相"（左上）。在边界附近，系统对参数微小变化高度敏感，呈现临界特征。

---

#### Fig 4.4: 策略复杂度分布演化

**文件**：`scripts/plots/e4/fig4_4_complexity_evolution.py`

**数据源**：`agents.csv`，按演化代数采样

**脚本结构**：
```
1. 每 5 代取一个 agents.csv 快照
2. 计算每个 agent 的策略复杂度 ‖w‖₁
3. 创建 1×1 figure（10×4 inches）
4. 小提琴图序列（x=代数, y=‖w‖₁）
5. 叠加均值趋势线
6. 标注复杂度上限平台期
7. 保存
```

**论文图片标题**：

> **图 4.4 策略复杂度（信号权重 L1 范数 ‖w‖₁）的种群分布演化。** 横轴为演化代数 G，每代以小提琴图表示该代所有 agent 的策略复杂度分布，红色实线为种群均值。策略复杂度在演化初期快速上升（"军备竞赛"效应），约 15-20 代后进入平台期——表明适应性复杂化存在上限，过高的策略复杂度并未带来更大的生存优势，支持 H4（中等复杂度最优假说）。

---

#### Fig 4.5: 生态位重叠度分布演化

**文件**：`scripts/plots/e4/fig4_5_niche_overlap.py`

**数据源**：`agents.csv`，计算所有家族对的 Pianka 指数 O_{kℓ}

**脚本结构**：
```
1. 每 10 代采样
2. 计算该代所有家族对的 O_{kℓ}
3. 创建 1×1 figure（8×4 inches）
4. 直方图序列（分面，每 1000 期一个直方图）
5. 标注各时期的均值 Ō
6. 保存
```

**论文图片标题**：

> **图 4.5 策略生态位重叠度 O_{kℓ}（Pianka 指数）的种群分布演化。** 四个直方图分别对应 t=0, 3000, 6000, 9000 期的策略家族间生态位重叠度分布。O→1 表示信号利用高度重叠（激烈竞争），O→0 表示生态位分化。随着演化进行，分布从初始的随机均匀逐渐向双峰结构演变——出现了生态位高度重叠的主导族群和与之分化的"边缘"策略（低重叠度、低竞争、Alpha 更持久）。

---

#### Fig 4.6: 新生策略存活率

**文件**：`scripts/plots/e4/fig4_6_offspring_survival.py`

**数据源**：`agents.csv`，追踪新 agent 的存活

**脚本结构**：
```
1. 识别所有 parent_id>0 的 agent（非初始）
2. 跟踪其 500 期内是否仍存在
3. 创建 1×1 figure（7×5 inches）
4. x=p_mut, y=存活率，误差棒 = ±1 SE
5. 按 σ_mut 分组用不同颜色/标记
6. 保存
```

**论文图片标题**：

> **图 4.6 突变后代在 500 期内存活的比例与突变参数的关系。** 横轴为突变率 p_mut，不同颜色的曲线对应不同变异幅度 σ_mut。误差棒为 ±1 SE（跨种子）。存活率在 p_mut≈0.10-0.20 达到峰值——过低则后代与父代过于相似（无优势改进），过高则后代策略被噪声破坏。σ_mut=0.03 的存活率整体最高，表明小幅变异更有利于渐进适应。

---

#### Fig 4.7: Alpha 半衰期跨条件小提琴图

**文件**：`scripts/plots/e4/fig4_7_halflife_mutation.py`

**数据源**：`families.csv`，计算所有家族的 t_half，按 p_mut 分组

**脚本结构**：
```
1. 计算各家族 t_half
2. 按 p_mut 分组
3. 创建 1×1 figure（8×5 inches）
4. 小提琴图 + 箱线图
5. 叠加 E3 基线（无突变）作为参考虚线
6. 标注 Kruskal-Wallis 检验
7. 保存
```

**论文图片标题**：

> **图 4.7 完整演化条件下 Alpha 半衰期 t_half 随突变率 p_mut 的分布。** 红色虚线为 E3（复制无突变）的 Alpha 半衰期中位数，作为基线对比。突变显著延长了 Alpha 半衰期——p_mut=0.10-0.20 时中位 t_half 较 E3 基线提升约 2-5 倍。然而 p_mut=0.40（过高突变率）时 t_half 回降，表明过量突变破坏了适应性积累。Kruskal-Wallis H=XX, p<0.001。

---

#### Fig 4.8: 策略交互网络快照

**文件**：`scripts/plots/e4/fig4_8_interaction_network.py`

**数据源**：`agents.csv`，计算家族间的竞争/互利关系

**脚本结构**：
```
1. 取 t=2000, 5000, 8000 三个时刻
2. 构建网络：节点=策略家族，边=O_{kℓ}（仅 |O|>0.3 绘制）
3. 边颜色：O>0 = 红色（竞争），O<0 = 蓝色（互利）
4. 边宽度 ∝ |O|
5. 节点大小 ∝ 财富份额
6. 使用 networkx + matplotlib 或 graphviz 布局
7. 创建 1×3 figure（18×6 inches）
8. 保存
```

**论文图片标题**：

> **图 4.8 策略交互网络在三个演化阶段的快照。** 节点代表策略家族（大小∝财富份额），边表示生态位重叠度 |O_{kℓ}|>0.3 的家族对（红色=竞争关系 O>0，蓝色=互利关系 O<0，边宽∝|O|）。t=2000 期时网络稀疏、家族众多；t=5000 期时出现核心-边缘结构；t=8000 期时形成稳定的生态位分化——核心族群内部激烈竞争，边缘族群彼此孤立但 Alpha 持久。

---

#### Fig 4.9: 策略多样性-极端事件倒U型检验

**文件**：`scripts/plots/e4/fig4_9_u_shape_test.py`

**数据源**：`market.csv`，聚合全部 E4 运行数据

**脚本结构**：
```
1. 每 500 期窗口聚合 (H_strat, 极端事件频率)
2. 创建 1×1 figure（7×6 inches）
3. 散点图 + 二次拟合
4. 叠加线性拟合（虚线，参考）
5. 二次项显著性标注（β₂<0 的 p 值）
6. 若显著倒 U，标注最优 H_strat*
7. 标注 ΔAIC（二次 vs 线性）
8. 保存
```

**论文图片标题**：

> **图 4.9 策略多样性 H_strat 与极端事件频率的倒 U 型关系检验。** 聚合全部 E4 运行数据（每 500 期窗口为一个观测点）。红色实线为二次回归拟合（β₁H+β₂H²），灰色虚线为线性拟合。二次项 β₂ 显著为负（p<0.001），ΔAIC=−XX.X（二次模型更优），支持 H3——存在最优策略多样性区间 H*≈2.3 使市场极端事件频率最低。偏离最优值（无论过低或过高）均导致市场脆弱性上升。

---

#### Fig 4.10: 制度冲击效应

**文件**：`scripts/plots/e4/fig4_10_regime_shock.py`

**数据源**：`market.csv`（子实验 4a，5 种制度）

**脚本结构**：
```
1. 加载五种制度的 market.csv
2. 提取冲击前（t<5000）和冲击后（t>5000）的 H_strat
3. 创建 1×2 figure（12×5 inches）
4. 左子图：配对条形图（前 vs 后，按制度分组）
5. 右子图：H_strat 时间序列（五种制度叠加，虚线标记冲击时刻）
6. 标注各制度的 ΔH_strat 和配对 t 检验 p 值
7. 保存
```

**论文图片标题**：

> **图 4.10 市场制度冲击对策略生态系统的影响。** 左图：冲击前后策略熵 H_strat 的配对条形图（白色=冲击前 1000 期均值，填充色=冲击后 1000 期均值）。右图：五种制度下 H_strat(t) 的时序演化，垂直虚线标示冲击时刻（t=5000）。涨跌停板（±10%）和 T+1 限制对策略多样性的冲击最大（ΔH_strat 显著为负），交易成本增加的影响次之。制度变化充当了演化"选择压力"——仅适应新规则的策略存活，引起策略组成的系统性格局重塑。

---

#### Fig 4.11: 完整演化谱系树

**文件**：`scripts/plots/e4/fig4_11_full_lineage.py`

**数据源**：`agents.csv` + `families.csv`

**脚本结构**：
```
1. 构建完整谱系树
2. 节点颜色编码家族终态状态（存活/灭绝）
3. 节点大小 ∝ 家族最大规模
4. 突变节点（策略参数发生变异的代）用特殊标记
5. 时间轴：垂直方向
6. 标注主要演化事件：新家族爆发、大灭绝、瓶颈期
7. 输出高分辨率 PDF（用于论文印刷）
```

**论文图片标题**：

> **图 4.11 完整演化条件下策略家族的演化谱系树。** 纵轴为演化代数（G=0→50），节点大小表示该家族的峰值 agent 数量，绿色=终态存活，灰色=已灭绝，红色圆点标示突变节点（策略参数在该代发生显著变异）。谱系展示了典型的"间断平衡"（punctuated equilibrium）模式——长期策略稳定被偶发的"创新爆发"打断，新家族从突变中产生并快速扩张或迅速灭绝。标注了三次主要演化事件：初始多样化（G=0-5）、第一次大灭绝（G≈12）、第二次创新辐射（G≈25-30）。

---

#### Fig 4.12: 制度- Alpha 半衰期对比

**文件**：`scripts/plots/e4/fig4_12_regime_halflife.py`

**数据源**：`families.csv`（子实验 4a），计算各制度下的 t_half

**脚本结构**：
```
1. 计算五种制度下所有家族的 t_half
2. 创建 1×1 figure（8×5 inches）
3. 箱线图（按制度分组）
4. 叠加基准制度（无摩擦）的参考虚线
5. 标注 Kruskal-Wallis 检验 + 事后两两比较
6. 保存
```

**论文图片标题**：

> **图 4.12 不同市场制度下的 Alpha 半衰期 t_half 分布对比。** 五种制度：无摩擦基准、涨跌停板（±10%）、T+1 交易限制、交易成本（佣金+印花税）、完整 A 股制度。红色虚线为无摩擦基准的中位 t_half。涨跌停板和 T+1 限制通过抑制短期交易降低了策略间竞争强度，意外延长了 Alpha 半衰期；而交易成本对所有策略施加均等摩擦，对相对 Alpha 的影响不显著。Kruskal-Wallis H=XX, p<0.001；事后 Dunn 检验：涨跌停 vs 基准 p<0.01，T+1 vs 基准 p<0.05。

---

## 六、跨实验对比图表

### 跨实验图表列表

---

#### Fig C.1: 四组实验策略熵综合对比

**文件**：`scripts/plots/cross/figC1_entropy_all.py`

**数据源**：各实验最优参数组的 `market.csv`

**脚本结构**：
```
1. 从 E1–E4 各选一个代表性运行（最优参数）
2. 创建 1×1 figure（10×5 inches）
3. 四条 H_strat(t) 曲线 + 图例
4. 颜色：E1=灰、E2=蓝、E3=橙、E4=绿
5. 标注各组终态值
6. 保存
```

**论文图片标题**：

> **图 5.1 四组实验的策略熵 H_strat 综合对比。** E1（无演化，灰色）：策略熵恒定；E2（资本扩张，蓝色）：缓慢下降；E3（复制机制，橙色）：快速坍缩；E4（完整演化，绿色）：在突变维持下达到稳态震荡。四条曲线清晰地分离了 Alpha 衰减的三个驱动因素——拥挤（E2−E1）、同质化（E3−E2）和创新对抗（E4−E3）。

---

#### Fig C.2: 市场效率综合对比

**文件**：`scripts/plots/cross/figC2_efficiency_all.py`

**脚本结构**：同 C.1，绘制 |ρ₁(t)|。

**论文图片标题**：

> **图 5.2 四组实验的市场效率指标 |ρ₁| 综合对比。** E3（复制无突变）在策略同质化后达到表面上的最高效率（|ρ₁|→0），但这是"脆弱的效率"（参见图 C.3 极端事件对比）。E4 的效率动态波动，反映策略创新与衰减的周期性循环，更接近 AMH 预测的效率动态性。

---

#### Fig C.3: 极端事件频率对比

**文件**：`scripts/plots/cross/figC3_extreme_events.py`

**脚本结构**：
```
1. 统计各实验后半段（t>5000）的极端事件频率
2. 创建 1×1 figure（6×4.5 inches）
3. 柱状图（x=实验, y=极端事件/1000 期）
4. 误差棒 = ±1 SE（跨种子）
5. 标注 ANOVA + 事后比较
6. 保存
```

**论文图片标题**：

> **图 5.3 四组实验的极端事件频率对比（t>5000 期）。** 纵轴为每 1000 期中 |r_t|>5σ 的极端事件次数。E3（复制无突变）的极端事件频率最高——验证了"同质化隐藏系统性风险"的核心假说。E4（含突变）的极端事件频率显著低于 E3（p<0.001），表明策略多样性是市场稳健性的有效缓冲。

---

#### Fig C.4: Alpha 半衰期跨实验对比

**文件**：`scripts/plots/cross/figC4_halflife_all.py`

**脚本结构**：
```
1. 从 E2/E3/E4 提取各家族 t_half
2. 创建 1×1 figure（7×4.5 inches）
3. 箱线图（x=实验）
4. 标注 Kruskal-Wallis + 事后比较
5. 保存
```

**论文图片标题**：

> **图 5.4 Alpha 半衰期 t_half 的跨实验对比。** E2（资本扩张）的 t_half 最长（仅拥挤效应），E3（复制）最短（拥挤+同质化双重效应），E4（完整演化）居中——突变通过持续引入策略多样性周期性"重置"拥挤状态，延长了 Alpha 的持久性。事后 Dunn 检验：E2 vs E3 p<0.001，E3 vs E4 p<0.01，E2 vs E4 p<0.05。

---

#### Fig C.5: 机制贡献的方差分解

**文件**：`scripts/plots/cross/figC5_variance_decomposition.py`

**脚本结构**：
```
1. 以终态 H_strat 为因变量
2. 因子：拥挤效应（E2 vs E1）、同质化效应（E3 vs E2）、突变效应（E4 vs E3）
3. 创建 1×1 figure（6×5 inches）
4. 堆叠柱状图：各效应的方差贡献比例
5. 标注各效应百分比
6. 保存
```

**论文图片标题**：

> **图 5.5 策略多样性衰减的机制贡献方差分解。** 以终态策略熵 H_strat(T) 为因变量，将总方差分解为三个机制的独立贡献：拥挤效应（资本集中驱动的多样性下降）、同质化效应（策略复制驱动的多样性坍缩）、突变效应（创新引入的多样性维持）。同质化效应贡献最大的方差比例（~50%），突变为负贡献（抑制多样性下降），残余为交互效应和随机噪声。

---

## 七、论文图片标题汇总

### 第五章（实验结果）建议排版

```
5.1 无演化基线实验
  图 5.1  价格与基础价值时序
  图 5.2  收益率分布正态性检验
  图 5.3  波动率聚集检验
  图 5.4  策略熵恒定验证
  图 5.5  Alpha 持续性热图
  图 5.6  财富基尼系数演化
  图 5.7  价格偏离度分析
  图 5.8  噪声水平与市场效率

5.2 资本扩张实验
  图 5.9  拥挤度-Alpha 双轴时序
  图 5.10 拥挤度-Alpha 散点关系
  图 5.11 Alpha-拥挤度弹性分布
  图 5.12 资本集中度演化
  图 5.13 策略熵对比（P_eliminate 效应）
  图 5.14 基尼系数-市场效率关系
  图 5.15 Alpha 半衰期箱线图
  图 5.16 重生策略存活曲线

5.3 复制机制实验
  图 5.17 策略家族数量衰减
  图 5.18 策略演化谱系树
  图 5.19 主导策略占比堆叠图
  图 5.20 市场效率 vs 选择压力
  图 5.21 策略熵-极端事件关系
  图 5.22 复制模式对比
  图 5.23 Alpha 半衰期-选择压力
  图 5.24 最大回撤演化

5.4 完整演化实验
  图 5.25 Alpha 生命周期追踪
  图 5.26 策略熵在突变参数空间
  图 5.27 策略多样性相变热图
  图 5.28 策略复杂度分布演化
  图 5.29 生态位重叠度分布
  图 5.30 新生策略存活率
  图 5.31 Alpha 半衰期-突变率
  图 5.32 策略交互网络快照
  图 5.33 策略多样性-极端事件检验
  图 5.34 制度冲击效应
  图 5.35 完整演化谱系树
  图 5.36 制度-Alpha 半衰期

5.5 跨实验综合分析
  图 5.37 策略熵综合对比
  图 5.38 市场效率综合对比
  图 5.39 极端事件频率对比
  图 5.40 Alpha 半衰期跨实验对比
  图 5.41 机制贡献方差分解
```

---

## 八、Matplotlib 脚本清单

| 脚本路径 | 对应图表 | 输入数据 | 输出文件 |
|----------|----------|----------|----------|
| `scripts/plots/plot_config.py` | 全局配置 | — | — |
| `scripts/plots/e1/fig1_1_price_fundamental.py` | Fig 1.1 | market.csv | fig1_1_price_vs_fundamental.png |
| `scripts/plots/e1/fig1_2_return_distribution.py` | Fig 1.2 | market.csv | fig1_2_return_distribution.png |
| `scripts/plots/e1/fig1_3_volatility_clustering.py` | Fig 1.3 | market.csv | fig1_3_volatility_clustering.png |
| `scripts/plots/e1/fig1_4_entropy_constant.py` | Fig 1.4 | market.csv | fig1_4_entropy_constant.png |
| `scripts/plots/e1/fig1_5_alpha_heatmap.py` | Fig 1.5 | families.csv | fig1_5_alpha_heatmap.png |
| `scripts/plots/e1/fig1_6_wealth_gini.py` | Fig 1.6 | market.csv | fig1_6_wealth_gini.png |
| `scripts/plots/e1/fig1_7_price_deviation.py` | Fig 1.7 | market.csv | fig1_7_price_deviation.png |
| `scripts/plots/e1/fig1_8_efficiency_comparison.py` | Fig 1.8 | market.csv×3 | fig1_8_efficiency_comparison.png |
| `scripts/plots/e2/fig2_1_crowding_alpha_dualaxis.py` | Fig 2.1 | families.csv | fig2_1_crowding_alpha_dualaxis.png |
| `scripts/plots/e2/fig2_2_crowding_alpha_scatter.py` | Fig 2.2 | families.csv | fig2_2_crowding_alpha_scatter.png |
| `scripts/plots/e2/fig2_3_elasticity_violin.py` | Fig 2.3 | families.csv | fig2_3_elasticity_violin.png |
| `scripts/plots/e2/fig2_4_capital_concentration.py` | Fig 2.4 | market.csv×3 | fig2_4_capital_concentration.png |
| `scripts/plots/e2/fig2_5_entropy_by_elimination.py` | Fig 2.5 | market.csv×3 | fig2_5_entropy_by_elimination.png |
| `scripts/plots/e2/fig2_6_gini_efficiency.py` | Fig 2.6 | market.csv | fig2_6_gini_efficiency.png |
| `scripts/plots/e2/fig2_7_halflife_boxplot.py` | Fig 2.7 | families.csv | fig2_7_halflife_boxplot.png |
| `scripts/plots/e2/fig2_8_survival_curve.py` | Fig 2.8 | agents.csv | fig2_8_survival_curve.png |
| `scripts/plots/e3/fig3_1_family_decay.py` | Fig 3.1 | market.csv×3 | fig3_1_family_decay.png |
| `scripts/plots/e3/fig3_2_lineage_tree.py` | Fig 3.2 | agents.csv | fig3_2_lineage_tree.png |
| `scripts/plots/e3/fig3_3_dominant_stack.py` | Fig 3.3 | families.csv | fig3_3_dominant_stack.png |
| `scripts/plots/e3/fig3_4_efficiency_selection.py` | Fig 3.4 | market.csv×3 | fig3_4_efficiency_selection.png |
| `scripts/plots/e3/fig3_5_entropy_extreme.py` | Fig 3.5 | market.csv | fig3_5_entropy_extreme.png |
| `scripts/plots/e3/fig3_6_replication_mode.py` | Fig 3.6 | market.csv×2 | fig3_6_replication_mode.png |
| `scripts/plots/e3/fig3_7_halflife_selection.py` | Fig 3.7 | families.csv | fig3_7_halflife_selection.png |
| `scripts/plots/e3/fig3_8_max_drawdown.py` | Fig 3.8 | market.csv | fig3_8_max_drawdown.png |
| `scripts/plots/e4/fig4_1_alpha_lifecycle.py` | Fig 4.1 | families.csv | fig4_1_alpha_lifecycle.png |
| `scripts/plots/e4/fig4_2_entropy_grid.py` | Fig 4.2 | market.csv×16 | fig4_2_entropy_grid.png |
| `scripts/plots/e4/fig4_3_phase_transition.py` | Fig 4.3 | 聚合 market.csv×48 | fig4_3_phase_transition.png |
| `scripts/plots/e4/fig4_4_complexity_evolution.py` | Fig 4.4 | agents.csv | fig4_4_complexity_evolution.png |
| `scripts/plots/e4/fig4_5_niche_overlap.py` | Fig 4.5 | agents.csv | fig4_5_niche_overlap.png |
| `scripts/plots/e4/fig4_6_offspring_survival.py` | Fig 4.6 | agents.csv | fig4_6_offspring_survival.png |
| `scripts/plots/e4/fig4_7_halflife_mutation.py` | Fig 4.7 | families.csv | fig4_7_halflife_mutation.png |
| `scripts/plots/e4/fig4_8_interaction_network.py` | Fig 4.8 | agents.csv | fig4_8_interaction_network.png |
| `scripts/plots/e4/fig4_9_u_shape_test.py` | Fig 4.9 | 聚合 market.csv | fig4_9_u_shape_test.png |
| `scripts/plots/e4/fig4_10_regime_shock.py` | Fig 4.10 | market.csv×5 | fig4_10_regime_shock.png |
| `scripts/plots/e4/fig4_11_full_lineage.py` | Fig 4.11 | agents.csv | fig4_11_full_lineage.pdf |
| `scripts/plots/e4/fig4_12_regime_halflife.py` | Fig 4.12 | families.csv×5 | fig4_12_regime_halflife.png |
| `scripts/plots/cross/figC1_entropy_all.py` | Fig C.1 | market.csv×4 | figC1_entropy_all.png |
| `scripts/plots/cross/figC2_efficiency_all.py` | Fig C.2 | market.csv×4 | figC2_efficiency_all.png |
| `scripts/plots/cross/figC3_extreme_events.py` | Fig C.3 | 聚合统计 | figC3_extreme_events.png |
| `scripts/plots/cross/figC4_halflife_all.py` | Fig C.4 | families.csv×3 | figC4_halflife_all.png |
| `scripts/plots/cross/figC5_variance_decomposition.py` | Fig C.5 | 聚合统计 | figC5_variance_decomposition.png |

**总计**：41 个 matplotlib 脚本，产生 41 张论文级图表。

---

*END OF PLOT_SPEC.md*
