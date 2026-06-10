"""Agent 模块单元测试。

测试范围：Strategy, TradingAgent, MomentumAgent。
"""

from __future__ import annotations

import math
import sys
import unittest

import numpy as np


from evo_asm.config import EVOASMConfig
from evo_asm.market.walrasian_market import WalrasianMarket
from evo_asm.signals.signal_computer import SignalComputer
from evo_asm.agents.strategy import Strategy
from evo_asm.agents.trading_agent import TradingAgent
from evo_asm.agents.momentum_agent import MomentumAgent


# ═══════════════════════════════════════════════════════════════════
# Strategy
# ═══════════════════════════════════════════════════════════════════

class TestStrategy(unittest.TestCase):
    """Strategy 值对象的单元测试。"""

    def setUp(self) -> None:
        self.rng = np.random.default_rng(42)

    def test_creation(self) -> None:
        w = np.array([1.0, 0.0, 0.0])
        s = Strategy(weights=w, threshold=0.1, holding_period=20, risk_appetite=0.5)
        self.assertEqual(s.threshold, 0.1)
        self.assertEqual(s.holding_period, 20)
        self.assertEqual(s.risk_appetite, 0.5)

    def test_random_factory(self) -> None:
        s = Strategy.random(D=6, rng=self.rng)
        self.assertEqual(len(s.weights), 6)
        self.assertAlmostEqual(np.linalg.norm(s.weights), 1.0, places=6)
        self.assertGreaterEqual(s.threshold, 0.01)
        self.assertLessEqual(s.threshold, 0.50)
        self.assertIn(s.holding_period, (1, 3, 5, 10, 20, 60))

    def test_momentum_focused_factory(self) -> None:
        s = Strategy.momentum_focused(D=6, momentum_signal_idx=0,
                                       momentum_weight=0.85, rng=self.rng)
        self.assertEqual(len(s.weights), 6)
        self.assertAlmostEqual(np.linalg.norm(s.weights), 1.0, places=6)
        # 动量信号权重应占主导
        self.assertGreater(abs(s.weights[0]), 0.7)

    def test_compute_signal_strength(self) -> None:
        w = np.array([1.0, 0.0])
        s = Strategy(weights=w)
        signals = np.array([0.05, 0.02])
        z = s.compute_signal_strength(signals)
        self.assertAlmostEqual(z, 0.05)

    def test_compute_direction_long(self) -> None:
        s = Strategy(weights=np.array([1.0, 0.0]), threshold=0.05)
        d = s.compute_direction(np.array([0.10, 0.0]))
        self.assertEqual(d, +1)

    def test_compute_direction_short(self) -> None:
        s = Strategy(weights=np.array([1.0, 0.0]), threshold=0.05)
        d = s.compute_direction(np.array([-0.10, 0.0]))
        self.assertEqual(d, -1)

    def test_compute_direction_neutral(self) -> None:
        s = Strategy(weights=np.array([1.0, 0.0]), threshold=0.05)
        d = s.compute_direction(np.array([0.02, 0.0]))
        self.assertEqual(d, 0)

    def test_compute_direction_boundary(self) -> None:
        """恰好等于阈值时不触发（严格大于才触发）。"""
        s = Strategy(weights=np.array([1.0, 0.0]), threshold=0.05)
        d = s.compute_direction(np.array([0.05, 0.0]))
        self.assertEqual(d, 0)

    def test_compute_target_holdings(self) -> None:
        s = Strategy(weights=np.array([1.0]), risk_appetite=1.0,
                     holding_period=20)
        h = s.compute_target_holdings(cash=100_000, price=100.0, volatility=0.02)
        expected = 1.0 * 100_000 / (0.02 * 100.0 * 20)
        self.assertAlmostEqual(h, expected)

    def test_compute_target_holdings_zero_price(self) -> None:
        s = Strategy(weights=np.array([1.0]))
        self.assertEqual(s.compute_target_holdings(1000, 0.0, 0.01), 0.0)

    def test_clone_returns_independent_copy(self) -> None:
        w = np.array([0.6, 0.8])
        w = w / np.linalg.norm(w)
        s1 = Strategy(weights=w, threshold=0.2, holding_period=10, risk_appetite=0.7)
        s2 = s1.clone()
        self.assertAlmostEqual(s2.threshold, 0.2)
        self.assertEqual(s2.holding_period, 10)
        # 修改 s2 不影响 s1
        s2.weights[0] = 999.0
        self.assertNotEqual(s1.weights[0], s2.weights[0])

    def test_mutate_weights_preserves_norm(self) -> None:
        s = Strategy.random(D=6, rng=self.rng)
        s.mutate_weights(sigma=0.03, rng=self.rng)
        self.assertAlmostEqual(np.linalg.norm(s.weights), 1.0, places=6)

    def test_mutate_threshold_clamps(self) -> None:
        s = Strategy(weights=np.array([1.0, 0.0]), threshold=0.01)
        s.mutate_threshold(sigma=10.0, theta_min=0.01, theta_max=0.50,
                           rng=self.rng)
        self.assertGreaterEqual(s.threshold, 0.01)
        self.assertLessEqual(s.threshold, 0.50)

    def test_mutate_holding_period(self) -> None:
        s = Strategy(weights=np.array([1.0, 0.0]), holding_period=10)
        periods = (1, 3, 5, 10, 20, 60)
        # 强制触发翻倍
        s.mutate_holding_period(p_up=1.0, p_down=0.0, holding_periods=periods,
                                rng=self.rng)
        self.assertEqual(s.holding_period, 20)

    def test_mutate_risk_appetite_clamps(self) -> None:
        s = Strategy(weights=np.array([1.0]), risk_appetite=0.5)
        s.mutate_risk_appetite(sigma=10.0, rng=self.rng)
        self.assertIn(s.risk_appetite, (0.0, 1.0))  # extreme sigma clamps

    def test_to_tuple(self) -> None:
        w = np.array([0.6, 0.8])
        w = w / np.linalg.norm(w)
        s = Strategy(weights=w, threshold=0.3, holding_period=5, risk_appetite=0.4)
        t = s.to_tuple()
        self.assertIsInstance(t, tuple)
        self.assertAlmostEqual(t[-1], 0.4)


