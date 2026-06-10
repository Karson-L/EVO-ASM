"""信号计算器模块。

从市场数据计算 D 维信号向量 s_i(t)，供 Agent 感知层使用。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..market.base_market import BaseMarket


class SignalComputer:
    """D 维市场信号计算器。

    对给定价格/成交量序列计算动量、移动平均交叉、
    波动率、成交量异常、基本面偏离和短期反转六个信号。

    Attributes
    ----------
    ma_short_window : int
        短期移动平均窗口。
    ma_long_window : int
        长期移动平均窗口。
    vol_anomaly_window : int
        成交量异常检测窗口。
    reversal_window : int
        短期反转窗口。
    """

    def __init__(
        self,
        ma_short_window: int = 5,
        ma_long_window: int = 20,
        vol_anomaly_window: int = 20,
        reversal_window: int = 3,
    ) -> None:
        """初始化信号计算器。

        Parameters
        ----------
        ma_short_window : int
            短期 MA 窗口。
        ma_long_window : int
            长期 MA 窗口。
        vol_anomaly_window : int
            成交量均值/标准差计算窗口。
        reversal_window : int
            短期反转回看窗口。
        """
        self.ma_short_window = ma_short_window
        self.ma_long_window = ma_long_window
        self.vol_anomaly_window = vol_anomaly_window
        self.reversal_window = reversal_window

    def compute_all(
        self,
        market: "BaseMarket",
        holding_period: int = 20,
        asset_idx: int = 0,
    ) -> np.ndarray:
        """计算全部 D 个信号，返回长度为 D 的向量。

        Parameters
        ----------
        market : BaseMarket
            市场实例。
        holding_period : int
            Agent 的典型持仓周期（用于动量/波动率回看窗口）。
        asset_idx : int
            资产索引。

        Returns
        -------
        np.ndarray
            shape=(D,)，信号向量 s(t) ∈ ℝ^D。
        """
        prices = self._price_array(market, asset_idx, holding_period)
        volumes = self._volume_array(market, holding_period)
        asset = market.assets[asset_idx]

        s1 = self.momentum(prices, holding_period)
        s2 = self.ma_crossover(prices)
        s3 = self.realized_vol(prices, holding_period)
        s4 = self.volume_anomaly(volumes)
        s5 = self.fundamental_deviation(market.get_price(asset_idx), asset.F)
        s6 = self.short_reversal(prices)

                # 各信号分量 clamp 到合理范围，防止成交量异常等信号爆炸
        SIG_MAX = 5.0
        s1 = float(np.clip(s1, -SIG_MAX, SIG_MAX))
        s2 = float(np.clip(s2, -SIG_MAX, SIG_MAX))
        s3 = float(np.clip(s3, -SIG_MAX, SIG_MAX))
        s4 = float(np.clip(s4, -SIG_MAX, SIG_MAX))
        s5 = float(np.clip(s5, -SIG_MAX, SIG_MAX))
        s6 = float(np.clip(s6, -SIG_MAX, SIG_MAX))
        return np.array([s1, s2, s3, s4, s5, s6], dtype=np.float64)

    # ── 单项信号 ──

    @staticmethod
    def momentum(prices: np.ndarray, lookback: int) -> float:
        """价格动量：过去 lookback 期的指数加权平均收益率。

        Parameters
        ----------
        prices : np.ndarray
            价格序列，prices[-1] 为最新价。
        lookback : int
            回看窗口。

        Returns
        -------
        float
            S1 动量信号。
        """
        if len(prices) < 2:
            return 0.0
        returns = np.diff(prices[-lookback - 1:]) / prices[-lookback - 1:-1]
        if len(returns) == 0:
            return 0.0
        alpha = 2.0 / (lookback + 1)
        weights = (1 - alpha) ** np.arange(len(returns))[::-1]
        weights /= weights.sum()
        return float(np.dot(returns, weights))

    def ma_crossover(self, prices: np.ndarray) -> float:
        """移动平均交叉信号。

        (MA_short − MA_long) / MA_long

        Parameters
        ----------
        prices : np.ndarray
            价格序列。

        Returns
        -------
        float
            S2 信号。
        """
        if len(prices) < self.ma_long_window:
            return 0.0
        ma_short = np.mean(prices[-self.ma_short_window:])
        ma_long = np.mean(prices[-self.ma_long_window:])
        if ma_long == 0:
            return 0.0
        return float((ma_short - ma_long) / ma_long)

    @staticmethod
    def realized_vol(prices: np.ndarray, lookback: int) -> float:
        """已实现波动率。

        Parameters
        ----------
        prices : np.ndarray
            价格序列。
        lookback : int
            回看窗口。

        Returns
        -------
        float
            S3 波动率信号。
        """
        if len(prices) < 2:
            return 0.0
        returns = np.diff(prices[-lookback - 1:]) / prices[-lookback - 1:-1]
        if len(returns) < 2:
            return 0.0
        return float(np.std(returns, ddof=1))

    def volume_anomaly(self, volumes: np.ndarray) -> float:
        """成交量异常：(V_t − V̄) / σ_V。

        Parameters
        ----------
        volumes : np.ndarray
            成交量序列。

        Returns
        -------
        float
            S4 成交量异常信号。
        """
        if len(volumes) < self.vol_anomaly_window:
            return 0.0
        window = volumes[-self.vol_anomaly_window:]
        mean_v = np.mean(window[:-1])
        std_v = np.std(window[:-1], ddof=1)
        if std_v == 0:
            return 0.0
        return float((window[-1] - mean_v) / std_v)

    @staticmethod
    def fundamental_deviation(price: float, fundamental: float) -> float:
        """基本面偏离：(F − P) / P。

        Parameters
        ----------
        price : float
            当前价格。
        fundamental : float
            当前基础价值。

        Returns
        -------
        float
            S5 基本面偏离信号。
        """
        if price == 0:
            return 0.0
        return float((fundamental - price) / price)

    def short_reversal(self, prices: np.ndarray) -> float:
        """短期反转：近期负累收益率。

        Parameters
        ----------
        prices : np.ndarray
            价格序列。

        Returns
        -------
        float
            S6 反转信号。
        """
        if len(prices) < self.reversal_window + 1:
            return 0.0
        start = prices[-self.reversal_window - 1]
        end = prices[-1]
        if start == 0:
            return 0.0
        return float(-(end - start) / start)

    # ── 辅助 ──

    @staticmethod
    def _price_array(
        market: "BaseMarket",
        asset_idx: int,
        min_len: int,
    ) -> np.ndarray:
        """从 market.P_history 构建价格数组。"""
        prices = np.array(
            [p[asset_idx] for p in market.P_history[-max(min_len + 1, 60):]],
            dtype=np.float64,
        )
        return prices

    @staticmethod
    def _volume_array(
        market: "BaseMarket",
        min_len: int,
    ) -> np.ndarray:
        """从 market.volume_history 构建成交量数组。"""
        if hasattr(market, "volume_history") and len(market.volume_history) > 0:
            return np.array(market.volume_history[-max(min_len, 60):], dtype=np.float64)
        return np.array([float(market.V)])
