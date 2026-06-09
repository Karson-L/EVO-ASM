"""市场抽象基类。

定义 EVO-ASM 中市场模块的公共接口，支持 Walrasian 出清
和限价订单簿两种微观结构实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import numpy as np

from .asset import Asset

if TYPE_CHECKING:
    from ..config import EVOASMConfig


class BaseMarket(ABC):
    """市场模块抽象基类。

    所有市场微观结构实现（WalrasianMarket、OrderBookMarket）
    必须继承此类并实现全部抽象方法。

    Attributes
    ----------
    config : EVOASMConfig
        模型配置（市场相关参数）。
    assets : list[Asset]
        N 个资产实例。
    P : np.ndarray
        当前价格向量，shape=(N,)。
    P_history : list[np.ndarray]
        历史价格序列，每个元素为 shape=(N,) 的数组。
    V : float
        当前步成交量。
    step : int
        当前时间步序号。
    rng : np.random.Generator
        随机数生成器。
    """

    def __init__(
        self,
        config: "EVOASMConfig",
        assets: list[Asset] | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        """初始化市场。

        Parameters
        ----------
        config : EVOASMConfig
            模型配置。
        assets : list[Asset] | None
            预设资产列表。若为 None，则创建 N 个默认资产。
        rng : np.random.Generator | None
            随机数生成器。若为 None，则使用默认 BitGenerator。
        """
        self.config: "EVOASMConfig" = config
        self.rng: np.random.Generator = (
            rng if rng is not None
            else np.random.default_rng(config.seed)
        )

        if assets is not None:
            self.assets: list[Asset] = assets
        else:
            self.assets = [
                Asset(name=f"Asset_{n}", index=n, F=config.F_bar)
                for n in range(config.N)
            ]

        self.P: np.ndarray = np.full(config.N, config.F_bar, dtype=np.float64)
        self.P_history: list[np.ndarray] = [self.P.copy()]
        self.V: float = 0.0
        self.volume_history: list[float] = []
        self.step: int = 0

    # ── 抽象方法 ──

    @abstractmethod
    def update_fundamentals(self) -> None:
        """更新所有资产的基础价值 F^{(n)}(t)。

        按 GBM + 均值回复离散化递推。
        """
        ...

    @abstractmethod
    def clear(self, demands: np.ndarray) -> None:
        """根据 agent 需求矩阵计算清算价格。

        Parameters
        ----------
        demands : np.ndarray
            shape=(M, N)，agent_i 对 asset_n 的净需求。
        """
        ...

    # ── 具体方法 ──

    def get_price(self, asset_idx: int = 0) -> float:
        """返回资产的最新价格。

        Parameters
        ----------
        asset_idx : int
            资产索引（0-based）。

        Returns
        -------
        float
            当前价格 P^{(asset_idx)}(t)。
        """
        return float(self.P[asset_idx])

    def get_return(self, asset_idx: int = 0) -> float:
        """返回资产的最新对数收益率。

        Parameters
        ----------
        asset_idx : int
            资产索引（0-based）。

        Returns
        -------
        float
            r^{(n)}(t) = ln(P_t / P_{t-1})。
        """
        if len(self.P_history) < 2:
            return 0.0
        prev = float(self.P_history[-2][asset_idx])
        curr = float(self.P[asset_idx])
        if prev <= 0 or curr <= 0:
            return 0.0
        return float(np.log(curr / prev))

    def aggregate_demand(self, demands: np.ndarray) -> np.ndarray:
        """聚合 agent 需求为总超额需求 ED^{(n)}(t)。

        Parameters
        ----------
        demands : np.ndarray
            shape=(M, N)，净需求矩阵。

        Returns
        -------
        np.ndarray
            shape=(N,)，ED^{(n)}(t) = Σ_i D_i^{(n)}(t)。
        """
        return np.sum(demands, axis=0)

    def record_price(self) -> None:
        """将当前 P 追加到价格历史。"""
        self.P_history.append(self.P.copy())

    def reset(self) -> None:
        """重置市场状态（用于多轮模拟）。"""
        for asset in self.assets:
            asset.F = self.config.F_bar
            asset.F_history.clear()
            asset.record()
        self.P = np.full(self.config.N, self.config.F_bar, dtype=np.float64)
        self.P_history = [self.P.copy()]
        self.V = 0.0
        self.volume_history.clear()
        self.step = 0
