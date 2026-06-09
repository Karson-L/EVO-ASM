# EVO-ASM 模型数学规格说明书 (MODEL_SPEC.md)

> 基于 REASEARCH_PLAN.md §5 §6 的 EVO-ASM (Evolutionary Artificial Stock Market) 框架
> 版本：v1.0 | 日期：2026-06-09
> 语言：纯数学符号描述，不含代码

---

## 符号约定

| 符号惯例 | 含义 |
|----------|------|
| 下标 `i, j` | Agent索引，i,j ∈ {1, 2, …, M} |
| 下标 `t` | 离散时间步（交易日），t ∈ {0, 1, …, T} |
| 下标 `k` | 策略类型/家族索引 |
| 粗体 `x` | 向量 |
| 上标 `(n)` | 资产索引，n ∈ {1, 2, …, N} |
| `E[·]` | 期望算子 |
| `I{·}` | 示性函数 |

---

## 1. Agent 类型定义

### 1.1 Agent 的统一表示

系统中所有 agent 共享同一形式化结构。Agent 的类型不预设，而是由其策略编码 `π_i(t)` 在信号空间中的位置**涌现**决定。

Agent i 在时刻 t 的完整状态由一个六元组定义：

$$\boxed{\mathcal{A}_i(t) = \bigl(\; \pi_i(t),\; W_i(t),\; h_i^{(n)}(t),\; S_i(t),\; \mathcal{H}_i(t),\; \mathcal{R}_i(t) \;\bigr)}$$

其中：
- `π_i(t)`：策略编码（定义见 §1.2）
- `W_i(t)`：总财富（现金 + 持仓市值）
- `h_i^{(n)}(t)`：资产 n 的持仓数量
- `S_i(t)`：已实现累计收益（用于适应度评估）
- `ℋ_i(t)`：历史记忆（用于学习）
- `ℛ_i(t)`：所属策略家族标签（聚类产生，非预设）

### 1.2 策略编码 π_i(t)

每个 agent 的策略由信号权重向量、阈值、持仓周期、风险偏好组成：

$$\boxed{\pi_i(t) = \bigl(\; \mathbf{w}_i(t),\; \theta_i(t),\; \tau_i(t),\; \alpha_i(t) \;\bigr)}$$

**分量详解**：

**(a) 信号权重向量 `w_i(t)`**

$$ \mathbf{w}_i(t) \in \mathbb{R}^D,\quad D = |\mathcal{S}| $$

其中 `S = {S1, S2, …, SD}` 为信号空间（见 §2.3），D 维信号。

**(b) 进入阈值 `θ_i(t)`**

$$ \theta_i(t) \in [\theta_{\min},\; \theta_{\max}] \subset \mathbb{R}^+ $$

信号强度必须超过此阈值才触发交易。

**(c) 典型持仓周期 `τ_i(t)`**

$$ \tau_i(t) \in \{1, 3, 5, 10, 20, 60\} \quad \text{(离散层级)} $$

控制 agent 持有头寸的预期时间尺度。

**(d) 风险偏好 `α_i(t)`**

$$ \alpha_i(t) \in [0, 1] $$

α_i → 1：激进（满仓倾向）；α_i → 0：保守（轻仓/空仓）。

### 1.3 策略类型的涌现分类（非预设，事后聚类）

以下分类仅作为分析工具而非模型预设。通过聚类 `w_i(t)` 向量自然产生：

| 涌现类型 | 信号空间特征 | 数学判别式 |
|----------|-------------|-----------|
| 趋势跟踪 (TF) | w_MOM ≫ 0, w_REV ≈ 0 | `w_MOM / ‖w‖ > κ_TF` |
| 均值回复 (MR) | w_REV ≫ 0, w_MOM ≈ 0 | `w_REV / ‖w‖ > κ_MR` |
| 价值型 (VL) | w_FUND ≫ 0 | `w_FUND / ‖w‖ > κ_VL` |
| 波动率型 (VT) | w_VOL ≫ 0 | `w_VOL / ‖w‖ > κ_VT` |
| 混合型 (HY) | 多信号均衡 | 不满足以上单一判别式 |
| 噪声交易 (NS) | ‖w‖ ≈ 0 | `‖w‖ < ε_noise` |

