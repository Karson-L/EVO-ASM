"""EVO-ASM 顶层模型。

协调 Market、EvolutionEngine、SignalComputer 和 Agent 集合。
实现 MODEL_SPEC §10.1 的完整主循环。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .agents.strategy import Strategy
from .agents.trading_agent import TradingAgent
from .config import EVOASMConfig
from .evolution.evolution_engine import EvolutionEngine, EvolutionReport
from .market.walrasian_market import WalrasianMarket
from .metrics.metrics_collector import MetricsCollector
from .signals.signal_computer import SignalComputer


class EVOASMModel:
    """EVO-ASM 顶层模型。

    持有所有子模块引用，实现完整的 step() 主循环：
    基本面更新 → Agent 感知 → 决策 → 市场出清 → 交易执行
    → 财富更新 → 度量记录 → 演化（每 K 步）。

    Attributes
    ----------
    config : EVOASMConfig
    market : WalrasianMarket
    signal_computer : SignalComputer
    evolution_engine : EvolutionEngine
    agents : list[TradingAgent]
    step_count : int
    generation : int
    metrics : dict[str, list]  # backward compat (delegates to metrics_collector)
    evolution_history : list[EvolutionReport]
    """

    def __init__(
        self,
        config: EVOASMConfig | None = None,
        *,
        market_type: str = "walrasian",
    ) -> None:
        """初始化 EVO-ASM 模型。

        Parameters
        ----------
        config : EVOASMConfig | None
        market_type : str
            "walrasian"（默认）。
        """
        self.config: EVOASMConfig = (
            config if config is not None else EVOASMConfig()
        )
        self.rng: np.random.Generator = np.random.default_rng(
            self.config.seed
        )

        # ── 子模块 ──
        self.market: WalrasianMarket = WalrasianMarket(
            self.config, rng=self.rng,
        )
        self.signal_computer: SignalComputer = SignalComputer()
        self.evolution_engine: EvolutionEngine = EvolutionEngine(
            self.config, rng=self.rng,
        )

        # ── Agent ──
        self.agents: list[TradingAgent] = []
        self._create_agents()

        # ── 计数器 ──
        self.step_count: int = 0
        self.generation: int = 0

        # ── 度量存储 ──
        # ?????
        self.metrics_collector: MetricsCollector = MetricsCollector(
            self.config, self,
        )
        self._agent_snapshots: list[dict] = []
        # backward compat
        self.metrics = self.metrics_collector.data
        self._return_buffer: list[float] = []  # 用于滚动 ACF1
        self._evolution_history: list[EvolutionReport] = []

    # ═══════════════════════════════════════════════════════════════
    # Agent 初始化
    # ═══════════════════════════════════════════════════════════════

    def _create_agents(self) -> None:
        """创建 M 个随机策略 agent，均等初始财富。"""
        cfg = self.config
        initial_cash = cfg.W_total / cfg.M
        self.agents.clear()
        for _ in range(cfg.M):
            s = Strategy.random(
                D=cfg.D, rng=self.rng,
                sigma_init=cfg.sigma_init,
                threshold_min=cfg.theta_min,
                threshold_max=cfg.theta_max,
                holding_periods=cfg.holding_periods,
            )
            a = TradingAgent(strategy=s, cash=initial_cash, N=cfg.N)
            self.agents.append(a)

    # ═══════════════════════════════════════════════════════════════
    # 主循环
    # ═══════════════════════════════════════════════════════════════

    def step(self) -> None:
        """执行一个完整的时间步。

        严格遵循 MODEL_SPEC §10.1 的 13 步流水线。
        """
        cfg = self.config

        # ── 1. 更新基础价值 ──
        self.market.update_fundamentals()

        # ── 2. Agent 感知 + 决策 + 提交需求 ──
        M = len(self.agents)
        demands = np.zeros((M, cfg.N), dtype=np.float64)

        for i, agent in enumerate(self.agents):
            # 2a. 感知：计算信号向量
            signals = agent.perceive(self.market, self.signal_computer)

            # 2b. 决策：方向 + 净需求（单资产模式）
            direction, net_demand = agent.decide(signals, self.market, asset_idx=0)
            demands[i, 0] = net_demand

        # ── 3. 市场出清 ──
        self.market.clear(demands)

        # ── 4-5. 执行交易 + 更新持仓 ──
        price = self.market.get_price(0)
        prices_arr = np.array([price], dtype=np.float64)

        for i, agent in enumerate(self.agents):
            qty = float(demands[i, 0])
            if qty != 0.0:
                agent.execute_trade(
                    asset_idx=0, quantity=qty, price=price, config=cfg,
                )

        # ── 6. 记录财富 ──
        for agent in self.agents:
            agent.record_step(prices_arr)

        # ── 7. 记录度量 ──
        self._record_metrics()

        # Periodic agent snapshot (matches families snapshot interval)
        snap_interval = self.metrics_collector._snapshot_interval
        if self.step_count % snap_interval == 0 or self.step_count == self.config.T - 1:
            self._snapshot_agents()

        # ── 8-13. 演化（每 K 步） ──
        self.step_count += 1
        if self.step_count % cfg.K == 0 and self.step_count > 0:
            self._run_evolution()

    # ═══════════════════════════════════════════════════════════════
    # 演化
    # ═══════════════════════════════════════════════════════════════

    def _run_evolution(self) -> None:
        """执行一次完整演化循环。"""
        price = self.market.get_price(0)
        prices_arr = np.array([price], dtype=np.float64)

        report = self.evolution_engine.evolve(
            self.agents,
            prices=prices_arr,
            N=self.config.N,
            generation_window=self.config.K,
        )
        self._evolution_history.append(report)
        self.generation = self.evolution_engine.generation

    # ═══════════════════════════════════════════════════════════════
    # 度量采集（内嵌，未来迁移到 MetricsCollector）
    # ═══════════════════════════════════════════════════════════════

    def _record_metrics(self) -> None:
        """???????????????? MetricsCollector??"""
        self.metrics_collector.record_step()

    def _compute_gini(self) -> float:
        """计算 agent 财富的基尼系数。"""
        w = np.array([a.compute_wealth(self.market.P) for a in self.agents],
                     dtype=np.float64)
        if len(w) < 2 or np.sum(w) == 0:
            return 0.0
        w_sorted = np.sort(w)
        n = len(w_sorted)
        cumsum = np.cumsum(w_sorted)
        return float(
            (2.0 * np.sum((np.arange(1, n + 1) * w_sorted)) - (n + 1.0) * np.sum(w_sorted))
            / (n * np.sum(w_sorted))
        )

    def _compute_acf1(self) -> float:
        """计算滚动窗口一阶自相关系数。"""
        buf = self._return_buffer
        if len(buf) < 3:
            return 0.0
        window = min(len(buf), self.config.delta_alpha)
        r = np.array(buf[-window:], dtype=np.float64)
        r_mean = np.mean(r)
        num = np.sum((r[1:] - r_mean) * (r[:-1] - r_mean))
        den = np.sum((r - r_mean) ** 2)
        if den == 0:
            return 0.0
        return float(num / den)

    # ═══════════════════════════════════════════════════════════════
    # 运行与输出
    # ═══════════════════════════════════════════════════════════════

    def run(self, n_steps: int | None = None) -> pd.DataFrame:
        """运行模型 n_steps 期，返回度量 DataFrame。

        Parameters
        ----------
        n_steps : int | None
            运行步数。若为 None，则使用 config.T。

        Returns
        -------
        pd.DataFrame
            每行一期，列为度量指标。
        """
        total = n_steps if n_steps is not None else self.config.T
        for _ in range(total):
            self.step()
        return self.to_dataframe()

    def to_dataframe(self) -> pd.DataFrame:
        """将当前度量转换为 DataFrame。

        Returns
        -------
        pd.DataFrame
        """
        return pd.DataFrame(self.metrics)

    def save_results(
        self,
        output_dir: str | Path,
        *,
        experiment_name: str = "run",
    ) -> Path:
        """保存运行结果到指定目录。

        输出文件：
        - market.csv  — 度量时序
        - agents.csv  — agent 快照
        - summary.json — 运行摘要

        Parameters
        ----------
        output_dir : str | Path
            输出根目录。
        experiment_name : str
            实验名称（作为子目录名）。

        Returns
        -------
        Path
            输出目录的完整路径。
        """
        out = Path(output_dir) / experiment_name
        out.mkdir(parents=True, exist_ok=True)

        # market.csv
        self.metrics_collector.to_dataframe().to_csv(out / "market.csv", index=False)

        # families.csv (strategy family data — multi-timepoint)
        fam_df = self.metrics_collector.to_families_dataframe()
        if len(fam_df) > 0:
            fam_df.to_csv(out / "families.csv", index=False)

        # agents.csv — all accumulated snapshots, not just final
        self._save_agents_csv(out / "agents.csv")

        # summary.json
        self._save_summary_json(out / "summary.json")

        return out

    def _snapshot_agents(self) -> None:
        rows = []
        for a in self.agents:
            rows.append({
                'step': self.step_count,
                'agent_id': a.agent_id,
                'ancestor_id': a.ancestor_id,
                'parent_id': a.parent_id if a.parent_id is not None else -1,
                'wealth': a.compute_wealth(self.market.P),
                'cash': a.cash,
                'holdings': float(a.holdings[0]),
                'weight_0': float(a.strategy.weights[0]),
                'weight_1': float(a.strategy.weights[1]),
                'weight_2': float(a.strategy.weights[2]),
                'weight_3': float(a.strategy.weights[3]),
                'weight_4': float(a.strategy.weights[4]),
                'weight_5': float(a.strategy.weights[5]),
                'threshold': a.strategy.threshold,
                'holding_period': a.strategy.holding_period,
                'risk_appetite': a.strategy.risk_appetite,
                'age': a.age,
            })
        self._agent_snapshots.append(rows)

    def _save_agents_csv(self, path: Path) -> None:
        all_rows = []
        if self._agent_snapshots:
            for snap in self._agent_snapshots:
                all_rows.extend(snap)
        else:
            for a in self.agents:
                all_rows.append({
                    "step": self.step_count,
                    "agent_id": a.agent_id,
                    "ancestor_id": a.ancestor_id,
                    "parent_id": a.parent_id if a.parent_id is not None else -1,
                    "wealth": a.compute_wealth(self.market.P),
                    "cash": a.cash,
                    "holdings": float(a.holdings[0]),
                    "weight_0": float(a.strategy.weights[0]),
                    "weight_1": float(a.strategy.weights[1]),
                    "weight_2": float(a.strategy.weights[2]),
                    "weight_3": float(a.strategy.weights[3]),
                    "weight_4": float(a.strategy.weights[4]),
                    "weight_5": float(a.strategy.weights[5]),
                    "threshold": a.strategy.threshold,
                    "holding_period": a.strategy.holding_period,
                    "risk_appetite": a.strategy.risk_appetite,
                    "age": a.age,
                })
        pd.DataFrame(all_rows).to_csv(path, index=False)

    def _save_summary_json(self, path: Path) -> None:
        """保存运行摘要 JSON。"""
        df = self.to_dataframe()
        if len(df) == 0:
            return

        returns = df["log_return"].values
        returns_valid = returns[~np.isnan(returns) & ~np.isinf(returns)]

        summary: dict[str, Any] = {
            "experiment": "run",
            "parameters": {
                k: v for k, v in self.config.to_dict().items()
                if not k.startswith("_")
            },
            "statistics": {
                "steps_completed": int(self.step_count),
                "generations_completed": int(self.generation),
                "final_price": float(df["price"].iloc[-1]),
                "mean_return": float(np.mean(returns_valid)) if len(returns_valid) > 0 else 0.0,
                "return_std": float(np.std(returns_valid, ddof=1)) if len(returns_valid) > 1 else 0.0,
                "final_entropy": float(df["strategy_entropy"].iloc[-1]),
                "final_gini": float(df["wealth_gini"].iloc[-1]),
                "final_n_families": int(df["n_families"].iloc[-1]),
            },
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    # ═══════════════════════════════════════════════════════════════
    # 属性
    # ═══════════════════════════════════════════════════════════════

    @property
    def evolution_history(self) -> list[EvolutionReport]:
        """返回演化报告历史。"""
        return self._evolution_history
