"""EVO-ASM 顶层模型 — Mesa Model 子类。

协调 Market、EvolutionEngine、MetricsCollector、SignalComputer 等模块。
此处仅为 Market 模块编译所需的最小存根；完整实现见后续。
"""

from __future__ import annotations

from .config import EVOASMConfig


class EVOASMModel:
    """EVO-ASM 顶层模型（存根）。

    完整实现将在后续阶段完成。当前仅暴露 config 属性
    以支持 Market 模块的依赖解析。
    """

    def __init__(self, config: EVOASMConfig | None = None):
        self.config = config if config is not None else EVOASMConfig()
        self.step_count: int = 0
        self.generation: int = 0
