# EVO-ASM Mesa 项目架构文档 (ARCHITECTURE.md)

> 基于 MODEL_SPEC.md v1.0 | 框架：Mesa ≥ 2.x | 语言：Python
> 本文档只描述架构与类设计，不含实现代码

---

## 1. 目录结构

```
evo_asm/
│
├── __init__.py                        # 包入口，暴露 EVOASMModel, run 等顶层符号
├── model.py                           # EVOASMModel — Mesa Model 子类，顶层编排
├── config.py                          # 模型参数集中定义（dataclass）
├── run.py                             # 单次运行入口 + BatchRunner 配置
│
├── agents/
│   ├── __init__.py
│   ├── trading_agent.py               # TradingAgent — Mesa Agent 子类
│   └── strategy.py                    # Strategy — 策略编码值对象
│
├── market/
│   ├── __init__.py
│   ├── base_market.py                 # BaseMarket — 市场抽象基类
│   ├── walrasian_market.py            # WalrasianMarket — 方案A（基准）
│   ├── order_book.py                  # OrderBook — 限价订单簿
│   ├── order_book_market.py           # OrderBookMarket — 方案B（扩展）
│   └── asset.py                       # Asset — 资产定义（名称、基础价值过程）
│
├── evolution/
│   ├── __init__.py
│   └── evolution_engine.py            # EvolutionEngine — 复制-突变-选择
│
├── metrics/
│   ├── __init__.py
│   ├── metrics_collector.py           # MetricsCollector — 全局度量采集
│   └── alpha_tracker.py               # AlphaTracker — Alpha生命周期追踪
│
├── signals/
│   ├── __init__.py
│   └── signal_computer.py             # SignalComputer — D维信号计算
│
└── utils/
    ├── __init__.py
    └── math_utils.py                  # 辅助数学函数（L2归一化、滚动统计等）
```

---

## 2. 模块职责矩阵

| 模块 | 职责 | 依赖 |
|------|------|------|
| `model.py` | 顶层协调器；step() 编排顺序；持有所有子模块引用 | 所有其他模块 |
| `config.py` | 集中声明所有可配置参数，提供默认值与范围 | 无 |
| `run.py` | 入口脚本；创建 Model 实例；调用 Mesa BatchRunner | model, config |
| `agents/` | Agent 的 Mesa 定义 + 策略值对象 | signals, market |
| `market/` | 资产定义、价格形成、交易执行、订单簿 | 无外部 |
| `evolution/` | 淘汰、选择、复制、突变 | agents, config |
| `metrics/` | 所有定量指标的采集、聚合、导出 | model (读取) |
| `signals/` | 从市场数据计算信号向量 s(t) | market |
| `utils/` | 纯函数工具（L2范数、滚动窗口统计等） | 无 |

---

## 3. 类设计总览

```
              ┌──────────────────────────────────┐
              │         EVOASMModel               │
              │  (mesa.Model)                     │
              │  ┌──────────────────────────────┐ │
              │  │ scheduler: StagedActivation  │ │
              │  │ agents:   list[TradingAgent] │ │
              │  │ market:   BaseMarket         │ │
              │  │ evo_eng:  EvolutionEngine    │ │
              │  │ metrics:  MetricsCollector   │ │
              │  │ signals:  SignalComputer     │ │
              │  │ config:   EVOASMConfig       │ │
              │  └──────────────────────────────┘ │
              └───────┬────────────┬──────────────┘
                      │            │
          ┌───────────▼──┐  ┌──────▼────────────┐
          │ TradingAgent │  │   BaseMarket       │
          │ (mesa.Agent) │  │   (ABC)            │
          │ ┌──────────┐ │  │   ├─ Walrasian     │
          │ │ Strategy │ │  │   └─ OrderBook     │
          │ └──────────┘ │  └───────────────────┘
          └───────────────┘
```

---

## 4. 详细类规格

### 4.1 `EVOASMConfig` — 参数集中定义

