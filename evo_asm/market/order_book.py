"""限价订单簿模块。

实现双边限价订单簿，支持提交、撤销、撮合操作。
遵循价格优先+时间优先原则。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class Side(Enum):
    """订单方向。"""
    BUY = auto()
    SELL = auto()


class OrderType(Enum):
    """订单类型。"""
    LIMIT = auto()
    MARKET = auto()


@dataclass
class Order:
    """限价/市价订单。

    Attributes
    ----------
    agent_id : int
        提交订单的 agent unique_id。
    side : Side
        买卖方向。
    quantity : int
        委托数量。
    price_limit : float
        限价（市价单可用 inf）。
    timestamp : int
        提交时的全局步数，用于时间优先。
    order_type : OrderType
        LIMIT 或 MARKET。
    order_id : int
        唯一订单 ID（自动递增）。
    filled : int
        已成交数量。
    cancelled : bool
        是否已撤销。
    """

    agent_id: int
    side: Side
    quantity: int
    price_limit: float
    timestamp: int
    order_type: OrderType = OrderType.LIMIT

    order_id: int = field(default=-1)
    filled: int = 0
    cancelled: bool = False

    @property
    def remaining(self) -> int:
        """剩余未成交量。"""
        return self.quantity - self.filled

    @property
    def is_filled(self) -> bool:
        """是否已完全成交。"""
        return self.remaining <= 0


@dataclass
class Trade:
    """单笔成交记录。

    Attributes
    ----------
    buyer_id : int
        买方 agent_id。
    seller_id : int
        卖方 agent_id。
    quantity : int
        成交量。
    price : float
        成交价。
    timestamp : int
        成交步数。
    buy_order_id : int
        买方订单 ID。
    sell_order_id : int
        卖方订单 ID。
    """

    buyer_id: int
    seller_id: int
    quantity: int
    price: float
    timestamp: int
    buy_order_id: int = -1
    sell_order_id: int = -1


class OrderBook:
    """双边限价订单簿。

    维护买盘（价格降序）和卖盘（价格升序），
    遵循价格优先 + 时间优先的撮合原则。

    Attributes
    ----------
    asset_idx : int
        绑定的资产索引。
    tick_size : float
        最小价格变动单位。
    depth_levels : int
        保留的深度档数。
    bids : list[Order]
        买盘订单列表（价格降序、时间升序）。
    asks : list[Order]
        卖盘订单列表（价格升序、时间升序）。
    trades : list[Trade]
        当前步成交记录列表。
    last_price : float | None
        最近一笔成交价。
    _next_order_id : int
        自增订单 ID 计数器。
    """

    def __init__(
        self,
        asset_idx: int = 0,
        tick_size: float = 0.01,
        depth_levels: int = 5,
    ) -> None:
        """初始化订单簿。

        Parameters
        ----------
        asset_idx : int
            绑定的资产索引。
        tick_size : float
            最小价格变动单位。
        depth_levels : int
            保留的深度档数（用于查询，不影响撮合）。
        """
        self.asset_idx: int = asset_idx
        self.tick_size: float = tick_size
        self.depth_levels: int = depth_levels

        self.bids: list[Order] = []   # 价格降序
        self.asks: list[Order] = []   # 价格升序
        self.trades: list[Trade] = []
        self.last_price: float | None = None
        self._next_order_id: int = 0

    # ── 订单插入位置计算 ──

    def _bid_insert_pos(self, order: Order) -> int:
        """计算买盘插入位置（价格降序，同价时间升序）。"""
        for i, b in enumerate(self.bids):
            if order.price_limit > b.price_limit:
                return i
            if order.price_limit == b.price_limit and order.timestamp < b.timestamp:
                return i
        return len(self.bids)

    def _ask_insert_pos(self, order: Order) -> int:
        """计算卖盘插入位置（价格升序，同价时间升序）。"""
        for i, a in enumerate(self.asks):
            if order.price_limit < a.price_limit:
                return i
            if order.price_limit == a.price_limit and order.timestamp < a.timestamp:
                return i
        return len(self.asks)

    # ── 撮合逻辑 ──

    def _match_buy(self, incoming: Order) -> list[Trade]:
        """撮合市价/限价买单与卖盘。

        Parameters
        ----------
        incoming : Order
            新提交的买单。

        Returns
        -------
        list[Trade]
            本次触发的成交列表。
        """
        trades: list[Trade] = []
        i = 0
        while i < len(self.asks) and incoming.remaining > 0:
            ask = self.asks[i]
            if ask.cancelled:
                i += 1
                continue
            # 限价检查：买单价格 >= 卖单价格
            if incoming.price_limit < ask.price_limit:
                if incoming.order_type == OrderType.MARKET:
                    # 市价单：吃尽所有卖盘
                    pass
                else:
                    break  # 限价单无法成交

            # 成交价 = 卖方报价（价格优先）
            trade_qty = min(incoming.remaining, ask.remaining)
            trade = Trade(
                buyer_id=incoming.agent_id,
                seller_id=ask.agent_id,
                quantity=trade_qty,
                price=ask.price_limit,
                timestamp=incoming.timestamp,
                buy_order_id=incoming.order_id,
                sell_order_id=ask.order_id,
            )
            trades.append(trade)

            incoming.filled += trade_qty
            ask.filled += trade_qty

            # 移除已完全成交或取消的卖单
            if ask.is_filled or ask.cancelled:
                self.asks.pop(i)
            else:
                i += 1

        return trades

    def _match_sell(self, incoming: Order) -> list[Trade]:
        """撮合市价/限价卖单与买盘。

        Parameters
        ----------
        incoming : Order
            新提交的卖单。

        Returns
        -------
        list[Trade]
            本次触发的成交列表。
        """
        trades: list[Trade] = []
        i = 0
        while i < len(self.bids) and incoming.remaining > 0:
            bid = self.bids[i]
            if bid.cancelled:
                i += 1
                continue
            # 限价检查：卖单价格 <= 买单价格
            if incoming.price_limit > bid.price_limit:
                if incoming.order_type == OrderType.MARKET:
                    pass
                else:
                    break

            # 成交价 = 买方报价（价格优先）
            trade_qty = min(incoming.remaining, bid.remaining)
            trade = Trade(
                buyer_id=bid.agent_id,
                seller_id=incoming.agent_id,
                quantity=trade_qty,
                price=bid.price_limit,
                timestamp=incoming.timestamp,
                buy_order_id=bid.order_id,
                sell_order_id=incoming.order_id,
            )
            trades.append(trade)

            incoming.filled += trade_qty
            bid.filled += trade_qty

            if bid.is_filled or bid.cancelled:
                self.bids.pop(i)
            else:
                i += 1

        return trades

    # ── 公共接口 ──

    def submit(self, order: Order) -> list[Trade]:
        """提交订单并立即尝试撮合。

        Parameters
        ----------
        order : Order
            待提交的订单。

        Returns
        -------
        list[Trade]
            本次撮合产生的全部成交。
        """
        order.order_id = self._next_order_id
        self._next_order_id += 1

        trades: list[Trade] = []

        if order.side == Side.BUY:
            trades = self._match_buy(order)
            # 若有剩余量，挂入买盘
            if order.remaining > 0 and not order.cancelled:
                pos = self._bid_insert_pos(order)
                self.bids.insert(pos, order)
        else:
            trades = self._match_sell(order)
            # 若有剩余量，挂入卖盘
            if order.remaining > 0 and not order.cancelled:
                pos = self._ask_insert_pos(order)
                self.asks.insert(pos, order)

        # 更新最后成交价
        for t in trades:
            self.last_price = t.price

        self.trades.extend(trades)
        return trades

    def cancel(self, order_id: int) -> bool:
        """撤销未成交订单。

        Parameters
        ----------
        order_id : int
            待撤销的订单 ID。

        Returns
        -------
        bool
            是否成功撤销。
        """
        for lst in (self.bids, self.asks):
            for o in lst:
                if o.order_id == order_id and not o.is_filled:
                    o.cancelled = True
                    return True
        return False

    def get_mid_price(self) -> float | None:
        """返回最佳买卖价的均值。

        Returns
        -------
        float | None
            (best_bid + best_ask) / 2；若一侧为空则返回 last_price。
        """
        best_bid = self._best_bid_price()
        best_ask = self._best_ask_price()
        if best_bid is not None and best_ask is not None:
            return (best_bid + best_ask) / 2.0
        return self.last_price

    def get_spread(self) -> float | None:
        """返回买卖价差。

        Returns
        -------
        float | None
            best_ask − best_bid；若任意侧为空则返回 None。
        """
        best_bid = self._best_bid_price()
        best_ask = self._best_ask_price()
        if best_bid is not None and best_ask is not None:
            return best_ask - best_bid
        return None

    def get_depth(self, side: Side, levels: int | None = None) -> list[tuple[float, int]]:
        """获取深度快照。

        Parameters
        ----------
        side : Side
            BUY 或 SELL。
        levels : int | None
            返回档数；None 则用 depth_levels。

        Returns
        -------
        list[tuple[float, int]]
            [(price, total_volume), ...]。
        """
        if levels is None:
            levels = self.depth_levels

        orders = self.bids if side == Side.BUY else self.asks
        depth: dict[float, int] = {}
        for o in orders:
            if o.cancelled or o.is_filled:
                continue
            depth[o.price_limit] = depth.get(o.price_limit, 0) + o.remaining

        if side == Side.BUY:
            result = sorted(depth.items(), key=lambda x: -x[0])
        else:
            result = sorted(depth.items(), key=lambda x: x[0])
        return result[:levels]

    def clear_expired(self, current_step: int) -> None:
        """清除过期的未成交订单（GTC 不自动过期，此方法预留）。

        Parameters
        ----------
        current_step : int
            当前步数。
        """
        # GTC 订单默认不过期；保留接口供扩展。
        pass

    # ── 内部辅助 ──

    def _best_bid_price(self) -> float | None:
        for b in self.bids:
            if not b.cancelled and not b.is_filled:
                return float(b.price_limit)
        return None

    def _best_ask_price(self) -> float | None:
        for a in self.asks:
            if not a.cancelled and not a.is_filled:
                return float(a.price_limit)
        return None

    def clear_trades(self) -> None:
        """清空当前步的成交记录。"""
        self.trades.clear()
