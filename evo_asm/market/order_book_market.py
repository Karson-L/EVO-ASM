"""订单簿驱动市场（方案B）。

使用 N 个 OrderBook 实例的市场，agent 提交限价单而非需求函数。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .base_market import BaseMarket
from .order_book import OrderBook, Order, Trade, Side, OrderType

if TYPE_CHECKING:
    from ..config import EVOASMConfig
    from .asset import Asset


class OrderBookMarket(BaseMarket):
    """订单簿驱动的金融市场。

    每个资产对应一个独立的 OrderBook。
    Agent 在 decide() 阶段生成 (side, qty, price_limit)，
    而非 Walrasian 模式的净需求。

    Attributes
    ----------
    books : list[OrderBook]
        每资产一个限价订单簿。
    """

    def __init__(
        self,
        config: "EVOASMConfig",
        assets: list[Asset] | None = None,
        rng: np.random.Generator | None = None,
        tick_size: float = 0.01,
    ) -> None:
        """初始化订单簿驱动市场。

        Parameters
        ----------
        config : EVOASMConfig
            模型配置。
        assets : list[Asset] | None
            预设资产列表。
        rng : np.random.Generator | None
            随机数生成器。
        tick_size : float
            最小价格变动单位。
        """
        super().__init__(config, assets=assets, rng=rng)

        self.books: list[OrderBook] = [
            OrderBook(asset_idx=n, tick_size=tick_size)
            for n in range(self.config.N)
        ]

    def update_fundamentals(self) -> None:
        """更新所有资产的基础价值。

        与 WalrasianMarket 相同：GBM + 均值回复。
        """
        mu = self.config.mu_F
        sigma = self.config.sigma_F
        phi = self.config.phi
        F_bar = self.config.F_bar
        noise = self.rng.normal(0, 1, size=self.config.N)

        for n, asset in enumerate(self.assets):
            prev = asset.F
            mean_rev = phi * (F_bar / prev - 1.0)
            drift = mu - 0.5 * sigma * sigma + mean_rev
            asset.F = prev * np.exp(drift + sigma * noise[n])
            asset.record()

    def clear(self, demands: np.ndarray) -> None:
        """订单簿市场不使用 demands 出清。

        在 OrderBookMarket 中，agent 直接向 books 提交订单，
        撮合在 submit() 时即时发生。此方法保留接口兼容性，
        主要负责价格更新和成交量汇总。

        Parameters
        ----------
        demands : np.ndarray
            shape=(M, N)，未使用，保留接口统一。
        """
        total_volume = 0.0
        for n, book in enumerate(self.books):
            # 从成交记录汇总成交量
            for trade in book.trades:
                total_volume += trade.quantity
            # 以订单簿中间价或最后成交价更新 P
            mid = book.get_mid_price()
            if mid is not None:
                self.P[n] = mid
            elif book.last_price is not None:
                self.P[n] = book.last_price
            # 清空当前步成交记录
            book.clear_trades()

        self.V = total_volume
        self.volume_history.append(self.V)
        self.record_price()
        self.step += 1

    def get_book(self, asset_idx: int = 0) -> OrderBook:
        """返回指定资产的订单簿。

        Parameters
        ----------
        asset_idx : int
            资产索引。

        Returns
        -------
        OrderBook
        """
        return self.books[asset_idx]

    def reset(self) -> None:
        """重置市场状态。"""
        super().reset()
        for book in self.books:
            book.bids.clear()
            book.asks.clear()
            book.trades.clear()
            book.last_price = None