**位置**：`evo_asm/config.py`

**类型**：`@dataclass` (frozen)

**职责**：将所有 MODEL_SPEC.md §9 中的参数集中为一个不可变配置对象，保证参数可追溯、可序列化、可复现。

**字段分组**：

| 分组 | 字段 | 类型 | 默认值 |
|------|------|------|--------|
| **结构** | `M` | int | 1000 |
| | `N` | int | 1 |
| | `T` | int | 10000 |
| | `D` | int | 6 |
| **演化** | `K` | int | 200 |
| | `P_eliminate` | float | 0.20 |
| | `lambda_select` | float | 3.0 |
| | `p_mut` | float | 0.20 |
| | `sigma_mut` | float | 0.03 |
| | `sigma_theta` | float | 0.01 |
| | `sigma_alpha` | float | 0.03 |
| **市场** | `kappa` | float | 0.001 |
| | `sigma_noise` | float | 0.005 |
| | `price_limit` | float | 0.10 |
| | `mu_F` | float | 0.0 |
| | `sigma_F` | float | 0.01 |
| | `phi` | float | 0.001 |
| | `F_bar` | float | 100.0 |
| | `c_comm` | float | 0.0003 |
| | `c_stamp` | float | 0.001 |
| **测量** | `delta_alpha` | int | 60 |
| | `alpha_thresh` | float | 0.002 |
| | `eps_extinct` | float | 0.0005 |
| | `gamma` | float | 1.0 |
| | `r_f` | float | 0.0 |
| **初始** | `W_total` | float | 1e7 |
| | `sigma_init` | float | 0.10 |
| | `theta_min` | float | 0.01 |
| | `theta_max` | float | 0.50 |
| **种子** | `seed` | int \| None | None |

**方法**：
- `from_dict(d: dict) -> EVOASMConfig` — 从字典构建，用于 BatchRunner 参数扫描
- `to_dict() -> dict` — 序列化，用于日志记录

---

### 4.2 `EVOASMModel` — 顶层模型

**位置**：`evo_asm/model.py`

**继承**：`mesa.Model`

**职责**：
- 创建和持有所有子模块（Market, EvolutionEngine, MetricsCollector, SignalComputer, Agent 集合）
- 定义 `step()` 的执行顺序
- 管理 Mesa Scheduler（使用 StagedActivation 实现三阶段决策）

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `config` | EVOASMConfig | 全部参数（不可变） |
| `schedule` | StagedActivation | Mesa 调度器 |
| `market` | BaseMarket | 市场实例（Walrasian 或 OrderBook） |
| `evolution_engine` | EvolutionEngine | 演化引擎（每 K 步调用一次） |
| `metrics_collector` | MetricsCollector | 度量采集器 |
| `signal_computer` | SignalComputer | 信号计算器 |
| `datacollector` | DataCollector | Mesa 内置数据采集器（辅助） |
| `step_count` | int | 当前步数 t |
| `generation` | int | 当前演化代数 G = floor(t / K) |

**`step()` 执行流程**：

```
step():
    1. 更新基础价值 F^{(n)}(t)           → market.update_fundamentals()
    2. 执行 Stage 1: agent.perceive()    → 每个 agent 调用 signal_computer
    3. 执行 Stage 2: agent.decide()      → 每个 agent 计算净需求
    4. 聚合总供需 ED^{(n)}(t)            → market.aggregate_demand()
    5. 市场出清 P^{(n)}(t)               → market.clear()
    6. 执行 Stage 3: agent.act()         → 更新持仓、财富
    7. 记录所有度量指标                   → metrics_collector.record_step()
    8. 若 t % K == 0: 演化               → evolution_engine.evolve()
    9. step_count += 1
```

**关键方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `__init__` | `(config, market_type="walrasian")` | 构造模型，初始化所有子模块和 agent |
| `step` | `() -> None` | 单步推进 |
| `_create_agents` | `() -> None` | 初始化 M 个随机 TradingAgent |
| `run` | `(n_steps: int) -> pd.DataFrame` | 运行 n_steps，返回 metrics_collector 数据 |

