# PROJECT_CONTEXT.md — EVO-ASM 项目上下文

> 本文档是项目开发的唯一权威上下文入口。
> 每次开发前必须阅读。不得跳过。

---

## 一、项目目标

构建一个**演化 Agent-Based 人工金融市场**（EVO-ASM），用于回答一个核心研究问题：

> **市场中的 Alpha（超额收益）是否会因为策略竞争而自发消失？如果是，通过什么机制？在什么条件下？**

该问题是中文学位论文《基于演化 Agent-Based Modeling 的量化交易策略生态系统与 Alpha 消失机制研究》的实证核心。

### 项目的"是"与"不是"

**本项目是**：
- 一个学术研究工具，服务于论文的实验验证
- 一个可复现的 ABM 金融市场模拟器
- 一个用于探索策略协同演化与 Alpha 衰减机制的实验平台

**本项目不是**：
- 一个生产级量化交易系统
- 一个通用 ABM 框架
- 一个高频交易回测引擎
- 一个 Web 应用或 GUI 工具

---

## 二、核心研究问题与假说

### 核心问题

> 在异质 agent 自适应竞争的市场环境中，策略多样性、市场效率与 Alpha 消失之间存在怎样的演化动力学关系？

### 五个假说

| 假说 | 内容 | 检验实验 |
|------|------|----------|
| H1 | 策略充分多样化+持续学习 → 弱有效市场涌现（亚稳态） | E1, E4 |
| H2 | Alpha 生命周期：发现→拥挤→衰减，半衰期受生态位调节 | E2, E4 |
| H3 | 策略多样性-市场稳定性呈倒U型 | E3, E4 |
| H4 | 中等复杂度策略长期存活最优 | E4 |
| H5 | 制度冲击系统性改变策略生态 | E4a |

### 实验逻辑链

```
E1（无演化基线）
  → E2（+资本扩张 = 拥挤效应）
    → E3（+复制 = 拥挤+同质化）
      → E4（+突变 = 完整演化 = 拥挤+同质化+创新）
        → E4a（+制度冲击）
```

---

## 三、项目文档索引

**每次开发前按顺序阅读以下文档**：

| 序号 | 文档 | 角色 | 何时阅读 |
|------|------|------|----------|
| 1 | `docs/REASEARCH_PLAN.md` | 研究设计：文献综述、研究问题、假说、创新点 | 任何设计决策前 |
| 2 | `docs/MODEL_SPEC.md` | 数学模型：所有变量、方程、算法定义 | 实现任何模块前 |
| 3 | `docs/ARCHITECTURE.md` | 软件架构：Mesa 集成、目录结构、类接口 | 写代码前 |
| 4 | `docs/EXPERIMENTS.md` | 实验设计：自变量/因变量/图表/统计 | 设计实验前 |
| 5 | `docs/PLOT_SPEC.md` | 图表规格：CSV 结构、matplotlib 脚本、论文图题 | 生成图表前 |
| 6 | `PROJECT_CONTEXT.md` | 本文档：项目全局上下文 | 每次开始工作时 |

### 文档依赖关系

```
PROJECT_CONTEXT.md  ← 你在这里（入口）
       │
       ├── docs/REASEARCH_PLAN.md   ← 为什么做
       │       │
       │       └── docs/MODEL_SPEC.md   ← 做什么（数学定义）
       │               │
       │               └── docs/ARCHITECTURE.md  ← 怎么做（类设计）
       │
       ├── docs/EXPERIMENTS.md       ← 跑什么实验
       │
       └── docs/PLOT_SPEC.md         ← 出什么图
```

---

## 四、当前实现状态

### 已完成模块

| 模块 | 文件 | 测试 | 状态 |
|------|------|------|------|
| `config` | `evo_asm/config.py` | — | ✅ 完成 |
| `model` | `evo_asm/model.py` | — | ⚠️ 存根（待完整实现） |
| `market/asset` | `evo_asm/market/asset.py` | 4 tests | ✅ 完成 |
| `market/base_market` | `evo_asm/market/base_market.py` | — | ✅ 完成 |
| `market/walrasian_market` | `evo_asm/market/walrasian_market.py` | 15 tests | ✅ 完成 |
| `market/order_book` | `evo_asm/market/order_book.py` | 20 tests | ✅ 完成 |
| `market/order_book_market` | `evo_asm/market/order_book_market.py` | 8 tests | ✅ 完成 |
| `agents/strategy` | `evo_asm/agents/strategy.py` | 16 tests | ✅ 完成 |
| `agents/trading_agent` | `evo_asm/agents/trading_agent.py` | 12 tests | ✅ 完成 |
| `agents/momentum_agent` | `evo_asm/agents/momentum_agent.py` | 14 tests | ✅ 完成 |
| `signals/signal_computer` | `evo_asm/signals/signal_computer.py` | — | ✅ 完成 |
| `evolution/evolution_engine` | `evo_asm/evolution/evolution_engine.py` | 41 tests | ✅ 完成 |

**测试总计**：127 个单元测试，全部通过（零失败、零警告）。

### 待实现模块（按优先级）