其中 κ_TF, κ_MR, κ_VL, κ_VT ∈ (0, 1) 为阈值常数。

---

## 2. 状态变量全集

### 2.1 市场级全局状态

符号 `Ω(t)` 表示 t 时刻的市场全局状态：

$$\boxed{\Omega(t) = \bigl( \; P^{(n)}(t),\; r^{(n)}(t),\; V(t),\; F^{(n)}(t),\; \mathcal{O}(t) \;\bigr)_{n=1}^{N}}$$

| 变量 | 定义 |
|------|------|
| `P^{(n)}(t)` | 资产 n 在 t 时刻的清算价格 |
| `r^{(n)}(t)` | 资产 n 的对数收益率：`r^{(n)}(t) = ln(P^{(n)}(t)/P^{(n)}(t-1))` |
| `V(t)` | 市场总成交量 |
| `F^{(n)}(t)` | 资产 n 的基础价值（外生过程） |
| `𝒪(t)` | 限价订单簿快照（若使用订单簿撮合） |

### 2.2 Agent 级私有状态

| 变量 | 定义 | 来源 |
|------|------|------|
| `W_i(t)` | agent i 的总财富 | §4 更新 |
| `C_i(t)` | agent i 的现金余额 | `W_i(t) - Σ_n h_i^{(n)}(t) · P^{(n)}(t)` |
| `h_i^{(n)}(t)` | agent i 持有资产 n 的数量 | 交易后更新 |
| `Π_i(t)` | agent i 的策略 π_i(t)，见 §1.2 | §5 演化 |
| `fitness_i(t)` | agent i 的适应度值 | §5.1 定义 |
| `age_i(t)` | agent i 的存在期数 | 初始化为0，每期+1 |

### 2.3 信号空间 `S`（Agent 可感知的市场衍生量）

Agent i 在 t 时刻可观测的信号向量 `s_i(t) ∈ ℝ^D`：

| 信号 | 公式 | 参数 |
|------|------|------|
| S1 价格动量 | `r_{t-L_1:t}` 的指数加权均值 | L_1 = τ_i(t) |
| S2 移动平均交叉 | `MA_short(t) - MA_long(t) / MA_long(t)` | short=5, long=20 |
| S3 已实现波动率 | `σ_i(t) = √( Σ_{k=1}^{L_3} (r_{t-k} - r̄)^2 / (L_3-1) )` | L_3 = τ_i(t) |
| S4 成交量异常 | `(V(t) - V̄_L4) / σ_V` | L_4 = 20 |
| S5 基本面偏离 | `(F^{(n)}(t) - P^{(n)}(t)) / P^{(n)}(t)` | — |
| S6 短期反转 | `-r_{t-1:t-L_6}` 的累计收益 | L_6 = 3 |

### 2.4 演化动力学全局状态

| 变量 | 定义 |
|------|------|
| `P_eliminate` | 每 K 期淘汰的 agent 比例 |
| `σ_mut` | 策略变异幅度 |
| `λ_select` | 选择压力参数 |
| `K` | 演化代数间隔（期） |
| `G` | 演化代数计数器，G = ⌊t/K⌋ |

---

## 3. 行为规则

### 3.1 整体决策流程

Agent i 在每期 t 执行以下决策循环：

```
感知市场状态 → 计算综合信号 → 阈值判断 → 生成目标持仓 → 提交订单 → 成交
```

### 3.2 综合信号计算

Agent i 将感知到的信号向量 `s_i(t)` 与其策略权重 `w_i(t)` 内积：