**依赖注入关系**：
- `EVOASMModel` 持有对所有子模块的引用
- `TradingAgent` 通过 `self.model` 访问 Market, SignalComputer 等共享资源（Mesa 惯例）
- `EvolutionEngine` 接收 model 引用以访问 agent 列表和 config

---

### 4.3 `BaseMarket` — 市场抽象基类

**位置**：`evo_asm/market/base_market.py`

**类型**：ABC (Abstract Base Class)

**职责**：定义市场模块的公共接口，支持 Walrasian 出清和订单簿两种实现。

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `assets` | list[Asset] | N 个资产实例 |
| `P` | np.ndarray[N] | 当前价格向量 |
| `P_history` | list[np.ndarray] | 历史价格序列 |
| `V` | float | 当前成交量 |
| `config` | EVOASMConfig | 市场参数 |

**抽象方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `update_fundamentals` | `() -> None` | 更新所有资产的 F^{(n)}(t) |
| `clear` | `(demands: np.ndarray[M, N]) -> None` | 核心：根据 agent 需求向量计算清算价格 |
| `get_price` | `(asset_idx: int) -> float` | 返回资产 n 的最新价格 |
| `get_return` | `(asset_idx: int) -> float` | 返回资产 n 的最新对数收益率 |

**具体方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `execute_trade` | `(agent, asset, quantity, price) -> None` | 执行成交，更新 agent 持仓和现金 |
| `aggregate_demand` | `() -> np.ndarray[N]` | 遍历所有 agent，求和净需求 |
| `reset` | `() -> None` | 重置市场状态（用于多轮模拟） |

---

### 4.4 `WalrasianMarket` — 方案A：市场出清

**位置**：`evo_asm/market/walrasian_market.py`

**继承**：`BaseMarket`

**职责**：实现 MODEL_SPEC.md §7.2 的 Walrasian Clearing 机制。

**核心公式**：

```
ln P_n(t) = ln P_n(t-1) + κ · Σ_i D_i^{(n)}(t) + σ_noise · ξ(t)

应用涨跌停板 clamp：
P_n(t) ← clamp( P_n(t),
                 P_n(t-1) · (1 - ℓ₋),
                 P_n(t-1) · (1 + ℓ₊) )
```

**额外属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `rng` | np.random.Generator | 噪声生成器 |
| `_demand_buffer` | np.ndarray[M, N] | 当前步的 agent 需求暂存 |

**关键方法实现说明**：

- `clear(demands)`: 逐资产计算 ED^{(n)} → 更新对数价格 → 应用涨跌停板 → 执行成交
- `update_fundamentals()`: 按 GBM+均值回复离散化公式更新

---

### 4.5 `OrderBook` — 限价订单簿

**位置**：`evo_asm/market/order_book.py`

**类型**：独立类（非 Mesa Agent，是纯数据结构）

**职责**：维护一只资产的双边限价订单簿，支持提交、撤销、撮合。

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `bids` | SortedList[Order] | 买盘（价格降序） |
| `asks` | SortedList[Order] | 卖盘（价格升序） |
| `trades` | list[Trade] | 当前步成交记录 |
| `tick_size` | float | 最小价格变动单位 |
| `depth_levels` | int | 保留档数（默认 5） |
| `asset_idx` | int | 绑定资产索引 |

**内部类型**：

| 类型 | 字段 |
|------|------|
| `Order` | `(agent_id, side: {BUY, SELL}, quantity, price_limit, timestamp, order_type: {LIMIT, MARKET})` |
| `Trade` | `(buyer_id, seller_id, quantity, price, timestamp)` |

