"""交易者 Agent 基类。

实现 MODEL_SPEC §3 的行为规则通用框架：
感知 → 信号计算 → 方向判断 → 目标持仓 → 下单 → 财富更新。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .strategy import Strategy

if TYPE_CHECKING:
    from ..config import EVOASMConfig
    from ..market.base_market import BaseMarket
    from ..signals.signal_computer import SignalComputer


class TradingAgent:
    """交易者 Agent 基类。

    Attributes
    ----------
    agent_id : int
        唯一标识（对应 Mesa unique_id）。
    strategy : Strategy
        当前策略编码 π_i。
    cash : float
        现金余额 C_i。
    holdings : np.ndarray
        各资产持仓数量 h_i^{(n)}，shape=(N,)。
    info_delay : int
        信息延迟期数 δ_i。
    age : int
        存活步数。
    parent_id : int | None
        父代 agent_id（演化追踪）。
    ancestor_id : int | None
        祖源根 agent_id（策略家族标识）。
    wealth_history : list[float]
        财富时序。
    return_history : list[float]
        收益率时序。
    """

    _id_counter: int = 0

    def __init__(
        self,
        strategy: Strategy,
        *,
        cash: float,
        N: int,
        agent_id: int | None = None,
        info_delay: int = 0,
        parent_id: int | None = None,
        ancestor_id: int | None = None,
    ) -> None:
        """初始化 Agent。

        Parameters
        ----------
        strategy : Strategy
            策略编码。
        cash : float
            初始现金。
        N : int
            资产数量。
        agent_id : int | None
            若为 None 则自动分配。
        info_delay : int
            信息延迟。
        parent_id : int | None
            父代 ID。
        ancestor_id : int | None
            祖源 ID。
        """
        if agent_id is None:
            TradingAgent._id_counter += 1
            self.agent_id: int = TradingAgent._id_counter
        else:
            self.agent_id = agent_id

        self.strategy: Strategy = strategy
        self.cash: float = cash
        self.holdings: np.ndarray = np.zeros(N, dtype=np.float64)
        self._N: int = N

        self.info_delay: int = info_delay
        self.age: int = 0
        self.parent_id: int | None = parent_id
        self.ancestor_id: int | None = (
            ancestor_id if ancestor_id is not None else self.agent_id
        )

        self.wealth_history: list[float] = [cash]
        self.return_history: list[float] = []

        # 延迟信号缓冲
        self._delayed_signals: np.ndarray | None = None

    # ── 财富 ──

    @property
    def wealth(self) -> float:
        """总财富 W_i = C_i + Σ_n h_i^{(n)} · P^{(n)}。

        注意：需要外部传入价格数组。
        """
        return self.cash  # holdings * price 由外部累加

    def compute_wealth(self, prices: np.ndarray) -> float:
        """按市价重估财富。

        Parameters
        ----------
        prices : np.ndarray
            shape=(N,)，当前价格向量。

        Returns
        -------
        float
            W_i = C_i + Σ_n h_i^{(n)} · P^{(n)}。
        """
        return float(self.cash + np.dot(self.holdings, prices))

    # ── 感知与决策 ──

    def perceive(
        self,
        market: "BaseMarket",
        signal_computer: "SignalComputer",
        delay_rng: np.random.Generator | None = None,
    ) -> np.ndarray:
        """感知市场状态，计算信号向量。

        若 info_delay > 0 且有延迟缓冲，则使用延迟信号。

        Parameters
        ----------
        market : BaseMarket
            市场实例。
        signal_computer : SignalComputer
            信号计算器。
        delay_rng : np.random.Generator | None
            用于初始化信息延迟。

        Returns
        -------
        np.ndarray
            信号向量 s_i(t) ∈ ℝ^D。
        """
        raw = signal_computer.compute_all(
            market,
            holding_period=self.strategy.holding_period,
        )

        if self.info_delay == 0:
            return raw

        if self._delayed_signals is None:
            if delay_rng is not None:
                self.info_delay = int(delay_rng.poisson(1))
            self._delayed_signals = raw.copy()
            return raw

        # 返回延迟信号，更新缓冲
        delayed = self._delayed_signals.copy()
        self._delayed_signals = raw.copy()
        return delayed

    def decide(
        self,
        signals: np.ndarray,
        market: "BaseMarket",
        asset_idx: int = 0,
    ) -> tuple[int, float]:
        """根据信号决定交易方向和净需求。

        Parameters
        ----------
        signals : np.ndarray
            当前信号向量。
        market : BaseMarket
            市场实例。
        asset_idx : int
            目标资产索引。

        Returns
        -------
        tuple[int, float]
            (direction, net_demand)，direction ∈ {-1, 0, +1}。
        """
        direction = self.strategy.compute_direction(signals)
        if direction == 0:
            return (0, 0.0)

        price = market.get_price(asset_idx)
        volatility = signal_computer.realized_vol(
            self._prices_from_market(market, asset_idx),
            self.strategy.holding_period,
        )
        if volatility == 0:
            volatility = 0.01  # 下限

        target = self.strategy.compute_target_holdings(
            cash=self.cash,
            price=price,
            volatility=volatility,
        )
        # 财富约束：目标持仓不得超过可用现金可购买的最大数量
        max_shares = (max(0.0, self.cash) * 2.0) / price if price > 0 else 0.0
        target = min(target, max_shares) if max_shares > 0 else target
        target_qty = direction * target
        net_demand = target_qty - self.holdings[asset_idx]
        return (direction, float(net_demand))

    # ── 交易执行 ──

    def execute_trade(
        self,
        asset_idx: int,
        quantity: float,
        price: float,
        config: "EVOASMConfig | None" = None,
    ) -> float:
        """执行成交，更新持仓和现金。

        Parameters
        ----------
        asset_idx : int
            资产索引。
        quantity : float
            成交量（正=买入，负=卖出）。
        price : float
            成交价。
        config : EVOASMConfig | None
            配置（用于计算交易成本）。

        Returns
        -------
        float
            实际成交金额（扣除交易成本前）。
        """
        # 财富约束：买入不能透支，卖出不能超持
        if quantity > 0:
            # 买入：最多用可用现金的 2 倍
            max_buy_qty = (max(0.0, self.cash) * 2.0) / price if price > 0 else 0.0
            quantity = min(quantity, max_buy_qty)
        elif quantity < 0:
            # 卖出：不能超过现有持仓
            max_sell_qty = self.holdings[asset_idx]
            quantity = max(quantity, -max_sell_qty)
        cost = quantity * price
        # 再次检查：买入成本不得超过现金（不允许透支）
        if cost > self.cash and quantity > 0:
            quantity = self.cash / price if price > 0 else 0.0
            cost = quantity * price
        tc = 0.0
        if config is not None:
            tc += config.c_comm * abs(quantity) * price
            if quantity < 0:
                tc += config.c_stamp * abs(quantity) * price

        self.holdings[asset_idx] += quantity
        self.cash -= cost + tc
        return cost

    def record_step(
        self,
        prices: np.ndarray,
    ) -> None:
        """记录当前步的财富和收益率。

        Parameters
        ----------
        prices : np.ndarray
            shape=(N,)，当前价格向量。
        """
        w = self.compute_wealth(prices)
        if len(self.wealth_history) > 0 and self.wealth_history[-1] > 0:
            ret = (w - self.wealth_history[-1]) / self.wealth_history[-1]
        else:
            ret = 0.0
        self.wealth_history.append(w)
        self.return_history.append(ret)
        self.age += 1

    # ── 辅助 ──

    @staticmethod
    def _prices_from_market(
        market: "BaseMarket",
        asset_idx: int,
    ) -> np.ndarray:
        """从 market.P_history 提取价格数组。"""
        return np.array(
            [p[asset_idx] for p in market.P_history[-60:]],
            dtype=np.float64,
        )


# 模块级引用，避免循环导入
from ..signals.signal_computer import SignalComputer as _SC

signal_computer = _SC()