$$\boxed{z_i(t) = \mathbf{w}_i(t)^\top \cdot \mathbf{s}_i(t) = \sum_{d=1}^{D} w_{i,d}(t) \cdot s_{i,d}(t)}$$

其中 `z_i(t)` 为方向强度（标量）；`z_i > 0`：看涨倾向，`z_i < 0`：看跌倾向。

### 3.3 阈值门控与交易方向

$$\boxed{\text{dir}_i(t) = \begin{cases}
+1, & z_i(t) > +\theta_i(t) \quad \text{(做多信号)} \\
-1, & z_i(t) < -\theta_i(t) \quad \text{(做空信号)} \\
0, & |z_i(t)| \le \theta_i(t) \quad \text{(不交易)}
\end{cases}}$$

当 dir_i(t) = 0 时，agent 不提交任何订单（观望）。

### 3.4 目标持仓量

持仓规模受风险偏好 `α_i`、波动率 `σ_i(t)`、现金 `C_i(t)` 联合决定：

$$\boxed{h_i^{\text{target}}(t) = \text{dir}_i(t) \cdot \alpha_i(t) \cdot \frac{C_i(t)}{\sigma_i(t) \cdot P(t)} \cdot \frac{1}{\tau_i(t)}}$$

解释：
- `/ σ_i(t)`：波动率高→仓位降低（风险预算）
- `· α_i(t)`：风险偏好调节
- `· 1/τ_i(t)`：持仓周期长的 agent 单期调仓幅度小

### 3.5 订单提交（简化：需求函数式）

在基于需求函数的价格出清中（非订单簿方案），agent 提交其净需求：

$$\boxed{D_i(t) = h_i^{\text{target}}(t) - h_i(t-1)}$$

若 `D_i(t) > 0`，agent 发出净买入；`D_i(t) < 0`，净卖出。

### 3.6 信息延迟（可选的异质信息结构）

部分 agent 观察的是滞后信号：

$$\tilde{\mathbf{s}}_i(t) = \mathbf{s}_i(t - \delta_i), \quad \delta_i \sim \text{Poi}(1)$$

引入信息不对称，防止完美同质预期。

---

## 4. 财富更新规则

### 4.1 持仓市值重估

每期末，agent 根据清算价格 `P^{(n)}(t)` 重估持仓：

$$\boxed{W_i(t) = C_i(t) + \sum_{n=1}^{N} h_i^{(n)}(t) \cdot P^{(n)}(t)}$$

### 4.2 现金动态

$$\boxed{C_i(t) = C_i(t-1) - \sum_{n=1}^{N} D_i^{(n)}(t) \cdot P^{(n)}(t) - TC_i(t)}$$

其中 `TC_i(t)` 为交易成本：

$$TC_i(t) = c_{\text{comm}} \cdot \sum_{n} |D_i^{(n)}(t)| \cdot P^{(n)}(t) + c_{\text{stamp}} \cdot \sum_{n} \max(D_i^{(n)}(t), 0) \cdot P^{(n)}(t)$$

- `c_comm`：佣金费率
- `c_stamp`：印花税率（卖出时收取）

### 4.3 收益率分解

Agent i 的单期收益率：

$$\boxed{R_i(t) = \frac{W_i(t) - W_i(t-1)}{W_i(t-1)}}$$

可分解为：

$$R_i(t) = \underbrace{\sum_n \omega_i^{(n)}(t-1) \cdot r^{(n)}(t)}_{\text{持仓收益}} - \underbrace{\frac{TC_i(t)}{W_i(t-1)}}_{\text{交易成本}}$$

其中 `ω_i^{(n)}(t-1)` 为 agent i 在资产 n 上的期初财富权重。

### 4.4 适应度（Fitness）

适应度函数为 agent 的累积对数收益与风险调整项的组合：

$$\boxed{\Phi_i(t) = \frac{1}{t} \sum_{k=1}^{t} \ln\bigl(1 + R_i(k)\bigr) - \frac{\gamma}{2} \cdot \widehat{\sigma}_i^2(t)}$$

