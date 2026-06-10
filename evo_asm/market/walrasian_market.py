"""Walrasian 市场出清模型。

实现 MODEL_SPEC.md §7.2 方案A：
基于总供需的单一市场出清价，附涨跌停板限制。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .base_market import BaseMarket

if TYPE_CHECKING:
    from ..config import EVOASMConfig


class WalrasianMarket(BaseMarket):
    """Walrasian 拍卖人式市场出清。

    价格更新方程：
        ln P_n(t) = ln P_n(t-1) + κ · ED^{(n)}(t) + σ_noise · ξ(t)

    并施加涨跌停板 clamp：
        P_n(t) ∈ [P_n(t-1)·(1-ℓ₋), P_n(t-1)·(1+ℓ₊)]

    Attributes
    ----------
    _demand_buffer : np.ndarray | None
        当前步的 agent 需求暂存，shape=(M, N)。
    """

    def __init__(
        self,
        config: "EVOASMConfig",
        assets: list | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        """初始化 Walrasian 市场。

        Parameters
        ----------
        config : EVOASMConfig
            模型配置。
        assets : list[Asset] | None
            预设资产列表。
        rng : np.random.Generator | None
            随机数生成器。
        """
        super().__init__(config, assets=assets, rng=rng)
        self._demand_buffer: np.ndarray | None = None

    # ── 抽象方法实现 ──

    def update_fundamentals(self) -> None:
        """更新所有资产的基础价值。

        离散化 GBM + 均值回复：
            F_n(t) = F_n(t-1) · exp(μ_F − σ_F²/2
                      + φ · (F̄/F_{t-1} − 1) + σ_F · ξ_t)
        """
        mu = self.config.mu_F
        sigma = self.config.sigma_F
        phi = self.config.phi
        F_bar = self.config.F_bar

        # 预生成所有随机数
        noise = self.rng.normal(0, 1, size=self.config.N)

        for n, asset in enumerate(self.assets):
            prev = asset.F
            mean_rev = phi * (F_bar / prev - 1.0)
            drift = mu - 0.5 * sigma * sigma + mean_rev
            asset.F = prev * np.exp(drift + sigma * noise[n])
            asset.record()

    def clear(self, demands: np.ndarray) -> None:
        """Walrasian 市场出清。

        Parameters
        ----------
        demands : np.ndarray
            shape=(M, N)，净需求矩阵 D_i^{(n)}(t)。
        """
        # 存储需求缓冲
        self._demand_buffer = demands.copy()

        # 聚合总超额需求
        ED = self.aggregate_demand(demands)  # shape=(N,)

        # 计算成交量
        self.V = float(np.sum(np.abs(demands)))
        self.volume_history.append(self.V)

        kappa = self.config.kappa
        sigma_noise = self.config.sigma_noise
        price_limit = self.config.price_limit

        prev_P = self.P.copy()
        noise = self.rng.normal(0, 1, size=self.config.N)

        for n in range(self.config.N):
            # 对数价格更新（限制 delta 防止 exp 溢出）
            if prev_P[n] > 0:
                max_delta = np.log(1.0 + price_limit)
                min_delta = np.log(1.0 - price_limit)
                delta = kappa * ED[n] + sigma_noise * noise[n]
                delta = np.clip(delta, min_delta, max_delta)
                new_price = prev_P[n] * np.exp(delta)
            else:
                new_price = prev_P[n]
            # 涨跌停板限制
            upper = prev_P[n] * (1.0 + price_limit)
            lower = prev_P[n] * (1.0 - price_limit)
            self.P[n] = float(np.clip(new_price, lower, upper))

        # 记录价格历史
        self.record_price()
        self.step += 1

    @property
    def demand_buffer(self) -> np.ndarray | None:
        """返回当前步的需求缓冲（供 agent 写入）。"""
        return self._demand_buffer