**关键方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `submit` | `(order: Order) -> list[Trade]` | 提交订单，立即尝试撮合，返回本次触发的成交列表 |
| `cancel` | `(order_id) -> bool` | 撤销未成交订单 |
| `get_mid_price` | `() -> float` | best_bid 和 best_ask 的均值；若一侧为空则用最近成交价 |
| `get_spread` | `() -> float` | best_ask - best_bid |
| `get_depth` | `(side, levels) -> list[(price, volume)]` | 获取深度快照 |
| `clear_expired` | `(current_step) -> None` | 清除过期的 GTC 订单 |

**撮合逻辑（match）**：

```
match(incoming_order):
    若 incoming_order 是 BUY：
        遍历 asks（价格升序）：
            若 ask.price ≤ incoming_order.price_limit：
                成交价 = ask.price（价格优先，先到者得）
                成交量 = min(incoming_order.qty, ask.qty)
                记录 Trade
                更新剩余量
            否则：break
        若仍有剩余 → 挂入 bids
    若 incoming_order 是 SELL（对称逻辑）
    返回 trades[]
```

---

### 4.6 `OrderBookMarket` — 方案B：订单簿驱动市场

**位置**：`evo_asm/market/order_book_market.py`

**继承**：`BaseMarket`

**职责**：使用 N 个 OrderBook 实例的市场，agent 不提交需求函数而提交限价单。

**额外属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `books` | list[OrderBook] | 每资产一个订单簿 |

**与 WalrasianMarket 的核心差异**：

- `clear()` 方法被 `match_all()` 替代——遍历所有 order_book 撮合内部订单
- agent 在 decide() 阶段生成 `(side, qty, price_limit)` 而非净需求
- 价格发现来自订单簿撮合而非供需方程

---

### 4.7 `Asset` — 资产定义

**位置**：`evo_asm/market/asset.py`

**类型**：`@dataclass`

**字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | str | 资产名称 |
| `index` | int | 在资产数组中的索引 |
| `F` | float | 当前基础价值 |
| `F_history` | list[float] | 基础价值时序 |
| `mu_F` | float | 漂移率（可覆盖全局） |
| `sigma_F` | float | 波动率（可覆盖全局） |

---

### 4.8 `Strategy` — 策略值对象

**位置**：`evo_asm/agents/strategy.py`

**类型**：`@dataclass` (mutable fields for mutation)

**职责**：承载 MODEL_SPEC.md §1.2 的策略编码 `π_i = (w_i, θ_i, τ_i, α_i)`。

**数学对应**：

| 字段 | 类型 | 数学符号 | 约束 |
|------|------|----------|------|
| `weights` | np.ndarray[D] | `w_i` | L2归一化后 ‖w‖₂ = 1 |
| `threshold` | float | `θ_i` | [θ_min, θ_max] |
| `holding_period` | int | `τ_i` | {1, 3, 5, 10, 20, 60} |
| `risk_appetite` | float | `α_i` | [0, 1] |

**方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `compute_direction` | `(signals: np.ndarray[D]) -> int` | 计算 z = wᵀ·s，返回 dir ∈ {-1, 0, +1} |
| `compute_target_holdings` | `(cash, price, volatility) -> float` | 按 §3.4 公式计算 h_i^{target} |
| `clone` | `() -> Strategy` | 深拷贝（用于复制操作） |
| `mutate_weights` | `(sigma) -> None` | 权重加高斯噪声 + L2归一化 |
| `mutate_threshold` | `(sigma) -> None` | 阈值加噪声 + clamp |
| `mutate_holding_period` | `(p_up, p_down) -> None` | 持仓周期离散跳跃 |
| `mutate_risk` | `(sigma) -> None` | 风险偏好加噪声 + clamp |
| `to_tuple` | `() -> tuple` | 用于聚类分析的向量化表示 |

---

### 4.9 `TradingAgent` — 交易者 Agent

**位置**：`evo_asm/agents/trading_agent.py`

**继承**：`mesa.Agent`

**职责**：MODEL_SPEC.md §3 的行为规则实现。每个 agent 拥有独立的 Strategy、财富、持仓。

**属性**：