其中：
- 第一项：平均对数收益率（最大化长期增长）
- `γ > 0`：风险厌恶系数
- `σ̂_i^2(t)`：agent i 收益率序列的样本方差

若在离散演化代数 G 中评估，适应度使用窗口版本：

$$\boxed{F_i(G) = \text{Sharpe}_i(G) = \frac{ \overline{R}_i(G) - r_f }{ \text{std}(R_i(G)) }}$$

其中 `R̄_i(G)` 为第 G 代窗口内的平均收益率，`r_f` 为无风险利率。

---

## 5. 策略复制机制

### 5.1 演化触发

演化操作每隔 K 期（交易期）触发一次。演化代数 G 定义为：

$$\boxed{G = \left\lfloor \frac{t}{K} \right\rfloor}$$

仅在 `t ≡ 0 (mod K)` 时执行以下操作。

### 5.2 淘汰操作

将当前所有 agent 按其适应度 `F_i(G)` 从低到高排序，淘汰末尾比例 `P_eliminate` 的 agent：

$$\mathcal{M}_{\text{survive}}^{(G)} = \left\{ i \;\middle|\; \text{rank}(F_i(G)) > P_{\text{eliminate}} \cdot M^{(G)} \right\}$$

淘汰 agent 的财富退还给市场（或按比例重新分配给生存者）。

### 5.3 选择概率（Roulette-Wheel Selection）

生存 agent 被选中作为"父代"的概率与其适应度相关：

$$\boxed{P_{\text{select}}(i \mid G) = \frac{\exp\bigl(\lambda_{\text{select}} \cdot F_i(G)\bigr)}{\sum_{j \in \mathcal{M}_{\text{survive}}^{(G)}} \exp\bigl(\lambda_{\text{select}} \cdot F_j(G)\bigr)}}$$

其中 `λ_select > 0` 控制选择压力：
- λ_select → 0：近乎均匀选择（弱选择）
- λ_select → ∞：仅最优个体被选择（强选择）

### 5.4 复制操作

从 `𝒢_survive^{(G)}` 中有放回抽取 `⌊P_eliminate · M^{(G)}⌋` 个后代 agent j'。每个后代继承父代 i 的策略，但赋予初始财富：

$$\boxed{\pi_{j''}(G) = \pi_{i}(G) \quad \text{(inherit)}}$$

$$\boxed{W_{j''}(G) = \frac{W_0}{|{\mathcal{M}_{\text{new}}^{(G)}}|}}$$

`W_0` 为新生 agent 的总初始财富池。这种财富重置机制防止了"富人恒富"的马太效应，使策略质量而非财富继承决定演化方向。

### 5.5 策略家族与祖源追踪

每个 agent 记录其"祖源链"（ancestry lineage）。策略家族 k 定义为共享共同祖先的一族 agent：

$$\mathcal{K}_k^{(G)} = \left\{ i \;\middle|\; \text{ancestor}^{(\tilde{G})}(i) = \text{ancestor}^{(\tilde{G})}(j),\; \forall i, j \in \mathcal{K}_k^{(G)} \right\}$$

祖源距离 `Ğ` 控制分类粒度。

---

## 6. 突变机制

### 6.1 突变触发

复制完成后，每个新生 agent j' 的每一个策略分量以概率 `p_mut` 独立突变。

### 6.2 信号权重突变

$$\boxed{\mathbf{w}_{j''}(G) = \mathbf{w}_{i}(G) + \boldsymbol{\epsilon},\quad \boldsymbol{\epsilon} \sim \mathcal{N}\bigl(\mathbf{0},\; \sigma_{\text{mut}}^2 \cdot \mathbf{I}_D\bigr)}$$

每个维度 d 独立施加噪声：

$$w_{j'',d} = w_{i,d} + \epsilon_d,\quad \epsilon_d \sim \mathcal{N}(0, \sigma_{\text{mut}}^2)$$

