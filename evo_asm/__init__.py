"""EVO-ASM: Evolutionary Artificial Stock Market.

基于演化 Agent-Based Modeling 的量化交易策略生态系统
与 Alpha 消失机制研究。
"""

from .model import EVOASMModel
from .config import EVOASMConfig

__all__ = ["EVOASMModel", "EVOASMConfig"]
