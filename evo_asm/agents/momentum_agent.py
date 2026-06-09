"""动量交易者 Agent。

趋势跟踪型 Agent，策略权重集中于动量信号（S1），
对移动平均交叉信号（S2）有次要关注。

继承自 TradingAgent，重写感知和决策逻辑以体现
动量交易特征：追涨杀跌、信号敏感度高、持仓周期较长。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .strategy import Strategy
from .trading_agent import TradingAgent

if TYPE_CHECKING:
    from ..config import EVOASMConfig
    from ..market.base_market import BaseMarket
    from ..signals.signal_computer import SignalComputer


class MomentumAgent(TradingAgent):
    """趋势跟踪型动量交易者。

    核心特征：
    - 策略权重集中在动量信号 S1（默认 w_MOM ≈ 0.85）
    - 移动平均交叉信号 S2 作为辅助确认
    - 阈值较低（θ ≈ 0.05），对趋势更敏感
    - 默认持仓周期较长（τ = 20）

    Attributes
    ----------
    momentum_window : int
        动量回看窗口。
    confirmation_required : bool
        是否需要 MA 交叉确认。
    max_position_pct : float
        单次建仓最大仓位比例（相对现金）。
    """

    def __init__(
        self,
        *,
        cash: float,
        N: int = 1,
        D: int = 6,
        momentum_window: int = 20,
        confirmation_required: bool = False,
        max_position_pct: float = 1.0,
        agent_id: int | None = None,
        info_delay: int = 0,
        parent_id: int | None = None,
        ancestor_id: int | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        """初始化动量交易者。

        Parameters
        ----------
        cash : float
            初始现金。
        N : int
            资产数量。
        D : int
            信号空间维度。
        momentum_window : int
            动量回看窗口。
        confirmation_required : bool
            是否需要 MA 交叉确认信号。
        max_position_pct : float
            单次建仓最大仓位比例。
        agent_id : int | None
        info_delay : int
        parent_id : int | None
        ancestor_id : int | None
        rng : np.random.Generator | None
        """
        # 使用动量聚焦策略初始化
        strategy = Strategy.momentum_focused(
            D=D,
            momentum_signal_idx=0,  # S1 动量
            momentum_weight=0.85,
            rng=rng,
        )

        super().__init__(
            strategy=strategy,
            cash=cash,
            N=N,
            agent_id=agent_id,
            info_delay=info_delay,
            parent_id=parent_id,
            ancestor_id=ancestor_id,
        )

        self.momentum_window: int = momentum_window
        self.confirmation_required: bool = confirmation_required
        self.max_position_pct: float = max_position_pct

        # 动量特有状态
        self._momentum_history: list[float] = []
        self._ma_cross_history: list[float] = []

    # ── 感知（动量特化） ──

    def perceive_momentum(
        self,
        market: "BaseMarket",
        signal_computer: "SignalComputer",
        asset_idx: int = 0,
    ) -> dict[str, float]:
        """仅计算动量相关信号，用于高效感知。

        Parameters
        ----------
        market : BaseMarket
            市场实例。
        signal_computer : SignalComputer
            信号计算器。
        asset_idx : int
            资产索引。

        Returns
        -------
        dict[str, float]
            {"momentum": S1, "ma_cross": S2, "volatility": S3}。
        """
        prices = self._prices_from_market(market, asset_idx)

        mom = signal_computer.momentum(prices, self.momentum_window)
        ma_cross = signal_computer.ma_crossover(prices)
        vol = signal_computer.realized_vol(prices, self.momentum_window)

        self._momentum_history.append(mom)
        self._ma_cross_history.append(ma_cross)

        return {"momentum": mom, "ma_cross": ma_cross, "volatility": vol}

    # ── 决策（动量特化） ──

    def decide_momentum(
        self,
        market: "BaseMarket",
        signal_computer: "SignalComputer",
        asset_idx: int = 0,
    ) -> tuple[int, float]:
        """动量特化决策。

        仅使用动量 + MA 交叉信号进行判断，忽略其余信号维度。

        Parameters
        ----------
        market : BaseMarket
        signal_computer : SignalComputer
        asset_idx : int

        Returns
        -------
        tuple[int, float]
            (direction, net_demand)。
        """
        sig = self.perceive_momentum(market, signal_computer, asset_idx)
        mom = sig["momentum"]
        ma_cross = sig["ma_cross"]
        vol = sig["volatility"]

        # 方向判断：动量 > 阈值
        threshold = self.strategy.threshold
        direction = 0

        if mom > threshold:
            if not self.confirmation_required or ma_cross > 0:
                direction = +1
        elif mom < -threshold:
            if not self.confirmation_required or ma_cross < 0:
                direction = -1

        if direction == 0:
            return (0, 0.0)

        price = market.get_price(asset_idx)
        if vol == 0:
            vol = 0.01

        # 仓位规模 = 风险偏好 × 现金 / (波动率 × 价格 × 持仓周期)
        target_value = (
            self.strategy.risk_appetite
            * self.cash
            / (vol * price * self.strategy.holding_period)
        )
        # 应用最大仓位限制
        max_value = self.max_position_pct * self.cash / price
        target_qty = direction * min(target_value, max_value)

        net_demand = target_qty - self.holdings[asset_idx]
        return (direction, float(net_demand))

    # ── 覆盖的通用方法 ──

    def decide(
        self,
        signals: np.ndarray,
        market: "BaseMarket",
        asset_idx: int = 0,
    ) -> tuple[int, float]:
        """MomentumAgent 使用 decide_momentum。

        覆盖基类方法，忽略传入的全信号向量，
        直接从 market 计算动量信号。
        """
        from ..signals.signal_computer import SignalComputer

        sc = SignalComputer()
        return self.decide_momentum(market, sc, asset_idx)

    # ── 诊断 ──

    @property
    def recent_momentum(self) -> float:
        """最近动量值。"""
        return self._momentum_history[-1] if self._momentum_history else 0.0

    @property
    def recent_ma_cross(self) -> float:
        """最近 MA 交叉信号。"""
        return self._ma_cross_history[-1] if self._ma_cross_history else 0.0

    def momentum_trend_strength(self, lookback: int = 5) -> float:
        """动量趋势强度的滚动平均。

        Parameters
        ----------
        lookback : int
            回看期数。

        Returns
        -------
        float
            最近 lookback 期动量的均值。
        """
        if len(self._momentum_history) == 0:
            return 0.0
        window = self._momentum_history[-lookback:]
        return float(np.mean(window))