然后对 `w_{j''}` 进行 L2 归一化以保证尺度一致性：

$$\boxed{\tilde{\mathbf{w}}_{j''} = \frac{\mathbf{w}_{j''}}{\|\mathbf{w}_{j''}\|_2}}$$

### 6.3 阈值突变

$$\boxed{\theta_{j''}(G) = \min\left(\max\left(\theta_i(G) + \eta_\theta,\; \theta_{\min}\right),\; \theta_{\max}\right)}$$

其中 `η_θ ∼ 𝒩(0, σ_θ²)`，被截断在 [θ_min, θ_max] 区间。

### 6.4 持仓周期突变

$$\boxed{\tau_{j''}(G) = \begin{cases}
\tau_i(G) \cdot 2, & \text{以概率 } p_{\tau\uparrow} \\
\tau_i(G) \cdot \frac{1}{2}, & \text{以概率 } p_{\tau\downarrow} \\
\tau_i(G), & \text{以概率 } 1 - p_{\tau\uparrow} - p_{\tau\downarrow}
\end{cases}}$$

离散跳跃，保持在允许集合 {1, 3, 5, 10, 20, 60} 内。若越界则 clamp 到最近允许值。

### 6.5 风险偏好突变

$$\boxed{\alpha_{j''}(G) = \min\left(\max\left(\alpha_i(G) + \eta_\alpha,\; 0\right),\; 1\right)}$$

其中 `η_α ∼ 𝒩(0, σ_α²)`。

### 6.6 突变参数总表

| 参数 | 符号 | 建议值/范围 |
|------|------|------------|
| 突变概率 | p_mut | 0.1 – 0.3 |
| 权重变异幅度 | σ_mut | 0.01 – 0.10 |
| 阈值变异幅度 | σ_θ | 0.005 – 0.02 |
| 持仓周期上调概率 | p_{τ↑} | 0.05 |
| 持仓周期下调概率 | p_{τ↓} | 0.05 |
| 风险偏好变异幅度 | σ_α | 0.02 – 0.05 |

---

## 7. 市场撮合机制

### 7.1 两种可选方案

模型支持两种市场微观结构，可通过参数切换：

| 方案 | 描述 | 适用场景 |
|------|------|----------|
| **方案A：Walrasian Clearing** | 基于总供需的单一市场出清价 | 基准实验、长周期模拟 |
| **方案B：Limit Order Book** | 双拍卖限价订单簿 | 微观结构分析、制度实验 |

### 7.2 方案A：市场出清模型（Walrasian Clearing）

**净总超额需求**：

$$\boxed{ED^{(n)}(t) = \sum_{i=1}^{M} D_i^{(n)}(t)}$$

其中 `D_i^{(n)}(t)` 为 agent i 对资产 n 的净需求（§3.5）。

**对数价格更新**：

$$\boxed{\ln P^{(n)}(t) = \ln P^{(n)}(t-1) + \kappa \cdot ED^{(n)}(t) + \sigma_{\text{noise}} \cdot \xi^{(n)}(t)}$$

其中：
- `κ > 0`：价格对供需失衡的敏感度（Kyle's λ 的倒数概念）
- `σ_noise > 0`：噪声交易者冲击幅度
- `ξ^{(n)}(t) ∼ 𝒩(0, 1)` i.i.d.

**涨跌停板限制（中国A股）**：

$$\boxed{P^{(n)}(t) \in \bigl[ P^{(n)}(t-1) \cdot (1 - \ell_-),\; P^{(n)}(t-1) \cdot (1 + \ell_+) \bigr]}$$

其中 `ℓ₋ = ℓ₊ = 0.10`（±10% 涨跌停）。

若清算价超出涨跌停范围，则截断至边界，超出部分的需求量不成交。

### 7.3 方案B：限价订单簿模型（Limit Order Book）

