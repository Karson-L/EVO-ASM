"""演化引擎模块。

每 K 步执行一次达尔文式演化循环：
计算适应度 → 淘汰 → 轮盘赌选择 → 复制 → 突变。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from ..agents.strategy import Strategy
from ..agents.trading_agent import TradingAgent

if TYPE_CHECKING:
    from ..config import EVOASMConfig


# ═══════════════════════════════════════════════════════════════════
# EvolutionReport
# ═══════════════════════════════════════════════════════════════════

@dataclass
class EvolutionReport:
    """单次演化循环的摘要报告。

    Attributes
    ----------
    generation : int
        演化代数 G。
    n_before : int
        演化前 agent 总数。
    n_eliminated : int
        淘汰的 agent 数。
    n_survivors : int
        留存 agent 数。
    n_new : int
        新生成的 agent 数。
    n_after : int
        演化后 agent 总数。
    mean_fitness_before : float
        淘汰前平均适应度。
    mean_fitness_after : float
        复制+突变后平均适应度（以父代适应度近似）。
    best_fitness : float
        最优适应度。
    strategy_entropy_before : float
        淘汰前策略熵。
    mutation_count : int
        发生突变的基因位总数。
    eliminated_ids : list[int]
        被淘汰 agent 的 id 列表。
    """

    generation: int = 0
    n_before: int = 0
    n_eliminated: int = 0
    n_survivors: int = 0
    n_new: int = 0
    n_after: int = 0
    mean_fitness_before: float = 0.0
    mean_fitness_after: float = 0.0
    best_fitness: float = float("-inf")
    strategy_entropy_before: float = 0.0
    mutation_count: int = 0
    eliminated_ids: list[int] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# EvolutionEngine
# ═══════════════════════════════════════════════════════════════════

class EvolutionEngine:
    """达尔文式演化引擎。

    实现淘汰 → 选择 → 复制 → 突变的完整演化循环。
    每 K 个市场步调用一次 evolve()。

    Attributes
    ----------
    config : EVOASMConfig
        模型配置（演化相关参数）。
    rng : np.random.Generator
        随机数生成器。
    generation : int
        当前演化代数 G。
    history : list[EvolutionReport]
        每代演化报告的历史记录。
    """

    def __init__(
        self,
        config: "EVOASMConfig",
        rng: np.random.Generator | None = None,
    ) -> None:
        """初始化演化引擎。

        Parameters
        ----------
        config : EVOASMConfig
            模型配置。
        rng : np.random.Generator | None
            随机数生成器。
        """
        self.config: "EVOASMConfig" = config
        self.rng: np.random.Generator = (
            rng if rng is not None
            else np.random.default_rng(config.seed)
        )
        self.generation: int = 0
        self.history: list[EvolutionReport] = []

    # ── 主入口 ──

    def evolve(
        self,
        agents: list[TradingAgent],
        *,
        prices: np.ndarray | None = None,
        N: int = 1,
        generation_window: int | None = None,
    ) -> EvolutionReport:
        """执行一次完整演化循环。

        Parameters
        ----------
        agents : list[TradingAgent]
            当前所有 agent（将被原地修改：淘汰 + 新增后代）。
        prices : np.ndarray | None
            shape=(N,)，当前价格向量，用于计算 agent 财富。
        N : int
            资产数量（用于新 agent 初始化）。
        generation_window : int | None
            适应度评估窗口。若为 None，则使用全部 return_history。

        Returns
        -------
        EvolutionReport
            本次演化的摘要报告。
        """
        n_before = len(agents)
        report = EvolutionReport(
            generation=self.generation,
            n_before=n_before,
        )

        # 1. 计算适应度
        if prices is not None:
            for a in agents:
                a.compute_wealth(prices)
        fitness = self._compute_fitness(agents, window=generation_window)
        report.mean_fitness_before = float(np.mean(fitness)) if len(fitness) > 0 else 0.0
        report.best_fitness = float(np.max(fitness)) if len(fitness) > 0 else float("-inf")

        # 策略熵
        report.strategy_entropy_before = self._compute_strategy_entropy(agents)

        # 2. 淘汰
        survivors, eliminated = self._eliminate(agents, fitness)
        report.n_eliminated = len(eliminated)
        report.n_survivors = len(survivors)
        report.eliminated_ids = [a.agent_id for a in eliminated]

        # 3. 选择父代
        n_offspring = len(eliminated)  # 补齐到淘汰前数量
        parents = self._select_parents(survivors, fitness[:len(survivors)],
                                       n_offspring)
        report.n_new = len(parents)

        # 4. 复制 + 5. 突变
        offspring = []
        total_mutations = 0
        for parent in parents:
            child = self._replicate(parent, N=N)
            mut_count = self._mutate(child)
            total_mutations += mut_count
            offspring.append(child)
        report.mutation_count = total_mutations

        # 用父代适应度近似后适应度
        parent_fitness = [
            fitness[agents.index(p)] for p in parents
            if p in agents[:len(survivors)]
        ]
        if parent_fitness:
            report.mean_fitness_after = float(np.mean(parent_fitness))
        else:
            report.mean_fitness_after = 0.0

        # 替换 agent 列表
        agents.clear()
        agents.extend(survivors)
        agents.extend(offspring)
        report.n_after = len(agents)

        # 记录
        self.history.append(report)
        self.generation += 1

        return report

    # ── 适应度 ──

    def _compute_fitness(
        self,
        agents: list[TradingAgent],
        window: int | None = None,
    ) -> np.ndarray:
        """计算所有 agent 的适应度（窗口夏普比率）。

        Parameters
        ----------
        agents : list[TradingAgent]
            agent 列表。
        window : int | None
            窗口长度。若为 None，则使用全部历史。

        Returns
        -------
        np.ndarray
            shape=(M,)，适应度值 F_i。
        """
        fitness = np.zeros(len(agents), dtype=np.float64)
        for idx, agent in enumerate(agents):
            returns = agent.return_history
            if window is not None and len(returns) > window:
                returns = returns[-window:]
            fitness[idx] = self._sharpe(returns)
        return fitness

    def _sharpe(self, returns: list[float]) -> float:
        """计算夏普比率。

        Parameters
        ----------
        returns : list[float]
            收益率序列。

        Returns
        -------
        float
            (μ − r_f) / σ。若 σ=0 或序列为空，返回 0。
        """
        if len(returns) < 2:
            return 0.0
        arr = np.array(returns, dtype=np.float64)
        mu = np.mean(arr)
        sigma = np.std(arr, ddof=1)
        if sigma == 0:
            return 0.0
        return float((mu - self.config.r_f) / sigma)

    # ── 淘汰 ──

    def _eliminate(
        self,
        agents: list[TradingAgent],
        fitness: np.ndarray,
    ) -> tuple[list[TradingAgent], list[TradingAgent]]:
        """按适应度淘汰末尾 P_eliminate 比例的 agent。

        Parameters
        ----------
        agents : list[TradingAgent]
            原 agent 列表。
        fitness : np.ndarray
            shape=(M,)，适应度数组。

        Returns
        -------
        tuple[list[TradingAgent], list[TradingAgent]]
            (survivors, eliminated)。
        """
        n_elim = max(1, int(len(agents) * self.config.P_eliminate))
        if n_elim >= len(agents):
            n_elim = max(1, len(agents) // 2)

        # 按适应度升序排列索引
        order = np.argsort(fitness)
        eliminated_indices = set(order[:n_elim].tolist())

        survivors = [a for i, a in enumerate(agents) if i not in eliminated_indices]
        eliminated = [a for i, a in enumerate(agents) if i in eliminated_indices]
        return survivors, eliminated

    # ── 选择 ──

    def _select_parents(
        self,
        survivors: list[TradingAgent],
        fitness: np.ndarray,
        n_offspring: int,
    ) -> list[TradingAgent]:
        """轮盘赌选择（roulette-wheel selection）。

        P_select(i) ∝ exp(λ_select · F_i)

        Parameters
        ----------
        survivors : list[TradingAgent]
            存活的 agent。
        fitness : np.ndarray
            shape=(|survivors|,)，适应度数组。
        n_offspring : int
            需要产生的后代数量。

        Returns
        -------
        list[TradingAgent]
            选中的父代列表（可重复）。
        """
        if len(survivors) == 0 or n_offspring == 0:
            return []

        lam = self.config.lambda_select

        # 防止数值溢出：减去 max
        f_max = np.max(fitness)
        weights = np.exp(lam * (fitness - f_max))
        total = np.sum(weights)

        if total == 0 or np.isnan(total):
            # 退化为均匀选择
            probs = np.ones(len(survivors)) / len(survivors)
        else:
            probs = weights / total

        chosen_indices = self.rng.choice(
            len(survivors), size=n_offspring, replace=True, p=probs,
        )
        return [survivors[int(i)] for i in chosen_indices]

    # ── 复制 ──

    def _replicate(
        self,
        parent: TradingAgent,
        N: int = 1,
    ) -> TradingAgent:
        """从父代复制一个后代 agent。

        后代继承策略，重置财富和年龄。

        Parameters
        ----------
        parent : TradingAgent
            父代 agent。
        N : int
            资产数量。

        Returns
        -------
        TradingAgent
            新创建的后代。
        """
        # 每个后代获得均等的初始财富
        # 使用 "新生财富池" 概念：W_0 在外部调用时按比例分配
        initial_cash = parent.cash  # 实际财富由 model 统一分配

        child = TradingAgent(
            strategy=parent.strategy.clone(),
            cash=initial_cash,
            N=N,
            parent_id=parent.agent_id,
            ancestor_id=parent.ancestor_id,
        )
        return child

    # ── 突变 ──

    def _mutate(self, agent: TradingAgent) -> int:
        """对 agent 策略施加随机突变。

        五维独立突变：weights、threshold、holding_period、risk_appetite。

        Parameters
        ----------
        agent : TradingAgent
            目标 agent。

        Returns
        -------
        int
            实际发生突变的基因位数量。
        """
        cfg = self.config
        s = agent.strategy
        mut_count = 0

        # 权重突变
        if self.rng.random() < cfg.p_mut:
            s.mutate_weights(sigma=cfg.sigma_mut, rng=self.rng)
            mut_count += 1

        # 阈值突变
        if self.rng.random() < cfg.p_mut:
            s.mutate_threshold(
                sigma=cfg.sigma_theta,
                theta_min=cfg.theta_min,
                theta_max=cfg.theta_max,
                rng=self.rng,
            )
            mut_count += 1

        # 持仓周期突变
        if self.rng.random() < cfg.p_mut:
            s.mutate_holding_period(
                p_up=cfg.p_tau_up,
                p_down=cfg.p_tau_down,
                holding_periods=cfg.holding_periods,
                rng=self.rng,
            )
            mut_count += 1

        # 风险偏好突变
        if self.rng.random() < cfg.p_mut:
            s.mutate_risk_appetite(sigma=cfg.sigma_alpha, rng=self.rng)
            mut_count += 1

        return mut_count

    # ── 辅助 ──

    @staticmethod
    def _compute_strategy_entropy(agents: list[TradingAgent]) -> float:
        """计算策略多样性香农熵。

        H = −Σ_k p_k · ln(p_k)，p_k 为策略家族 k 的 agent 占比。

        Parameters
        ----------
        agents : list[TradingAgent]
            agent 列表。

        Returns
        -------
        float
            H ∈ [0, ∞)。
        """
        if len(agents) == 0:
            return 0.0

        family_counts: dict[int, int] = {}
        for a in agents:
            anc = a.ancestor_id if a.ancestor_id is not None else a.agent_id
            family_counts[anc] = family_counts.get(anc, 0) + 1

        total = len(agents)
        entropy = 0.0
        for count in family_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log(p)
        return float(entropy)

    def reset(self) -> None:
        """重置演化引擎状态。"""
        self.generation = 0
        self.history.clear()