| 属性 | 类型 | 数学符号 | 说明 |
|------|------|----------|------|
| `strategy` | Strategy | `π_i` | 当前策略编码 |
| `cash` | float | `C_i` | 现金余额 |
| `holdings` | np.ndarray[N] | `h_i^{(n)}` | 各资产持仓量 |
| `wealth` | float | `W_i` | 总财富（cash + holdings·P） |
| `wealth_history` | list[float] | — | 财富时序 |
| `return_history` | list[float] | — | 收益率时序 |
| `age` | int | — | 存活步数 |
| `parent_id` | int \| None | — | 父代 unique_id（演化追踪） |
| `ancestor_id` | int \| None | — | 祖源（策略家族根） |
| `info_delay` | int | `δ_i` | 信息延迟期数，∼ Poi(1) |

**Mesa StagedActivation 三阶段方法**：

| 阶段 | 方法 | 职责 |
|------|------|------|
| Stage 1 | `perceive()` | 通过 model.signal_computer 获取 s_i(t)；应用 info_delay |
| Stage 2 | `decide()` | 调用 strategy.compute_direction() → 计算目标持仓 → 计算净需求 D_i^{(n)} → 写入 model.market 的需求缓冲 |
| Stage 3 | `act()` | 根据成交结果更新 holdings 和 cash；重算 wealth |

**辅助方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `compute_wealth` | `(prices) -> float` | 按市价重估 W_i = C_i + Σ h_i^{(n)} · P^{(n)} |
| `record` | `() -> None` | 记录 wealth, return 到历史 |
| `get_return` | `() -> float` | 当前步收益率 R_i(t) |

**Mesa 集成注意**：
- 通过 `self.model` 访问共享资源（Market, SignalComputer, EvolutionEngine）
- `self.unique_id` 为 Mesa 自动分配的整数 id
- `self.model.schedule` 管理 agent 激活顺序

---

### 4.10 `SignalComputer` — 信号计算器

**位置**：`evo_asm/signals/signal_computer.py`

**类型**：独立类（不是 Agent）

**职责**：从市场数据计算 D 维信号向量 `s_i(t)`。MODEL_SPEC.md §2.3。

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `price_history` | list[np.ndarray] | 价格序列（由 model 每步追加） |
| `volume_history` | list[float] | 成交量序列 |
| `config` | EVOASMConfig | 参数 |
| `_cache` | dict | 中间计算结果缓存（避免重复计算 MA 等） |

**方法**：

| 方法 | 签名 | 返回 | 对应信号 |
|------|------|------|----------|
| `compute_all` | `(holding_period) -> np.ndarray[D]` | 长度为 D 的信号向量 | S1–S6 |
| `momentum` | `(lookback) -> float` | 过去 lookback 期的 EWA 收益率 | S1 |
| `ma_crossover` | `() -> float` | (MA_short − MA_long) / MA_long | S2 |
| `realized_vol` | `(lookback) -> float` | 已实现波动率 | S3 |
| `volume_anomaly` | `() -> float` | (V_t − V̄) / σ_V | S4 |
| `fundamental_deviation` | `(asset_idx) -> float` | (F − P) / P | S5 |
| `short_reversal` | `() -> float` | 近期负累收益率 | S6 |

---

### 4.11 `EvolutionEngine` — 演化引擎

**位置**：`evo_asm/evolution/evolution_engine.py`

**类型**：独立类

**职责**：每 K 步执行一次达尔文式演化循环。MODEL_SPEC.md §5 §6。

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `model_ref` | WeakRef[EVOASMModel] | 对 model 的弱引用（避免循环） |
| `rng` | np.random.Generator | 随机数生成器 |
| `generation` | int | 演化代数 G |
| `elimination_history` | list[list[int]] | 每代被淘汰 agent 的 id 列表 |
| `mutation_log` | list[dict] | 突变事件日志 |

**`evolve()` 方法流程**（核心）：