- Agent i 根据其目标持仓和价格预期提交限价单 `(q_i, price_limit_i, side_i)`。
- 订单簿维护 5 档买价和卖价。
- 成交遵循价格优先+时间优先原则。
- 订单簿中间价作为清算价格 `P^{(n)}(t)`。

**（方案B的完整规格留待后续补充，基准实验使用方案A。）**

### 7.4 基础价值过程

资产 n 的基础价值遵循几何布朗运动加均值回复：

$$\boxed{dF^{(n)}(t) = \mu_F \cdot F^{(n)}(t) \, dt + \phi \cdot (\bar{F}^{(n)} - F^{(n)}(t)) \, dt + \sigma_F \cdot F^{(n)}(t) \, dW_t}$$

离散化形式：

$$\boxed{F^{(n)}(t) = F^{(n)}(t-1) \cdot \exp\left(\mu_F - \frac{\sigma_F^2}{2} + \phi \cdot \left(\frac{\bar{F}^{(n)}}{F^{(n)}(t-1)} - 1\right) + \sigma_F \cdot \xi_t\right)}$$

| 参数 | 含义 | 基准值 |
|------|------|--------|
| μ_F | 漂移率 | 0.0 |
| σ_F | 基础波动率 | 0.01 |
| φ | 均值回复强度 | 0.001 |
| F̄^{(n)} | 长期均值 | 100 |

### 7.5 成交量

$$\boxed{V(t) = \sum_{n=1}^{N} \sum_{i=1}^{M} |D_i^{(n)}(t)|}$$

---

## 8. Alpha 测度指标

### 8.1 Alpha 的理论定义

策略家族 k 在时刻 t 的 Alpha 定义为其持仓组合相对基准的超额收益：

$$\boxed{\alpha_k(t \mid \Delta) = \frac{1}{\Delta} \sum_{s=t-\Delta+1}^{t} \left( R_k(s) - R_{\text{bench}}(s) \right) }$$

其中：
- `R_k(s)`：策略家族 k 在第 s 期的等权/市值加权平均收益率
- `R_bench(s)`：基准收益率（等价加权市场组合或无风险利率）
- `Δ`：回顾窗口长度（如 Δ = 60 期）

### 8.2 策略家族收益率

$$\boxed{R_k(t) = \frac{1}{|\mathcal{K}_k(t)|} \sum_{i \in \mathcal{K}_k(t)} R_i(t)}$$

或财富加权版本：

$$\boxed{R_k^W(t) = \frac{\sum_{i \in \mathcal{K}_k(t)} W_i(t-1) \cdot R_i(t)}{\sum_{i \in \mathcal{K}_k(t)} W_i(t-1)}}$$

### 8.3 Alpha 生命周期五个阶段

对每个可追踪策略家族 k，定义五个阶段的关键时间节点：

| 阶段 | 时间定义 | 条件 |
|------|----------|------|
| **阶段I：探索期** | t ∈ [t_0, t_emerge) | α_k(t) 不显著异于 0 |
| **阶段II：爆发期** | t ∈ [t_emerge, t_peak) | α_k(t) > 0 且 dα_k/dt > 0 |
| **阶段III：拥挤期** | t ∈ [t_peak, t_half) | α_k(t) > 0 但 dα_k/dt < 0 |
| **阶段IV：衰退期** | t ∈ [t_half, t_extinct) | α_k(t) → 0⁺ |
| **阶段V：灭绝/恢复** | t ≥ t_extinct | α_k(t) ≈ 0 或 α_k(t) 重新上升 |

其中：
- `t_emerge = min{ t : α_k(t) > α_thresh }`
- `t_peak = argmax_t α_k(t ∣ Δ)`
- `t_half = min{ t ≥ t_peak : α_k(t) ≤ α_k(t_peak) / 2 }` （Alpha半衰期）
- `t_extinct = min{ t ≥ t_peak : α_k(t) ≤ ε_extinct }`

