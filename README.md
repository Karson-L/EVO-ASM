# EVO-ASM: 演化人工股票市场

> 基于演化 Agent-Based Modeling 的量化交易策略生态系统与 Alpha 消失机制研究

[![tests](https://img.shields.io/badge/tests-127%2F127%20passed-brightgreen)]()
[![python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![mesa](https://img.shields.io/badge/mesa-%E2%89%A52.x-orange)]()

---

## 核心研究问题

**市场中的 Alpha（超额收益）是否会因为策略竞争而自发消失？如果是，通过什么机制？在什么条件下？**

## 项目结构

```
毕设/
├── README.md                     # ← 你在这里
├── .gitignore
│
├── docs/                         # 全部文档（开发前必读）
│   ├── PROJECT_CONTEXT.md        #   项目上下文入口 ★
│   ├── REASEARCH_PLAN.md         #   研究设计方案
│   ├── MODEL_SPEC.md             #   数学模型规格
│   ├── ARCHITECTURE.md           #   Mesa 软件架构
│   ├── EXPERIMENTS.md            #   实验设计
│   └── PLOT_SPEC.md              #   图表输出规格
│
├── evo_asm/                      # 源代码
│   ├── config.py                 #   全局参数
│   ├── model.py                  #   EVOASMModel（顶层协调）
│   ├── agents/                   #   Strategy / TradingAgent / MomentumAgent
│   ├── market/                   #   WalrasianMarket / OrderBook / Asset
│   ├── evolution/                #   EvolutionEngine
│   ├── signals/                  #   SignalComputer
│   └── utils/                    #   数学工具
│
├── tests/                        # 单元测试（127 个）
│   ├── test_market.py
│   ├── test_agents.py
│   └── test_evolution.py
│
├── scripts/                      # 运行和绘图脚本
│   ├── run_experiment.py         #   实验运行器（待实现）
│   └── plots/
│       ├── plot_config.py        #   全局绘图配置
│       ├── e1/                   #   E1 无演化基线（8 图）
│       ├── e2/                   #   E2 资本扩张（8 图）
│       ├── e3/                   #   E3 复制机制（8 图）
│       ├── e4/                   #   E4 完整演化（12 图）
│       └── cross/                #   跨实验对比（5 图）
│
├── results/                      # 实验输出（数据 + 图表）
│   ├── e1_no_evolution/
│   ├── e2_capital_expansion/
│   ├── e3_replication/
│   └── e4_full_evolution/
│
├── paper/                        # 毕业论文（基于 JLUThesis LaTeX 模板）
│   ├── thesis/                   #   LaTeX 论文工程（在这里写论文、编译）
│   │   ├── main.tex              #     主文档
│   │   ├── jluthesis.cls         #     JLU 论文文档类
│   │   ├── jluthesis.cfg         #     论文格式配置
│   │   ├── reference.bib         #     参考文献库
│   │   ├── data/                 #     各章节 tex 文件
│   │   └── figures/              #     论文插图（含校徽）
│   ├── drafts/                   #   草稿 / 写作笔记
│   └── figures/                  #   从 results/ 筛选的最终图表
│
└── data/                         # 外部数据
    └── literature/               #   文献检索结果
```

## 快速开始

```bash
# 安装依赖
pip install mesa numpy pandas matplotlib pytest

# 运行全部测试
pytest tests/ -v

# 阅读文档（按顺序）
# 1. docs/PROJECT_CONTEXT.md
# 2. docs/REASEARCH_PLAN.md
# 3. docs/MODEL_SPEC.md
```

## 实现状态

| 模块 | 状态 | 测试 |
|------|------|------|
| Market (Walrasian + OrderBook) | ✅ 完成 | 44 |
| Agent (Strategy + Trading + Momentum) | ✅ 完成 | 42 |
| Evolution Engine | ✅ 完成 | 41 |
| EVOASMModel (Mesa 集成) | ⚠️ 存根 | — |
| MetricsCollector + AlphaTracker | ❌ 待实现 | — |
| Experiment Runner | ❌ 待实现 | — |
| Plot Scripts (41 scripts) | ❌ 待实现 | — |

**总计：127 测试全部通过。**

## 工作原则

1. 研究目标优先于软件工程目标
2. 所有代码必须对应 `MODEL_SPEC.md` 中的数学定义
3. 禁止与论文无关的功能
4. 开发前阅读 `docs/` 中的文档
5. 每完成一个模块：测试 → 更新文档 → 标注实验影响

详见 `docs/PROJECT_CONTEXT.md`。