```
evolve():
    ┌─────────────────────────────────────────┐
    │ 1. 计算适应度 F_i(G)                      │
    │    = Sharpe_i(G)  (§4.4)                  │
    │    对所有 agent 排序                        │
    ├─────────────────────────────────────────┤
    │ 2. 淘汰 (eliminate)                       │
    │    移除末尾 P_eliminate 比例的 agent        │
    │    记录 eliminated_ids                     │
    ├─────────────────────────────────────────┤
    │ 3. 选择 (select_parents)                  │
    │    对幸存 agent 按 roulette-wheel 选择     │
    │    P_select(i) ∝ exp(λ · F_i)            │
    │    抽取 N_new 个父代（可重复）              │
    ├─────────────────────────────────────────┤
    │ 4. 复制 (replicate)                       │
    │    每个父代产生一个后代 agent               │
    │    后代 strategy = 父代 strategy.clone()    │
    │    后代 wealth = W_0 / N_new               │
    │    记录 parent_id, ancestor_id             │
    ├─────────────────────────────────────────┤
    │ 5. 突变 (mutate)                           │
    │    对每个后代，以 p_mut 概率独立突变：        │
    │    · weights  += ε ∼ N(0, σ²_mut), L2 归一化 │
    │    · threshold += ε ∼ N(0, σ²_θ), clamp    │
    │    · holding_period 离散跳跃               │
    │    · risk_appetite += ε ∼ N(0, σ²_α), clamp│
    ├─────────────────────────────────────────┤
    │ 6. 注册后代到 model.schedule               │
    │    更新 agent 计数                          │
    │    generation += 1                         │
    └─────────────────────────────────────────┘
```

**关键方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `evolve` | `() -> EvolutionReport` | 完整执行一次演化循环 |
| `_compute_fitness` | `(agents) -> np.ndarray` | 计算所有 agent 的夏普比率 |
| `_eliminate` | `(agents, fitness) -> (survivors, eliminated)` | 淘汰末尾 |
| `_select_parents` | `(survivors, fitness, n) -> list[Agent]` | 轮盘赌选择 |
| `_replicate` | `(parent, offspring_id) -> TradingAgent` | 创建一个后代 |
| `_mutate` | `(offspring: TradingAgent) -> None` | 对后代策略施加突变 |

**EvolutionReport**（内部 dataclass）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `generation` | int | G |
| `n_eliminated` | int | 淘汰 agent 数 |
| `n_survivors` | int | 留存 agent 数 |
| `n_new` | int | 新生 agent 数 |
| `mean_fitness_before` | float | 淘汰前平均适应度 |
| `mean_fitness_after` | float | 复制后平均适应度 |
| `mutation_count` | int | 发生突变的基因数 |
| `strategy_diversity_before` | float | 淘汰前策略熵 |

---

### 4.12 `MetricsCollector` — 度量采集器

**位置**：`evo_asm/metrics/metrics_collector.py`

**类型**：独立类

**职责**：每步采集所有 MODEL_SPEC.md §8 定义的度量指标。提供时间序列查询和聚合。

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `model_ref` | WeakRef[EVOASMModel] | 对 model 的弱引用 |
| `data` | dict[str, list] | 主存储：key=指标名，value=时间序列 |
| `alpha_tracker` | AlphaTracker | Alpha 生命周期追踪子模块 |
| `config` | EVOASMConfig | 测量参数 |

**`record_step()` 采集的指标清单**：

| 指标 | 存储 key | 数学符号 | 计算方式 |
|------|----------|----------|----------|
| 价格 | `"price"` | P(t) | model.market.get_price() |
| 对数收益率 | `"return"` | r(t) | ln(P_t / P_{t-1}) |
| 成交量 | `"volume"` | V(t) | Σ |D_i| |
| 策略熵 | `"strategy_entropy"` | H_strat(t) | -Σ p_k · ln(p_k) |
| 一阶自相关 | `"acf1"` | ρ₁(t\|Δ) | 滚动窗口自相关 |
| Hurst 指数 | `"hurst"` | H(t\|Δ) | 滚动 R/S 分析 |
| 策略家族数 | `"n_families"` | K(t) | 活跃祖源数 |
| 平均适应度 | `"mean_fitness"` | — | 所有 agent 的平均 Sharpe |
| 财富基尼系数 | `"wealth_gini"` | — | agent 财富分布的基尼系数 |
| Alpha(每家族) | `"alpha_k"` | α_k(t\|Δ) | 见 AlphaTracker |

