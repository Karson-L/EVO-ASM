"""资产定义模块。

提供 Asset dataclass，描述模拟市场中每只资产的基础属性
与基础价值动力学。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Asset:
    """单个金融资产的定义。

    Attributes
    ----------
    name : str
        资产名称。
    index : int
        在资产数组中的索引（0-based）。
    F : float
        当前基础价值。
    mu_F : float | None
        漂移率，若为 None 则使用全局 mu_F。
    sigma_F : float | None
        基础价值波动率，若为 None 则使用全局 sigma_F。
    F_history : list[float]
        基础价值时序（最近值在前）。
    """

    name: str
    index: int
    F: float = 100.0
    mu_F: float | None = None
    sigma_F: float | None = None
    F_history: list[float] = field(default_factory=list)

    def record(self) -> None:
        """将当前 F 追加到历史记录中。"""
        self.F_history.append(self.F)

    def __repr__(self) -> str:
        return (
            f"Asset(name={self.name!r}, index={self.index}, "
            f"F={self.F:.4f})"
        )
