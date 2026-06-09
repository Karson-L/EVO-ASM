"""策略编码值对象。

承载 MODEL_SPEC §1.2 的策略四元组 π_i = (w_i, θ_i, τ_i, α_i)，
提供变异、克隆和信号计算接口。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Strategy:
    """Agent 策略编码的值对象。

    每个 Agent 持有一个 Strategy 实例，描述其交易行为。
    字段可变以支持 Mutation 操作。

    Attributes
    ----------
    weights : np.ndarray
        信号权重向量 w_i，shape=(D,)，L2 归一化后 ‖w‖₂ = 1。
    threshold : float
        进入阈值 θ_i ∈ [θ_min, θ_max]。
    holding_period : int
        典型持仓周期 τ_i，取值 {1, 3, 5, 10, 20, 60}。
    risk_appetite : float
        风险偏好 α_i ∈ [0, 1]。
    """

    weights: np.ndarray
    threshold: float = 0.10
    holding_period: int = 20
    risk_appetite: float = 0.5

    # ── 工厂方法 ──

    @classmethod
    def random(
        cls,
        D: int,
        rng: np.random.Generator | None = None,
        *,
        threshold_min: float = 0.01,
        threshold_max: float = 0.50,
        holding_periods: tuple[int, ...] = (1, 3, 5, 10, 20, 60),
        risk_low: float = 0.2,
        risk_high: float = 0.8,
        sigma_init: float = 0.10,
    ) -> "Strategy":
        """创建随机初始化的策略。

        Parameters
        ----------
        D : int
            信号空间维度。
        rng : np.random.Generator | None
            随机数生成器。
        threshold_min, threshold_max : float
            阈值范围。
        holding_periods : tuple[int, ...]
            允许的持仓周期值。
        risk_low, risk_high : float
            风险偏好范围。
        sigma_init : float
            权重初始化标准差。

        Returns
        -------
        Strategy
        """
        if rng is None:
            rng = np.random.default_rng()
        w = rng.normal(0, sigma_init, size=D)
        return cls(
            weights=cls._l2_normalize(w),
            threshold=float(rng.uniform(threshold_min, threshold_max)),
            holding_period=int(rng.choice(holding_periods)),
            risk_appetite=float(rng.uniform(risk_low, risk_high)),
        )

    @classmethod
    def momentum_focused(
        cls,
        D: int = 6,
        momentum_signal_idx: int = 0,
        *,
        momentum_weight: float = 0.85,
        rng: np.random.Generator | None = None,
    ) -> "Strategy":
        """创建动量主导的策略（趋势跟踪型）。

        动量信号（默认 S1）权重占主导，其余信号分配少量权重。

        Parameters
        ----------
        D : int
            信号空间维度。
        momentum_signal_idx : int
            动量信号在信号向量中的索引（默认 0 = S1）。
        momentum_weight : float
            动量信号的 L2 范数占比目标（0~1）。
        rng : np.random.Generator | None
            随机数生成器。

        Returns
        -------
        Strategy
        """
        if rng is None:
            rng = np.random.default_rng()
        w = np.zeros(D, dtype=np.float64)
        w[momentum_signal_idx] = momentum_weight
        # 其余维度分配噪声
        other_indices = [i for i in range(D) if i != momentum_signal_idx]
        noise = rng.normal(0, (1.0 - momentum_weight) / D, size=len(other_indices))
        for idx, val in zip(other_indices, noise):
            w[idx] = val
        return cls(
            weights=cls._l2_normalize(w),
            threshold=0.05,
            holding_period=20,
            risk_appetite=0.6,
        )

    # ── 核心方法 ──

    def compute_signal_strength(self, signals: np.ndarray) -> float:
        """计算综合方向强度 z = wᵀ · s。

        Parameters
        ----------
        signals : np.ndarray
            shape=(D,) 的信号向量。

        Returns
        -------
        float
            z ∈ ℝ。
        """
        return float(np.dot(self.weights, signals))

    def compute_direction(self, signals: np.ndarray) -> int:
        """根据信号强度和阈值决定交易方向。

        Parameters
        ----------
        signals : np.ndarray
            shape=(D,) 的信号向量。

        Returns
        -------
        int
            +1（做多）、−1（做空）、0（观望）。
        """
        z = self.compute_signal_strength(signals)
        if z > self.threshold:
            return +1
        if z < -self.threshold:
            return -1
        return 0

    def compute_target_holdings(
        self,
        cash: float,
        price: float,
        volatility: float,
    ) -> float:
        """计算目标持仓量。

        h_target = dir · α · cash / (σ · P · τ)

        Parameters
        ----------
        cash : float
            可用现金。
        price : float
            当前价格。
        volatility : float
            已实现波动率。

        Returns
        -------
        float
            目标持仓数量（需配合方向使用）。
        """
        if price <= 0 or volatility <= 0 or self.holding_period <= 0:
            return 0.0
        return self.risk_appetite * cash / (volatility * price * self.holding_period)

    # ── 变异操作 ──

    def mutate_weights(
        self,
        sigma: float,
        rng: np.random.Generator | None = None,
    ) -> None:
        """权重加高斯噪声后 L2 归一化。

        Parameters
        ----------
        sigma : float
            变异标准差。
        rng : np.random.Generator | None
        """
        if rng is None:
            rng = np.random.default_rng()
        noise = rng.normal(0, sigma, size=len(self.weights))
        self.weights += noise
        self.weights = self._l2_normalize(self.weights)

    def mutate_threshold(
        self,
        sigma: float,
        theta_min: float = 0.01,
        theta_max: float = 0.50,
        rng: np.random.Generator | None = None,
    ) -> None:
        """阈值加噪声后 clamp。

        Parameters
        ----------
        sigma : float
            变异标准差。
        theta_min, theta_max : float
            允许范围。
        rng : np.random.Generator | None
        """
        if rng is None:
            rng = np.random.default_rng()
        self.threshold += float(rng.normal(0, sigma))
        self.threshold = max(theta_min, min(theta_max, self.threshold))

    def mutate_holding_period(
        self,
        p_up: float = 0.05,
        p_down: float = 0.05,
        holding_periods: tuple[int, ...] = (1, 3, 5, 10, 20, 60),
        rng: np.random.Generator | None = None,
    ) -> None:
        """持仓周期离散跳跃：以概率 p_up 翻倍、p_down 减半。

        Parameters
        ----------
        p_up, p_down : float
            翻倍/减半概率。
        holding_periods : tuple[int, ...]
            允许值集合。
        rng : np.random.Generator | None
        """
        if rng is None:
            rng = np.random.default_rng()
        u = rng.random()
        if u < p_up:
            new_val = self.holding_period * 2
        elif u < p_up + p_down:
            new_val = max(1, self.holding_period // 2)
        else:
            return
        # clamp 到最近允许值
        best = min(holding_periods, key=lambda x: abs(x - new_val))
        self.holding_period = int(best)

    def mutate_risk_appetite(
        self,
        sigma: float,
        rng: np.random.Generator | None = None,
    ) -> None:
        """风险偏好加噪声后 clamp 到 [0, 1]。

        Parameters
        ----------
        sigma : float
            变异标准差。
        rng : np.random.Generator | None
        """
        if rng is None:
            rng = np.random.default_rng()
        self.risk_appetite += float(rng.normal(0, sigma))
        self.risk_appetite = max(0.0, min(1.0, self.risk_appetite))

    # ── 复制与序列化 ──

    def clone(self) -> "Strategy":
        """深拷贝策略。

        Returns
        -------
        Strategy
        """
        return Strategy(
            weights=self.weights.copy(),
            threshold=self.threshold,
            holding_period=self.holding_period,
            risk_appetite=self.risk_appetite,
        )

    def to_tuple(self) -> tuple:
        """返回向量化表示，用于聚类。"""
        return tuple(self.weights.tolist()) + (
            self.threshold,
            float(self.holding_period),
            self.risk_appetite,
        )

    # ── 内部工具 ──

    @staticmethod
    def _l2_normalize(w: np.ndarray) -> np.ndarray:
        """L2 归一化。"""
        norm = np.linalg.norm(w)
        if norm == 0:
            return w.copy()
        return w / norm