**方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `record_step` | `() -> None` | 采集当前步的所有指标 |
| `to_dataframe` | `() -> pd.DataFrame` | 导出为 DataFrame |
| `get_metric` | `(key, start, end) -> np.ndarray` | 时间窗口查询 |
| `compute_strategy_entropy` | `() -> float` | 计算当前 H_strat |
| `compute_wealth_gini` | `() -> float` | 计算当前财富基尼系数 |
| `compute_acf1` | `(window) -> float` | 滚动一阶自相关 |
| `cluster_strategies` | `() -> dict[int, list[int]]` | 按 ancestor_id 聚类为策略家族 |
| `reset` | `() -> None` | 清空所有序列（用于新模拟） |

---

### 4.13 `AlphaTracker` — Alpha 生命周期追踪器

**位置**：`evo_asm/metrics/alpha_tracker.py`

**类型**：独立类（被 MetricsCollector 持有）

**职责**：追踪每个策略家族 k 的 Alpha 完整生命周期。MODEL_SPEC.md §8.3。

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `families` | dict[int, AlphaLifecycle] | key=ancestor_id，value=生命周期数据 |
| `window` | int | Δ（Alpha 滚动窗口） |
| `alpha_thresh` | float | 显著阈值 |
| `eps_extinct` | float | 消亡阈值 |

**内部类型 `AlphaLifecycle`**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `family_id` | int | 策略家族标识（祖源 id） |
| `birth_step` | int | t_0（首次出现） |
| `alpha_series` | list[float] | α_k(t) 时间序列 |
| `crowding_series` | list[float] | C_k(t) 时间序列 |
| `t_emerge` | int \| None | 阶段 I→II 转折 |
| `t_peak` | int \| None | 阶段 II→III 转折 |
| `t_half` | int \| None | Alpha 半衰期 |
| `t_extinct` | int \| None | 阶段 IV→V 转折 |
| `current_phase` | str | {"exploration", "burst", "crowding", "decay", "extinct", "recovery"} |
| `is_alive` | bool | 是否仍有活跃 agent |
| `peak_alpha` | float | α_k(t_peak) 值 |

**方法**：

| 方法 | 签名 | 职责 |
|------|------|------|
| `update` | `(step, family_returns, family_wealth, total_wealth) -> None` | 追加一步数据到各家族 |
| `detect_phases` | `(family_id) -> None` | 扫描 alpha_series 检测五阶段转折点 |
| `get_halflife` | `(family_id) -> float \| None` | 返回 t_half − t_peak |
| `get_active_families` | `() -> list[int]` | 返回当前活跃的家族 id 列表 |
| `get_lifecycle_summary` | `() -> pd.DataFrame` | 返回所有家族的生命周期摘要表 |

---

## 5. 数据流图（单步）

```
                    ┌──────────────┐
                    │ EVOASMModel  │
                    │   .step()    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ Stage 1    │ │ Stage 2    │ │ Stage 3    │
     │ perceive() │ │ decide()   │ │ act()      │
     └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
           │              │              │
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │SignalComp. │ │ Strategy   │ │ Portfolio  │
    │→ s_i(t)    │ │ → D_i(t)   │ │ Update     │
    └────────────┘ └─────┬──────┘ └─────┬──────┘
                         │              │
                         ▼              │
                  ┌────────────┐        │
                  │  Market    │        │
                  │  .clear()  │        │
                  │ → P(t)     │────────┘
                  └─────┬──────┘
                        │
                        ▼
                 ┌──────────────┐
                 │MetricsCollect│
                 │ .record()    │
                 └──────┬───────┘
                        │
                   t % K == 0 ?
                    │ yes
                    ▼
             ┌──────────────┐
             │EvolutionEng. │
             │ .evolve()    │
             └──────────────┘
```