### 8.4 Alpha 半衰期

$$\boxed{t_{\text{half}}^{(k)} = \min\left\{ t \geq t_{\text{peak}}^{(k)} \;\middle|\; \alpha_k(t) \leq \frac{1}{2} \alpha_k(t_{\text{peak}}^{(k)}) \right\} - t_{\text{peak}}^{(k)}}$$

这是 Alpha 衰减速度的核心度量。半衰期越短，Alpha 衰减越快。

### 8.5 策略拥挤度

策略家族 k 的拥挤度定义为其控制的财富占市场总财富的比例：

$$\boxed{C_k(t) = \frac{\sum_{i \in \mathcal{K}_k(t)} W_i(t)}{\sum_{j=1}^{M} W_j(t)}}$$

拥挤度与 Alpha 的关系构成核心研究问题（Q2）。

### 8.6 市场效率度量

由 t 期价格序列计算：

**(a) 一阶自相关系数**：

$$\boxed{\rho_1(t \mid \Delta) = \frac{\sum_{s=t-\Delta+2}^{t} (r_s - \bar{r})(r_{s-1} - \bar{r})}{\sum_{s=t-\Delta+1}^{t} (r_s - \bar{r})^2}}$$

|ρ_1| → 0：市场有效；|ρ_1| ≫ 0：可预测性存在。

**(b) Hurst 指数 H**：使用 R/S 分析方法估计。H = 0.5 → 随机游走（有效）；H > 0.5 → 趋势持续性；H < 0.5 → 均值回复。

### 8.7 策略多样性熵

$$\boxed{H_{\text{strat}}(t) = -\sum_{k=1}^{K(t)} p_k(t) \cdot \ln p_k(t)}$$

其中 `p_k(t) = |𝒦_k(t)| / M(t)` 为策略家族 k 的 agent 数量占比，`K(t)` 为活跃策略家族数量。

### 8.8 生态位重叠度（Pianka Index）

策略家族 k 与 ℓ 之间的生态位重叠度：

$$\boxed{O_{k\ell}(t) = \frac{\bar{\mathbf{w}}_k(t)^\top \cdot \bar{\mathbf{w}}_\ell(t)}{\|\bar{\mathbf{w}}_k(t)\|_2 \cdot \|\bar{\mathbf{w}}_\ell(t)\|_2}}$$

其中 `w̄_k(t)` 为策略家族 k 的平均权重向量：

$$\bar{\mathbf{w}}_k(t) = \frac{1}{|\mathcal{K}_k(t)|} \sum_{i \in \mathcal{K}_k(t)} \mathbf{w}_i(t)$$

O_{kℓ} ∈ [-1, 1]，O_{kℓ} → 1 表示高度重叠（激烈竞争），O_{kℓ} → 0 表示正交（无竞争），O_{kℓ} → -1 表示反向利用（互利可能）。

### 8.9 Alpha-拥挤度弹性

策略间的交叉弹性衡量竞争强度：

$$\boxed{\varepsilon_{\alpha}(k) = \frac{d\alpha_k}{dC_k} \cdot \frac{C_k}{\alpha_k} \approx \frac{\Delta \ln \alpha_k}{\Delta \ln C_k}}$$

ε_α(k) < 0 且 |ε_α(k)| 大 → Alpha 对拥挤高度敏感。

---

## 9. 模型参数汇总

### 9.1 结构参数

| 符号 | 含义 | 基准值 | 扫描范围 |
|------|------|--------|----------|
| M | Agent总数 | 1000 | 200 – 2000 |
| N | 资产数量 | 1 | 1 – 10 |
| T | 模拟总期数 | 10000 | 5000 – 20000 |
| D | 信号空间维度 | 6 | 4 – 10 |

### 9.2 演化参数

