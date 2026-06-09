"""EVO-ASM 模型参数集中定义。

所有可配置参数在此 dataclass 中声明，支持序列化与反序列化，
保证参数可追溯、可复现。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class EVOASMConfig:
    """EVO-ASM 模型全部参数的不可变配置。

    Attributes
    ----------
    M : int
        Agent 总数。
    N : int
        资产数量。
    T : int
        模拟总期数（交易日）。
    D : int
        信号空间维度。
    """

    # ── 结构参数 ──
    M: int = 1000
    N: int = 1
    T: int = 10_000
    D: int = 6

    # ── 演化参数 ──
    K: int = 200
    P_eliminate: float = 0.20
    lambda_select: float = 3.0
    p_mut: float = 0.20
    sigma_mut: float = 0.03
    sigma_theta: float = 0.01
    sigma_alpha: float = 0.03

    # ── 市场参数 ──
    kappa: float = 0.001
    sigma_noise: float = 0.005
    price_limit: float = 0.10
    mu_F: float = 0.0
    sigma_F: float = 0.01
    phi: float = 0.001
    F_bar: float = 100.0
    c_comm: float = 0.0003
    c_stamp: float = 0.001

    # ── 测量参数 ──
    delta_alpha: int = 60
    alpha_thresh: float = 0.002
    eps_extinct: float = 0.0005
    gamma: float = 1.0
    r_f: float = 0.0

    # ── 初始化参数 ──
    W_total: float = 10_000_000.0
    sigma_init: float = 0.10
    theta_min: float = 0.01
    theta_max: float = 0.50

    # ── 随机种子 ──
    seed: Optional[int] = None

    # ── Agent 策略阈值 ──
    kappa_TF: float = 0.40
    kappa_MR: float = 0.40
    kappa_VL: float = 0.40
    kappa_VT: float = 0.40
    epsilon_noise: float = 0.05

    # ── 持仓周期允许值 ──
    holding_periods: tuple = field(default=(1, 3, 5, 10, 20, 60))

    # ── 演变变参数 ──
    p_tau_up: float = 0.05
    p_tau_down: float = 0.05

    def to_dict(self) -> dict:
        """将所有字段序列化为字典，用于日志和复现。

        Returns
        -------
        dict
            字段名到值的映射。
        """
        return {k: v for k, v in self.__dataclass_fields__.items()
                if not k.startswith("_")}

    @classmethod
    def from_dict(cls, d: dict) -> "EVOASMConfig":
        """从字典构建配置，用于 BatchRunner 参数扫描。

        Parameters
        ----------
        d : dict
            包含配置字段的字典（可含子集，其余取默认值）。

        Returns
        -------
        EVOASMConfig
        """
        defaults = cls().to_dict()
        defaults.update(d)
        return cls(**defaults)