---

## 6. 关键设计决策

### 6.1 Scheduler 选择：`StagedActivation`

**选择理由**：
- 每个 agent 必须在观察同一市场状态后独立决策（Stage 1 + Stage 2）
- 所有决策提交完毕后，市场一次性出清
- 出清后所有 agent 同时更新持仓和财富（Stage 3）
- `StagedActivation` 天然支持此三阶段流水线，避免 agent 执行顺序偏差

**Stage 定义**：
```python
stage_names = ["perceive", "decide", "act"]
```

### 6.2 Agent-Market 通信：需求缓冲区模式

**问题**：agent 在 decide() 中产生净需求，但市场要在所有 agent 决策完毕后才聚合。

**方案**：`WalrasianMarket` 维护一个 `_demand_buffer: np.ndarray[M, N]`。Agent 在 decide() 中写入 `self.model.market._demand_buffer[self.unique_id, :]`。`clear()` 时读取 buffer 并聚合。

**替代方案（订单簿模式）**：agent 在 decide() 中调用 `self.model.market.books[n].submit(order)`，订单簿即时撮合并记录。

### 6.3 演化引擎的 Agent 生命周期管理

**问题**：Mesa 的 agent 通过 `model.schedule` 管理。淘汰时需从 scheduler 移除 agent。

**方案**：
- `EvolutionEngine.evolve()` 直接操作 `model.schedule.agents`（移除淘汰者）
- 新后代通过 `model.schedule.add(offspring_agent)` 注册
- 使用 `model.schedule.steps = 0` 重置 agent 的内部状态（如需）

### 6.4 策略家族的祖源追踪

**问题**：如何定义"策略家族 k"以进行 Alpha 追踪。

**方案**：每个 agent 携带 `ancestor_id`：
- 初始 agent：`ancestor_id = unique_id`（每个初始 agent 是独立家族根）
- 复制产生的后代：`ancestor_id = parent.ancestor_id`
- 这样，同一祖源的所有 agent 构成一个策略家族（共享演化谱系）
- 若有需要，可额外按 ancestor(Ğ) 回溯到更浅的层面进行粗粒度聚类

### 6.5 状态可变性与 Mesa Datacollector

**设计**：
- `EVOASMConfig` 为 frozen dataclass（不可变）
- `Strategy` 为可变 dataclass（突变直接修改字段）
- agent 的 wealth/holdings/cash 为普通属性（每步更新）
- `MetricsCollector` 是主要的时序数据存储，`Mesa DataCollector` 作为辅助（用于 Mesa 内置图表）
- 两者独立运行，`MetricsCollector` 负责全部自定义指标，`DataCollector` 仅用于快速可视化

---

## 7. 扩展点

| 扩展点 | 位置 | 方案 |
|--------|------|------|
| 新增资产类型 | `market/asset.py` | 扩展 Asset dataclass 字段（如股息率） |
| 新增信号类型 | `signals/signal_computer.py` | 增加 compute_* 方法，更新 D 维度 |
| 替换市场微观结构 | `market/base_market.py` | 新增 BaseMarket 子类（如 HybridMarket） |
| 替换学习机制 | `agents/trading_agent.py` | 重写 perceive/decide 方法，或新增 LearningAgent 子类 |
| 替换选择算子 | `evolution/evolution_engine.py` | 新增 `_select_parents_tournament()` 等方法 |
| 新增度量指标 | `metrics/metrics_collector.py` | 在 record_step() 中追加计算，在 data dict 中新增 key |
| 并行 BatchRunner | `run.py` | Mesa 原生 `batch_run()` 支持多核并行参数扫描 |

---

*END OF ARCHITECTURE.md*