| 优先级 | 模块 | 对应 docs/ARCHITECTURE.md | 说明 |
|--------|------|---------------------|------|
| P0 | `EVOASMModel` 完整实现 | §4.2 | Mesa 集成，step() 循环 |
| P0 | `MetricsCollector` | §4.12 | 全部度量采集 |
| P0 | `AlphaTracker` | §4.13 | Alpha 生命周期追踪 |
| P1 | `ExperimentRunner` | — | 批量实验管理、参数扫描、CSV 输出 |
| P1 | `scripts/plots/*` | docs/PLOT_SPEC.md | 41 个 matplotlib 脚本 |
| P2 | `MeanReversionAgent` | — | 与 MomentumAgent 对称的均值回复型 agent |
| P2 | `ValueAgent` | — | 基本面价值型 agent |
| P3 | `HybridAgent` | — | 混合信号型 agent |

---

## 五、工作原则

### 原则 1：研究目标优先于软件工程目标

- 代码的存在意义是回答研究问题。不追求覆盖率 100%、不追求完美抽象。
- 允许为特定实验硬编码参数——前提是这些参数被记录在 `summary.json` 中。
- 可复现性比可扩展性更重要。每次运行必须可精确复现（固定 seed + 保存全部参数）。

### 原则 2：所有代码必须对应论文中的模型

- 每个类、每个方法、每个参数必须在 `docs/MODEL_SPEC.md` 中有对应定义。
- 若发现代码需要偏离模型规格，必须先更新 `docs/MODEL_SPEC.md`，再更新代码。
- 禁止"实现先行、文档追补"——文档是真理源（source of truth）。

### 原则 3：禁止与论文无关的功能

**明确不允许**：
- 实时交易接口、API 集成
- GUI / Web 仪表板
- 多线程/分布式优化
- 数据库持久化（CSV 文件足以）
- 任何形式的"生产部署"准备
- 策略参数自动调优（AutoML / hyperopt）
- 增加新的信号类型（除非论文需要）
- 增加新的资产类别（除非论文需要）

### 原则 4：开发前置阅读

每次开始编码工作前：

```
1. 阅读 PROJECT_CONTEXT.md（本文档）— 确认当前状态和待办优先级
2. 阅读 docs/REASEARCH_PLAN.md 相关章节 — 确认研究动机
3. 阅读 docs/MODEL_SPEC.md 相关章节 — 确认数学定义
4. 阅读 docs/ARCHITECTURE.md 相关章节 — 确认类接口
```

### 原则 5：每个模块完成后必须执行

```
1. 编写单元测试（tests/ 目录）
2. 运行全部回归测试（pytest tests/ — 必须 100% 通过）
3. 更新 PROJECT_CONTEXT.md 的"当前实现状态"表
4. 若 API 变化，更新 docs/ARCHITECTURE.md 的类规格
5. 若模型变化，更新 docs/MODEL_SPEC.md
6. 在 commit message 中标注影响的实验（如 "影响: E2, E3, E4"）
```

---

## 六、设计问题处理流程

### 发现设计问题时

**禁止直接修改代码以"绕过"设计问题。**

按以下流程处理：

```
1. 在 PROJECT_CONTEXT.md 底部"问题日志"中记录问题
2. 提出设计建议（Design Proposal），包含：
   a. 问题描述：当前设计有什么缺陷？
   b. 影响范围：影响哪些模块？哪些实验？
   c. 可选方案：至少 2 个备选方案
   d. 推荐方案 + 理由
3. 更新相关文档（docs/MODEL_SPEC.md / docs/ARCHITECTURE.md）
4. 待设计建议被确认后，方可修改代码
```

### 设计建议模板

```markdown
### 设计建议 #N

**日期**：YYYY-MM-DD
**状态**：提案 / 已确认 / 已实施 / 已拒绝

**问题描述**：
[具体描述]

**影响范围**：
- 模块：xxx
- 实验：Ex
- 文档：docs/MODEL_SPEC.md §X / docs/ARCHITECTURE.md §Y

**方案 A**：
[描述]

**方案 B**：
[描述]

**推荐方案**：
[方案 X]，理由：[…]
```

---

## 七、技术栈约定

| 层 | 选择 | 版本 |
|---|------|------|
| 语言 | Python | ≥3.11 |
| ABM 框架 | Mesa | ≥2.x |
| 数值计算 | NumPy | ≥1.24 |
| 数据分析 | Pandas | ≥2.0 |
| 可视化 | Matplotlib | ≥3.7 |
| 测试 | pytest | ≥8.0 |
| 类型检查 | mypy（可选） | — |

仅使用上述库。不得引入新的第三方依赖——除非在"设计建议"中论证其必要性。

---

## 八、提交约定

### Commit Message 格式

```
<type>: <简短描述>

影响实验: <E1/E2/E3/E4/none>
```

**类型**：
- `feat`: 新模块/新功能
- `fix`: 修复 bug
- `test`: 添加/修改测试
- `docs`: 文档更新
- `refactor`: 重构（不改变行为）
- `exp`: 实验脚本/参数

**示例**：
```
feat: 实现 MomentumAgent

影响实验: E1, E2, E3, E4
```

### 分支策略

- `main` — 可运行的稳定版本
- 功能分支以模块名命名，如 `feat/metrics-collector`

---

## 九、问题日志

> 记录所有已发现的设计问题及其状态。

（当前无待解决问题。）

---

*最后更新：2026-06-09*