| 符号 | 含义 | 基准值 | 扫描范围 |
|------|------|--------|----------|
| K | 演化周期（期） | 200 | 50 – 500 |
| P_eliminate | 淘汰比例 | 0.20 | 0.05 – 0.40 |
| λ_select | 选择压力 | 3.0 | 0.5 – 10.0 |
| p_mut | 突变概率 | 0.20 | 0.05 – 0.50 |
| σ_mut | 权重变异幅度 | 0.03 | 0.005 – 0.15 |
| σ_θ | 阈值变异幅度 | 0.01 | 0.002 – 0.05 |
| σ_α | 风险偏好变异幅度 | 0.03 | 0.01 – 0.10 |

### 9.3 市场参数

| 符号 | 含义 | 基准值 |
|------|------|--------|
| κ | 价格-供需敏感度 | 0.001 |
| σ_noise | 噪声交易冲击 | 0.005 |
| ℓ₊ = ℓ₋ | 涨跌停板 | 0.10 |
| μ_F | 基础价值漂移 | 0.0 |
| σ_F | 基础价值波动率 | 0.01 |
| φ | 均值回复强度 | 0.001 |
| c_comm | 佣金费率 | 0.0003 |
| c_stamp | 印花税率 | 0.001 |

### 9.4 测量参数

| 符号 | 含义 | 基准值 |
|------|------|--------|
| Δ | Alpha滚动窗口 | 60 |
| α_thresh | Alpha显著阈值 | 0.002 |
| ε_extinct | Alpha消亡阈值 | 0.0005 |
| γ | 适应度风险厌恶系数 | 1.0 |
| r_f | 无风险利率 | 0.0 |

---

## 10. 模型运行时伪代码

### 10.1 主循环

```
Initialize: M agents with random π_i(0), equal W_i(0) = W_0
Initialize: P^{(n)}(0) = F^{(n)}(0) = 100

for t = 1 to T:
    1. Update fundamental values F^{(n)}(t) via §7.4
    2. For each agent i:
       a. Compute signal vector s_i(t) from market data (§2.3)
       b. Apply info delay δ_i if applicable (§3.6)
       c. Compute z_i(t) = w_i(t)·s_i(t) (§3.2)
       d. Determine dir_i(t) via threshold (§3.3)
       e. Compute target holdings (§3.4)
       f. Submit net demand D_i^{(n)}(t) (§3.5)
    3. Aggregate ED^{(n)}(t) and clear market (§7.2)
    4. Update P^{(n)}(t) and apply price limits
    5. Execute trades, update h_i^{(n)}(t)
    6. Update wealth W_i(t), cash C_i(t) (§4)
    7. Record metrics: returns, alpha, crowding, entropy (§8)
    
    if t mod K = 0:
        8. Compute fitness F_i(G) for all agents (§4.4)
        9. Eliminate weakest P_eliminate fraction (§5.2)
       10. Select parents via roulette (§5.3)
       11. Generate offspring via replication (§5.4) + mutation (§6)
       12. Assign offspring wealth W_0 / |new agents|
       13. Increment generation G
```

### 10.2 初始化细节

各 agent 的初始策略随机化：

$$\begin{aligned}
\mathbf{w}_i(0) &\sim \mathcal{N}(\mathbf{0}, \sigma_{\text{init}}^2 \cdot \mathbf{I}_D),\quad \text{then }\tilde{\mathbf{w}}_i = \mathbf{w}_i / \|\mathbf{w}_i\|_2 \\
\theta_i(0) &\sim \mathcal{U}(\theta_{\min}, \theta_{\max}) \\
\tau_i(0) &\sim \text{DiscreteUniform}(\{1, 3, 5, 10, 20, 60\}) \\
\alpha_i(0) &\sim \mathcal{U}(0.2, 0.8)
\end{aligned}$$

$$\boxed{W_i(0) = \frac{W_{\text{total}}}{M},\quad h_i^{(n)}(0) = 0,\quad C_i(0) = W_i(0)}$$

---

*END OF MODEL_SPEC.md*