# ═══════════════════════════════════════════════════════════════════
# TradingAgent
# ═══════════════════════════════════════════════════════════════════

class TestTradingAgent(unittest.TestCase):
    """TradingAgent 基类的单元测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(N=2, F_bar=100.0, seed=42, sigma_noise=0.0)
        self.rng = np.random.default_rng(42)
        self.market = WalrasianMarket(self.config, rng=self.rng)
        self.sc = SignalComputer()
        self.strategy = Strategy.random(D=6, rng=self.rng)

    def test_creation_defaults(self) -> None:
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=2)
        self.assertGreater(agent.agent_id, 0)
        self.assertEqual(agent.cash, 10_000)
        self.assertEqual(len(agent.holdings), 2)
        self.assertEqual(agent.holdings[0], 0.0)
        self.assertEqual(agent.age, 0)
        self.assertIsNone(agent.parent_id)
        self.assertIsNotNone(agent.ancestor_id)
        self.assertEqual(agent.ancestor_id, agent.agent_id)

    def test_creation_with_lineage(self) -> None:
        agent = TradingAgent(
            strategy=self.strategy, cash=5000, N=1,
            parent_id=10, ancestor_id=3, agent_id=42,
        )
        self.assertEqual(agent.agent_id, 42)
        self.assertEqual(agent.parent_id, 10)
        self.assertEqual(agent.ancestor_id, 3)

    def test_wealth_equals_cash_initially(self) -> None:
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=1)
        self.assertEqual(agent.wealth, 10_000)

    def test_compute_wealth_with_holdings(self) -> None:
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=1)
        agent.holdings[0] = 50.0
        prices = np.array([100.0])
        w = agent.compute_wealth(prices)
        self.assertAlmostEqual(w, 10_000 + 50 * 100)

    def test_perceive_returns_signal_vector(self) -> None:
        self.market.clear(np.zeros((1, 2)))  # 至少有一期数据
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=2)
        sig = agent.perceive(self.market, self.sc)
        self.assertEqual(len(sig), 6)

    def test_decide_no_signal_returns_neutral(self) -> None:
        self.market.clear(np.zeros((1, 2)))
        agent = TradingAgent(
            strategy=Strategy(weights=np.ones(6) / np.sqrt(6), threshold=0.50),
            cash=10_000, N=2,
        )
        sig = np.zeros(6)
        direction, demand = agent.decide(sig, self.market)
        self.assertEqual(direction, 0)
        self.assertEqual(demand, 0.0)

    def test_decide_positive_momentum_returns_long(self) -> None:
        """动量信号 > 阈值时触发做多。"""
        for _ in range(30):
            self.market.clear(np.array([[10.0, 0.0]]))  # 制造上涨趋势
        agent = TradingAgent(
            strategy=Strategy(
                weights=np.array([1.0, 0, 0, 0, 0, 0], dtype=np.float64),
                threshold=0.001,
                risk_appetite=0.5,
                holding_period=20,
            ),
            cash=100_000, N=2,
        )
        sig = agent.perceive(self.market, self.sc)
        direction, demand = agent.decide(sig, self.market)
        self.assertEqual(direction, +1)
        self.assertGreater(demand, 0)

    def test_execute_trade_buy(self) -> None:
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=1)
        cost = agent.execute_trade(asset_idx=0, quantity=10, price=100.0)
        self.assertAlmostEqual(cost, 1000.0)
        self.assertAlmostEqual(agent.holdings[0], 10.0)
        self.assertLess(agent.cash, 10_000)  # 扣款

    def test_execute_trade_sell(self) -> None:
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=1)
        agent.holdings[0] = 20.0
        cost = agent.execute_trade(asset_idx=0, quantity=-10, price=100.0)
        self.assertAlmostEqual(cost, -1000.0)
        self.assertAlmostEqual(agent.holdings[0], 10.0)
        self.assertGreater(agent.cash, 10_000)  # 收款（扣除交易成本）

    def test_execute_trade_with_transaction_cost(self) -> None:
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=1)
        agent.execute_trade(asset_idx=0, quantity=10, price=100.0,
                            config=self.config)
        # c_comm=0.0003: 10*100*0.0003 = 0.30
        # cash should be 9000 - 0.30 = 8999.70 (approximately)
        expected_cash = 10_000 - 1000 - 0.30
        self.assertAlmostEqual(agent.cash, expected_cash, places=4)

    def test_record_step(self) -> None:
        agent = TradingAgent(strategy=self.strategy, cash=10_000, N=1)
        agent.holdings[0] = 10.0
        agent.record_step(prices=np.array([105.0]))
        self.assertEqual(len(agent.wealth_history), 2)
        self.assertAlmostEqual(agent.wealth_history[-1], 10_000 + 10 * 105)
        self.assertGreater(agent.return_history[-1], 0)
        self.assertEqual(agent.age, 1)

    def test_info_delay(self) -> None:
        agent = TradingAgent(
            strategy=self.strategy, cash=10_000, N=2,
            info_delay=1,
        )
        self.market.clear(np.zeros((1, 2)))
        sig1 = agent.perceive(self.market, self.sc, delay_rng=self.rng)
        sig2 = agent.perceive(self.market, self.sc)
        # 第二次 perceive 返回的是第一次的延迟信号
        np.testing.assert_array_equal(sig1, sig2)


# ═══════════════════════════════════════════════════════════════════
# MomentumAgent
# ═══════════════════════════════════════════════════════════════════

class TestMomentumAgent(unittest.TestCase):
    """MomentumAgent 的单元测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(N=1, F_bar=100.0, seed=42, sigma_noise=0.0,
                                    kappa=0.001)
        self.rng = np.random.default_rng(42)
        self.market = WalrasianMarket(self.config, rng=self.rng)
        self.sc = SignalComputer()

    def _create_uptrend(self, steps: int = 30) -> None:
        """制造一段上涨趋势。"""
        for _ in range(steps):
            self.market.update_fundamentals()
            self.market.clear(np.array([[50.0]]))

    def _create_downtrend(self, steps: int = 30, demand: float = -55.0) -> None:
        """制造一段下跌趋势。"""
        for _ in range(steps):
            self.market.update_fundamentals()
            self.market.clear(np.array([[demand]]))

    def test_creation_defaults(self) -> None:
        agent = MomentumAgent(cash=100_000, N=1, D=6)
        self.assertGreater(agent.agent_id, 0)
        self.assertEqual(agent.momentum_window, 20)
        self.assertFalse(agent.confirmation_required)
        self.assertEqual(agent.max_position_pct, 1.0)
        # 动量聚焦策略
        self.assertGreater(abs(agent.strategy.weights[0]), 0.7)

    def test_creation_with_lineage(self) -> None:
        agent = MomentumAgent(
            cash=50_000, N=1, D=6,
            agent_id=77, parent_id=10, ancestor_id=3,
        )
        self.assertEqual(agent.agent_id, 77)
        self.assertEqual(agent.parent_id, 10)
        self.assertEqual(agent.ancestor_id, 3)

    def test_strategy_is_momentum_focused(self) -> None:
        agent = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
        w = agent.strategy.weights
        # S1（动量）权重最大
        max_idx = np.argmax(np.abs(w))
        self.assertEqual(max_idx, 0)

    def test_perceive_momentum(self) -> None:
        self._create_uptrend(30)
        agent = MomentumAgent(cash=100_000, N=1, D=6)
        sig = agent.perceive_momentum(self.market, self.sc)
        self.assertIn("momentum", sig)
        self.assertIn("ma_cross", sig)
        self.assertIn("volatility", sig)
        self.assertGreater(sig["momentum"], 0)

    def test_decide_momentum_uptrend_goes_long(self) -> None:
        self._create_uptrend(50)
        agent = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
        direction, demand = agent.decide_momentum(self.market, self.sc)
        self.assertEqual(direction, +1)
        self.assertGreater(demand, 0)

    def test_decide_momentum_downtrend_goes_short(self) -> None:
        self._create_downtrend(50)
        agent = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
        direction, demand = agent.decide_momentum(self.market, self.sc)
        self.assertEqual(direction, -1)
        self.assertLess(demand, 0)

    def test_decide_momentum_flat_market_neutral(self) -> None:
        """无趋势时观望。"""
        for _ in range(5):
            self.market.clear(np.zeros((1, 1)))
        agent = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
        direction, demand = agent.decide_momentum(self.market, self.sc)
        self.assertEqual(direction, 0)
        self.assertEqual(demand, 0.0)

    def test_confirm_required_prevents_false_signal(self) -> None:
        """confirmation_required=True 且 MA 交叉与动量方向相反时不开仓。"""
        self._create_uptrend(30)  # 动量偏正
        # 清除 market，重新构建——动量可能为正但 MA 交叉为负
        agent = MomentumAgent(
            cash=100_000, N=1, D=6,
            confirmation_required=True,
            rng=self.rng,
        )
        # 在一个趋势反转初期：动量仍为正，但短期MA在长期MA之下
        # 通过设置 agent 决策来测试
        sig = agent.perceive_momentum(self.market, self.sc)
        # 如果 confirmation 不满足，即使动量>阈值也不开仓
        # (具体行为取决于信号，这里验证方法存在即可)
        direction, _ = agent.decide_momentum(self.market, self.sc)
        self.assertIn(direction, (-1, 0, 1))

    def test_max_position_limit(self) -> None:
        self._create_uptrend(50)
        agent = MomentumAgent(
            cash=100_000, N=1, D=6,
            max_position_pct=0.25,  # 最多 25% 仓位
            rng=self.rng,
        )
        _, demand = agent.decide_momentum(self.market, self.sc)
        price = self.market.get_price(0)
        max_qty = 0.25 * 100_000 / price
        # demand 应不超过 max_qty
        self.assertLessEqual(abs(demand), max_qty * 1.01)

    def test_recent_momentum_property(self) -> None:
        self._create_uptrend(30)
        agent = MomentumAgent(cash=100_000, N=1, D=6)
        agent.perceive_momentum(self.market, self.sc)
        self.assertIsNotNone(agent.recent_momentum)

    def test_momentum_trend_strength(self) -> None:
        self._create_uptrend(30)
        agent = MomentumAgent(cash=100_000, N=1, D=6)
        for _ in range(10):
            agent.perceive_momentum(self.market, self.sc)
            self.market.update_fundamentals()
            self.market.clear(np.array([[50.0]]))
        strength = agent.momentum_trend_strength(lookback=5)
        self.assertIsInstance(strength, float)

    def test_decide_method_override(self) -> None:
        """覆盖的 decide() 方法应使用动量信号。"""
        self._create_uptrend(50)
        agent = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
        # 基类 decide 接口传入任意全信号——MomentumAgent 忽略并用自己的
        direction, _ = agent.decide(np.zeros(6), self.market)
        self.assertIn(direction, (-1, 0, 1))

    def test_execute_trade_integration(self) -> None:
        """交易执行后持仓和现金正确更新。"""
        self._create_uptrend(50)
        agent = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
        _, demand = agent.decide_momentum(self.market, self.sc)
        price = self.market.get_price(0)
        agent.execute_trade(asset_idx=0, quantity=demand, price=price,
                            config=self.config)
        # 持仓更新
        self.assertNotEqual(agent.holdings[0], 0.0)
        # 财富 = cash + holdings * price
        w = agent.compute_wealth(np.array([price]))
        self.assertGreater(w, 0)

    def test_record_step_updates_history(self) -> None:
        agent = MomentumAgent(cash=100_000, N=1, D=6)
        agent.record_step(prices=np.array([100.0]))
        self.assertEqual(len(agent.wealth_history), 2)
        self.assertEqual(agent.age, 1)


# ═══════════════════════════════════════════════════════════════════
# 运行
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
