"""Market 模块单元测试。

测试范围：Asset, WalrasianMarket, OrderBook, OrderBookMarket。
"""

from __future__ import annotations

import math
import sys
import unittest

import numpy as np


from evo_asm.config import EVOASMConfig
from evo_asm.market.asset import Asset
from evo_asm.market.walrasian_market import WalrasianMarket
from evo_asm.market.order_book import (
    OrderBook, Order, Trade, Side, OrderType,
)
from evo_asm.market.order_book_market import OrderBookMarket


# ═══════════════════════════════════════════════════════════════════
# Asset
# ═══════════════════════════════════════════════════════════════════

class TestAsset(unittest.TestCase):
    """Asset dataclass 的单元测试。"""

    def test_creation_defaults(self) -> None:
        a = Asset(name="TEST", index=0)
        self.assertEqual(a.name, "TEST")
        self.assertEqual(a.index, 0)
        self.assertEqual(a.F, 100.0)
        self.assertIsNone(a.mu_F)
        self.assertIsNone(a.sigma_F)
        self.assertEqual(len(a.F_history), 0)

    def test_creation_custom(self) -> None:
        a = Asset(name="CUSTOM", index=2, F=200.0, mu_F=0.05, sigma_F=0.2)
        self.assertEqual(a.F, 200.0)
        self.assertEqual(a.mu_F, 0.05)
        self.assertEqual(a.sigma_F, 0.2)

    def test_record_appends_f(self) -> None:
        a = Asset(name="REC", index=0, F=100.0)
        a.record()
        a.F = 102.0
        a.record()
        self.assertEqual(a.F_history, [100.0, 102.0])

    def test_repr(self) -> None:
        a = Asset(name="REPR", index=1, F=99.5)
        r = repr(a)
        self.assertIn("REPR", r)
        self.assertIn("99.5000", r)


# ═══════════════════════════════════════════════════════════════════
# WalrasianMarket
# ═══════════════════════════════════════════════════════════════════

