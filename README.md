# EVO-ASM：演化人工股票市场

> 基于演化 Agent-Based Modeling 的量化交易策略生态系统与 Alpha 消失机制研究  
> 吉林大学 2026 届本科毕业论文

[![tests](https://img.shields.io/badge/tests-155%20passed-brightgreen)]()
[![python](https://img.shields.io/badge/python-3.11+-blue)]()
[![pdf](https://img.shields.io/badge/PDF-61%E9%A1%B5-orange)]()

---

## 核心研究问题

**市场中的 Alpha（超额收益）是否会因为策略竞争而自发消失？如果是，通过什么机制？在什么条件下？**

四组递进实验从静态基线到完整达尔文演化，逐步剥离 Alpha 衰减的因果机制。关键发现：策略模仿是同质化的主要驱动力（贡献约 45% 方差），突变创新是对抗衰减的核心力量，策略生态系统在参数空间中存在临界相变。

---

## 项目结构

```
├── README.md
├── .gitignore
├── pytest.ini
│
├── docs/                         # 设计文档
│   ├── PROJECT_CONTEXT.md        #   项目目标与工作原则
│   ├── REASEARCH_PLAN.md         #   研究方案与文献综述
│   ├── MODEL_SPEC.md             #   数学模型规格（数学符号）
│   ├── ARCHITECTURE.md           #   软件架构设计
│   ├── EXPERIMENTS.md            #   实验设计方案
│   └── PLOT_SPEC.md              #   图表输出规格
│
├── evo_asm/                      # 核心代码
│   ├── config.py                 #   全局参数配置
│   ├── model.py                  #   EVOASMModel（Mesa 顶层）
│   ├── agents/                   #   Strategy / TradingAgent / MomentumAgent
│   ├── market/                   #   Market / OrderBook / Asset
│   ├── evolution/                #   EvolutionEngine
│   ├── metrics/                  #   MetricsCollector / AlphaTracker
│   └── signals/                  #   SignalComputer
│
├── tests/                        # 单元测试（155 个）
│
├── results/                      # 实验输出
│   ├── e1_no_evolution/          #   E1 无演化基线（370 PNGs）
│   ├── e2_capital_expansion/     #   E2 资本扩张（1,080 PNGs）
│   ├── e3_replication/           #   E3 复制机制（720 PNGs）
│   ├── e4_full_evolution/        #   E4 完整演化（2,880 PNGs）
│   └── cross_experiment/         #   跨实验对比（5 PNGs）
│
└── paper/                        # 毕业论文
    └── thesis/
        ├── main.tex              #   主文件
        ├── jluthesis.cfg         #   吉林大学模板配置
        ├── data/                 #   章节文件（chap01-04）
        └── main.pdf              #   61 页终稿
```

## 快速开始

```bash
# 安装依赖
pip install mesa numpy pandas matplotlib pytest scipy

# 运行全部测试
pytest tests/ -v

# 编译论文（需 xelatex + SimSun 字体）
cd paper/thesis
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

## 阅读顺序

1. `docs/PROJECT_CONTEXT.md` — 项目目标
2. `docs/MODEL_SPEC.md` — 数学模型
3. `docs/ARCHITECTURE.md` — 代码架构
4. `docs/EXPERIMENTS.md` — 实验设计
5. `docs/PLOT_SPEC.md` — 图表规格
6. `paper/thesis/main.pdf` — 完整论文

## 实现状态

| 模块 | 测试数 | 状态 |
|------|--------|------|
| Market（Walrasian + OrderBook） | 44 | ✅ |
| Agent（Strategy + Trading + Momentum） | 42 | ✅ |
| Evolution Engine | 41 | ✅ |
| EVOASMModel（Mesa 集成） | 28 | ✅ |
| Metrics / AlphaTracker | 集成测试 | ✅ |
| 全部 4 组实验 | 512 次运行 | ✅ |
| 论文（61 页 LaTeX） | 零编译错误 | ✅ |

**155 测试全部通过。**

## 实验摘要

| 实验 | 演化机制 | 图数 | 核心发现 |
|------|----------|------|----------|
| E1 | 无 | 370 | Alpha 不衰减；演化是必要条件 |
| E2 | 资本扩张 | 1,080 | 拥挤单独驱动 Alpha 衰减 |
| E3 | +复制 | 720 | 复制加速衰减 2.5×；效率悖论 |
| E4 | +突变 | 2,880 | Alpha 生命周期；相变；最优突变率 |

## 工作原则

1. 研究目标优先于软件工程目标
2. 所有代码对应 `MODEL_SPEC.md` 数学定义
3. 禁止与论文无关的功能
4. 开发前阅读 `docs/`；完成后测试 → 文档 → 实验影响