class TestWalrasianMarket(unittest.TestCase):
    """WalrasianMarket 的单元测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(
            N=2,
            kappa=0.001,
            sigma_noise=0.0,       # 关闭噪声以便确定性测试
            price_limit=0.10,
            mu_F=0.0,
            sigma_F=0.01,
            phi=0.0,
            F_bar=100.0,
            seed=42,
        )
        self.rng = np.random.default_rng(42)
        self.market = WalrasianMarket(self.config, rng=self.rng)

    def test_initial_state(self) -> None:
        m = self.market
        self.assertEqual(len(m.assets), 2)
        self.assertEqual(m.assets[0].name, "Asset_0")
        self.assertEqual(m.assets[1].name, "Asset_1")
        np.testing.assert_array_equal(m.P, np.array([100.0, 100.0]))
        self.assertEqual(m.V, 0.0)
        self.assertEqual(m.step, 0)

    def test_get_price(self) -> None:
        self.assertEqual(self.market.get_price(0), 100.0)
        self.assertEqual(self.market.get_price(1), 100.0)

    def test_get_return_zero_on_first_step(self) -> None:
        self.assertEqual(self.market.get_return(0), 0.0)

    def test_aggregate_demand(self) -> None:
        demands = np.array([
            [10.0, -5.0],
            [-3.0, 8.0],
            [-7.0, -3.0],
        ])
        ED = self.market.aggregate_demand(demands)
        np.testing.assert_array_equal(ED, np.array([0.0, 0.0]))

    def test_update_fundamentals(self) -> None:
        self.market.update_fundamentals()
        for asset in self.market.assets:
            self.assertGreater(asset.F, 0)
            self.assertGreaterEqual(len(asset.F_history), 1)

    def test_clear_zero_demand_unchanged_price(self) -> None:
        """当 sigma_noise=0 且需求为零时，价格不变。"""
        demands = np.zeros((10, 2))
        self.market.clear(demands)
        np.testing.assert_array_almost_equal(
            self.market.P, np.array([100.0, 100.0])
        )
        self.assertEqual(self.market.step, 1)

    def test_clear_positive_demand_raises_price(self) -> None:
        """正净需求推高价格。"""
        demands = np.array([[500.0, 0.0]])  # 仅 asset_0 有正需求
        self.market.clear(demands)
        self.assertGreater(self.market.get_price(0), 100.0)

    def test_clear_negative_demand_lowers_price(self) -> None:
        """负净需求压低价格。"""
        demands = np.array([[-500.0, 0.0]])
        self.market.clear(demands)
        self.assertLess(self.market.get_price(0), 100.0)

    def test_price_limit_upper(self) -> None:
        """涨跌幅限制：上涨不超过 +10%。"""
        # 极大正需求
        demands = np.array([[10000, 0.0]])
        self.market.clear(demands)
        self.assertLessEqual(
            self.market.get_price(0), 100.0 * 1.10 + 1e-9
        )

    def test_price_limit_lower(self) -> None:
        """涨跌幅限制：下跌不超过 −10%。"""
        demands = np.array([[-10000, 0.0]])
        self.market.clear(demands)
        self.assertGreaterEqual(
            self.market.get_price(0), 100.0 * 0.90 - 1e-9
        )

    def test_volume_recorded(self) -> None:
        demands = np.array([
            [10.0, -5.0],
            [-7.0, 5.0],
        ])
        self.market.clear(demands)
        expected = 10 + 5 + 7 + 5
        self.assertEqual(self.market.V, float(expected))

    def test_price_history_appended(self) -> None:
        demands = np.zeros((1, 2))
        self.market.clear(demands)
        self.assertEqual(len(self.market.P_history), 2)

    def test_get_return_after_price_change(self) -> None:
        demands = np.array([[100.0, 0.0]])
        self.market.clear(demands)
        r = self.market.get_return(0)
        self.assertGreater(r, 0.0)

    def test_reset(self) -> None:
        demands = np.array([[500.0, 0.0]])
        self.market.clear(demands)
        self.market.reset()
        self.assertEqual(self.market.step, 0)
        np.testing.assert_array_equal(self.market.P, np.array([100.0, 100.0]))
        self.assertEqual(self.market.V, 0.0)
        self.assertEqual(len(self.market.P_history), 1)

    def test_demand_buffer(self) -> None:
        demands = np.array([[1.0, -1.0], [2.0, 3.0]])
        self.market.clear(demands)
        buf = self.market.demand_buffer
        self.assertIsNotNone(buf)
        assert buf is not None
        np.testing.assert_array_equal(buf, demands)


# ═══════════════════════════════════════════════════════════════════
# OrderBook
# ═══════════════════════════════════════════════════════════════════

class TestOrderBook(unittest.TestCase):
    """OrderBook 的单元测试。"""

    def setUp(self) -> None:
        self.book = OrderBook(asset_idx=0, tick_size=0.01)

    # ── 初始状态 ──

    def test_initial_state(self) -> None:
        self.assertEqual(self.book.asset_idx, 0)
        self.assertEqual(len(self.book.bids), 0)
        self.assertEqual(len(self.book.asks), 0)
        self.assertIsNone(self.book.last_price)
        self.assertIsNone(self.book.get_mid_price())
        self.assertIsNone(self.book.get_spread())

    # ── 基础撮合 ──

    def test_submit_buy_fills_against_ask(self) -> None:
        """限价买单与卖单撮合。"""
        ask = Order(
            agent_id=1, side=Side.SELL, quantity=100,
            price_limit=10.0, timestamp=0,
        )
        self.book.submit(ask)

        bid = Order(
            agent_id=2, side=Side.BUY, quantity=50,
            price_limit=10.0, timestamp=1,
        )
        trades = self.book.submit(bid)

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 50)
        self.assertEqual(trades[0].price, 10.0)
        self.assertEqual(trades[0].buyer_id, 2)
        self.assertEqual(trades[0].seller_id, 1)
        self.assertEqual(self.book.last_price, 10.0)

    def test_submit_sell_fills_against_bid(self) -> None:
        """限价卖单与买单撮合。"""
        bid = Order(
            agent_id=1, side=Side.BUY, quantity=100,
            price_limit=10.0, timestamp=0,
        )
        self.book.submit(bid)

        sell = Order(
            agent_id=2, side=Side.SELL, quantity=60,
            price_limit=10.0, timestamp=1,
        )
        trades = self.book.submit(sell)

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 60)
        self.assertEqual(trades[0].price, 10.0)

    def test_partial_fill(self) -> None:
        """部分成交。"""
        # 挂卖单
        ask = Order(agent_id=1, side=Side.SELL, quantity=100,
                    price_limit=10.0, timestamp=0)
        self.book.submit(ask)
        # 买入 30 股
        bid = Order(agent_id=2, side=Side.BUY, quantity=30,
                    price_limit=10.0, timestamp=1)
        trades = self.book.submit(bid)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 30)
        # 卖单剩余 70
        self.assertEqual(len(self.book.asks), 1)
        self.assertEqual(self.book.asks[0].remaining, 70)

    def test_multiple_fills(self) -> None:
        """一笔买单扫过多档卖盘。"""
        self.book.submit(Order(1, Side.SELL, 50, 10.00, 0))
        self.book.submit(Order(1, Side.SELL, 50, 10.05, 0))
        trades = self.book.submit(Order(2, Side.BUY, 80, 10.10, 1))
        self.assertEqual(len(trades), 2)
        total = sum(t.quantity for t in trades)
        self.assertEqual(total, 80)

    def test_no_cross_no_trade(self) -> None:
        """价格不交叉，不成交。"""
        self.book.submit(Order(1, Side.SELL, 100, 10.00, 0))
        trades = self.book.submit(Order(2, Side.BUY, 50, 9.90, 1))
        self.assertEqual(len(trades), 0)
        # 买单挂入买盘
        self.assertEqual(len(self.book.bids), 1)
        self.assertEqual(self.book.bids[0].price_limit, 9.90)

    # ── 价格优先 ──

    def test_price_priority_bids(self) -> None:
        """买盘按价格降序排列。"""
        self.book.submit(Order(1, Side.BUY, 10, 10.00, 0))
        self.book.submit(Order(2, Side.BUY, 10, 10.05, 1))
        self.book.submit(Order(3, Side.BUY, 10, 9.95, 2))
        prices = [b.price_limit for b in self.book.bids]
        self.assertEqual(prices, [10.05, 10.00, 9.95])

    def test_price_priority_asks(self) -> None:
        """卖盘按价格升序排列。"""
        self.book.submit(Order(1, Side.SELL, 10, 10.00, 0))
        self.book.submit(Order(2, Side.SELL, 10, 9.95, 1))
        self.book.submit(Order(3, Side.SELL, 10, 10.05, 2))
        prices = [a.price_limit for a in self.book.asks]
        self.assertEqual(prices, [9.95, 10.00, 10.05])

    # ── 时间优先 ──

    def test_time_priority_same_price(self) -> None:
        """同价先到者优先成交。"""
        self.book.submit(Order(1, Side.SELL, 50, 10.00, timestamp=0))
        self.book.submit(Order(2, Side.SELL, 50, 10.00, timestamp=1))
        trades = self.book.submit(Order(3, Side.BUY, 50, 10.00, timestamp=2))
        self.assertEqual(len(trades), 1)
        # timestamp=0 的卖单先被撮合
        self.assertEqual(trades[0].seller_id, 1)

    # ── 撤销 ──

    def test_cancel_order(self) -> None:
        self.book.submit(Order(1, Side.BUY, 10, 10.00, 0))
        # 第二个订单 order_id=1
        o = Order(2, Side.BUY, 10, 10.05, 1)
        self.book.submit(o)
        self.assertTrue(self.book.cancel(o.order_id))
        self.assertTrue(o.cancelled)

    def test_cancel_nonexistent(self) -> None:
        self.assertFalse(self.book.cancel(999))

    # ── Mid price / spread ──

    def test_mid_price(self) -> None:
        self.book.submit(Order(1, Side.BUY, 10, 9.90, 0))
        self.book.submit(Order(2, Side.SELL, 10, 10.10, 1))
        self.assertAlmostEqual(self.book.get_mid_price(), 10.00)  # type: ignore[arg-type]

    def test_spread(self) -> None:
        self.book.submit(Order(1, Side.BUY, 10, 9.90, 0))
        self.book.submit(Order(2, Side.SELL, 10, 10.10, 1))
        self.assertAlmostEqual(self.book.get_spread(), 0.20)  # type: ignore[arg-type]

    def test_mid_price_one_side_empty(self) -> None:
        """一侧为空时回退到 last_price。"""
        self.book.submit(Order(1, Side.SELL, 10, 10.00, 0))
        self.book.submit(Order(2, Side.BUY, 10, 10.00, 1))
        # 全部成交，两侧皆空
        self.assertIsNotNone(self.book.last_price)
        self.assertEqual(self.book.get_mid_price(), self.book.last_price)

    # ── 深度快照 ──

    def test_depth_aggregates_same_price(self) -> None:
        self.book.submit(Order(1, Side.BUY, 10, 10.00, 0))
        self.book.submit(Order(2, Side.BUY, 15, 10.00, 1))
        depth = self.book.get_depth(Side.BUY)
        self.assertEqual(depth[0], (10.00, 25))

    # ── 市价单 ──

    def test_market_order_buy(self) -> None:
        self.book.submit(Order(1, Side.SELL, 100, 10.00, 0))
        mo = Order(2, Side.BUY, 50, price_limit=float("inf"),
                   timestamp=1, order_type=OrderType.MARKET)
        trades = self.book.submit(mo)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].quantity, 50)

    # ── 成交价规则 ──

    def test_trade_price_uses_resting_order_price(self) -> None:
        """成交价 = 被动方（已挂单）的报价。"""
        self.book.submit(Order(1, Side.SELL, 100, 9.95, 0))
        trades = self.book.submit(Order(2, Side.BUY, 50, 10.00, 1))
        self.assertEqual(trades[0].price, 9.95)


# ═══════════════════════════════════════════════════════════════════
# OrderBookMarket
# ═══════════════════════════════════════════════════════════════════

class TestOrderBookMarket(unittest.TestCase):
    """OrderBookMarket 的单元测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(
            N=2,
            mu_F=0.0,
            sigma_F=0.01,
            phi=0.0,
            F_bar=100.0,
            seed=42,
        )
        self.rng = np.random.default_rng(42)
        self.market = OrderBookMarket(self.config, rng=self.rng)

    def test_initial_state(self) -> None:
        self.assertEqual(len(self.market.books), 2)
        self.assertEqual(self.market.books[0].asset_idx, 0)
        self.assertEqual(self.market.books[1].asset_idx, 1)

    def test_get_book(self) -> None:
        book = self.market.get_book(0)
        self.assertIs(book, self.market.books[0])

    def test_update_fundamentals(self) -> None:
        self.market.update_fundamentals()
        for asset in self.market.assets:
            self.assertGreater(asset.F, 0)

    def test_clear_updates_price_from_trades(self) -> None:
        """撮合后 clear() 将最后成交价写入 P。"""
        book = self.market.get_book(0)
        book.submit(Order(1, Side.SELL, 100, 10.00, 0))
        book.submit(Order(2, Side.BUY, 50, 10.00, 1))

        self.market.clear(np.zeros((1, 2)))
        self.assertEqual(self.market.get_price(0), 10.00)

    def test_clear_no_trades_keeps_price(self) -> None:
        self.market.clear(np.zeros((1, 2)))
        # 无成交时价格不变（仍为初始 F_bar）
        self.assertAlmostEqual(self.market.get_price(0), 100.0)

    def test_volume_aggregated(self) -> None:
        book = self.market.get_book(0)
        book.submit(Order(1, Side.SELL, 30, 10.00, 0))
        book.submit(Order(2, Side.BUY, 30, 10.00, 1))
        book.submit(Order(3, Side.SELL, 20, 10.00, 2))
        book.submit(Order(4, Side.BUY, 20, 10.00, 3))

        self.market.clear(np.zeros((1, 2)))
        self.assertEqual(self.market.V, 50.0)

    def test_reset(self) -> None:
        book = self.market.get_book(0)
        book.submit(Order(1, Side.SELL, 10, 10.00, 0))
        book.submit(Order(2, Side.BUY, 10, 10.00, 1))
        self.market.clear(np.zeros((1, 2)))
        self.market.reset()

        self.assertEqual(self.market.step, 0)
        self.assertAlmostEqual(self.market.get_price(0), 100.0)
        self.assertEqual(len(self.market.books[0].bids), 0)
        self.assertEqual(len(self.market.books[0].asks), 0)
        self.assertIsNone(self.market.books[0].last_price)

    def test_multiple_assets_independent_books(self) -> None:
        book0 = self.market.get_book(0)
        book1 = self.market.get_book(1)

        book0.submit(Order(1, Side.SELL, 10, 10.00, 0))
        book1.submit(Order(1, Side.SELL, 10, 20.00, 0))

        self.assertIsNot(book0, book1)
        self.assertEqual(book0.asks[0].price_limit, 10.00)
        self.assertEqual(book1.asks[0].price_limit, 20.00)


# ═══════════════════════════════════════════════════════════════════
# 运行
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
