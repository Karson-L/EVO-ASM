"""EvolutionEngine 模块单元测试。

测试范围：EvolutionReport, EvolutionEngine。
"""

from __future__ import annotations

import math
import sys
import unittest

import numpy as np

sys.path.insert(0, r"C:\seelf\大三下\主修毕设")

from evo_asm.config import EVOASMConfig
from evo_asm.agents.strategy import Strategy
from evo_asm.agents.trading_agent import TradingAgent
from evo_asm.agents.momentum_agent import MomentumAgent
from evo_asm.evolution.evolution_engine import EvolutionEngine, EvolutionReport


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_agents(
    n: int,
    rng: np.random.Generator,
    *,
    D: int = 6,
    N: int = 1,
    cash: float = 100_000.0,
) -> list[TradingAgent]:
    """创建 n 个随机策略的 TradingAgent。"""
    agents = []
    for _ in range(n):
        s = Strategy.random(D=D, rng=rng)
        a = TradingAgent(strategy=s, cash=cash, N=N)
        agents.append(a)
    return agents


def _assign_returns(
    agents: list[TradingAgent],
    returns_per_agent: list[list[float]],
) -> None:
    """为 agent 赋值收益率历史（用于适应度测试）。"""
    for a, rets in zip(agents, returns_per_agent):
        a.return_history = list(rets)
        # 财富历史简化为从 cash 复合增长
        w = a.cash
        a.wealth_history = [w]
        for r in rets:
            w *= (1.0 + r)
            a.wealth_history.append(w)


# ═══════════════════════════════════════════════════════════════════
# EvolutionReport
# ═══════════════════════════════════════════════════════════════════

class TestEvolutionReport(unittest.TestCase):
    """EvolutionReport dataclass 的单元测试。"""

    def test_default_values(self) -> None:
        r = EvolutionReport()
        self.assertEqual(r.generation, 0)
        self.assertEqual(r.n_before, 0)
        self.assertEqual(r.n_eliminated, 0)
        self.assertEqual(r.eliminated_ids, [])

    def test_custom_values(self) -> None:
        r = EvolutionReport(
            generation=3,
            n_before=100,
            n_eliminated=20,
            n_survivors=80,
            n_new=20,
            n_after=100,
            mean_fitness_before=0.15,
            best_fitness=0.85,
            strategy_entropy_before=2.3,
            mutation_count=12,
        )
        self.assertEqual(r.generation, 3)
        self.assertEqual(r.n_eliminated, 20)
        self.assertAlmostEqual(r.mean_fitness_before, 0.15)


# ═══════════════════════════════════════════════════════════════════
# EvolutionEngine — 适应度
# ═══════════════════════════════════════════════════════════════════

class TestEvolutionEngineFitness(unittest.TestCase):
    """适应度计算测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(seed=42, r_f=0.0)
        self.rng = np.random.default_rng(42)
        self.engine = EvolutionEngine(self.config, rng=self.rng)

    def test_sharpe_zero_when_no_returns(self) -> None:
        self.assertEqual(self.engine._sharpe([]), 0.0)
        self.assertEqual(self.engine._sharpe([0.01]), 0.0)

    def test_sharpe_positive(self) -> None:
        rets = [0.01, 0.02, 0.01, 0.015, 0.02]
        s = self.engine._sharpe(rets)
        self.assertGreater(s, 0)

    def test_sharpe_zero_when_constant(self) -> None:
        rets = [0.01, 0.01, 0.01, 0.01]
        s = self.engine._sharpe(rets)
        self.assertEqual(s, 0.0)

    def test_sharpe_negative_for_negative_returns(self) -> None:
        rets = [-0.01, -0.02, -0.01, -0.015]
        s = self.engine._sharpe(rets)
        self.assertLess(s, 0)

    def test_compute_fitness_ranks_agents(self) -> None:
        agents = _make_agents(5, self.rng)
        _assign_returns(agents, [
            [0.01, 0.01, 0.01],   # low returns, low vol
            [0.05, 0.05, 0.05],   # high returns, low vol → best
            [-0.01, -0.01, -0.01],  # negative
            [0.02, 0.02, 0.02],   # medium
            [0.0, 0.0, 0.0],      # zero
        ])
        fitness = self.engine._compute_fitness(agents)
        self.assertEqual(len(fitness), 5)
        # agent 1 (high returns) should have highest fitness
        best_idx = int(np.argmax(fitness))
        self.assertEqual(best_idx, 1)

    def test_compute_fitness_with_window(self) -> None:
        agents = _make_agents(1, self.rng)
        agents[0].return_history = [0.01, 0.02, 0.03, 0.04, 0.05]
        f_all = self.engine._compute_fitness(agents, window=None)
        f_win = self.engine._compute_fitness(agents, window=2)
        # 窗口不同，适应度应不同
        self.assertNotEqual(f_all[0], f_win[0])


# ═══════════════════════════════════════════════════════════════════
# EvolutionEngine — 淘汰
# ═══════════════════════════════════════════════════════════════════

class TestEvolutionEngineElimination(unittest.TestCase):
    """淘汰操作测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(seed=42, P_eliminate=0.20)
        self.rng = np.random.default_rng(42)
        self.engine = EvolutionEngine(self.config, rng=self.rng)

    def test_eliminate_correct_count(self) -> None:
        agents = _make_agents(100, self.rng)
        _assign_returns(agents, [
            [float(i) * 0.001] * 10 for i in range(100)
        ])
        fitness = self.engine._compute_fitness(agents)
        survivors, eliminated = self.engine._eliminate(agents, fitness)
        self.assertEqual(len(eliminated), 20)
        self.assertEqual(len(survivors), 80)

    def test_eliminate_at_least_one(self) -> None:
        agents = _make_agents(3, self.rng)
        # 给极低适应度
        _assign_returns(agents, [
            [-0.10] * 5,
            [-0.10] * 5,
            [-0.10] * 5,
        ])
        fitness = np.array([0.0, 0.0, 0.0])
        survivors, eliminated = self.engine._eliminate(agents, fitness)
        self.assertGreaterEqual(len(eliminated), 1)

    def test_weakest_eliminated(self) -> None:
        agents = _make_agents(10, self.rng)
        # agent 0-4: negative, agent 5-9: positive
        returns = [[-0.01] * 10] * 5 + [[0.01] * 10] * 5
        _assign_returns(agents, returns)
        fitness = self.engine._compute_fitness(agents)
        survivors, eliminated = self.engine._eliminate(agents, fitness)
        # 淘汰的应该都是负收益 agent
        for e in eliminated:
            self.assertIn(e, agents[:5])


# ═══════════════════════════════════════════════════════════════════
# EvolutionEngine — 选择
# ═══════════════════════════════════════════════════════════════════

class TestEvolutionEngineSelection(unittest.TestCase):
    """选择操作测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(seed=42, lambda_select=3.0)
        self.rng = np.random.default_rng(42)
        self.engine = EvolutionEngine(self.config, rng=self.rng)

    def test_select_returns_correct_count(self) -> None:
        agents = _make_agents(50, self.rng)
        _assign_returns(agents, [
            [float(i) * 0.001] * 10 for i in range(50)
        ])
        fitness = self.engine._compute_fitness(agents)
        parents = self.engine._select_parents(agents, fitness, n_offspring=10)
        self.assertEqual(len(parents), 10)

    def test_select_zero_offspring(self) -> None:
        agents = _make_agents(10, self.rng)
        fitness = np.ones(10)
        parents = self.engine._select_parents(agents, fitness, n_offspring=0)
        self.assertEqual(len(parents), 0)

    def test_select_empty_survivors(self) -> None:
        parents = self.engine._select_parents([], np.array([]), n_offspring=5)
        self.assertEqual(len(parents), 0)

    def test_high_fitness_more_likely_selected(self) -> None:
        """统计验证：高适应度 agent 被选中的频率更高。"""
        agents = _make_agents(10, self.rng)
        # agent 9 适应度远高于其他
        fitness = np.array([0.01] * 9 + [10.0])
        counts = np.zeros(10, dtype=int)
        for _ in range(1000):
            parents = self.engine._select_parents(agents, fitness, n_offspring=1)
            counts[agents.index(parents[0])] += 1
        # agent 9 应被选中最多
        self.assertEqual(int(np.argmax(counts)), 9)
        self.assertGreater(counts[9], counts[0] * 5)

    def test_lambda_zero_uniform_selection(self) -> None:
        config = EVOASMConfig(seed=42, lambda_select=0.0)
        engine = EvolutionEngine(config, rng=self.rng)
        agents = _make_agents(3, self.rng)
        fitness = np.array([0.01, 10.0, 0.02])
        counts = np.zeros(3, dtype=int)
        for _ in range(300):
            parents = engine._select_parents(agents, fitness, n_offspring=1)
            counts[agents.index(parents[0])] += 1
        # λ=0 时近乎均匀
        self.assertGreater(counts[0], 50)
        self.assertGreater(counts[1], 50)
        self.assertGreater(counts[2], 50)

    def test_select_only_from_survivors(self) -> None:
        """选中父代应来自 survivors 列表。"""
        survivors = _make_agents(5, self.rng)
        fitness = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        parents = self.engine._select_parents(survivors, fitness, n_offspring=10)
        for p in parents:
            self.assertIn(p, survivors)


# ═══════════════════════════════════════════════════════════════════
# EvolutionEngine — 复制
# ═══════════════════════════════════════════════════════════════════

class TestEvolutionEngineReplication(unittest.TestCase):
    """复制操作测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(seed=42)
        self.rng = np.random.default_rng(42)
        self.engine = EvolutionEngine(self.config, rng=self.rng)

    def test_child_has_different_id(self) -> None:
        parent = MomentumAgent(cash=100_000, N=1, D=6, agent_id=5)
        child = self.engine._replicate(parent, N=1)
        self.assertNotEqual(child.agent_id, parent.agent_id)

    def test_child_inherits_parent_id(self) -> None:
        parent = MomentumAgent(cash=100_000, N=1, D=6, agent_id=5)
        child = self.engine._replicate(parent, N=1)
        self.assertEqual(child.parent_id, 5)

    def test_child_inherits_ancestor_id(self) -> None:
        parent = MomentumAgent(cash=100_000, N=1, D=6,
                                agent_id=5, ancestor_id=3)
        child = self.engine._replicate(parent, N=1)
        self.assertEqual(child.ancestor_id, 3)

    def test_child_strategy_is_clone_not_same_object(self) -> None:
        parent = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
        child = self.engine._replicate(parent, N=1)
        self.assertEqual(child.strategy.threshold, parent.strategy.threshold)
        self.assertEqual(child.strategy.holding_period, parent.strategy.holding_period)
        # 不同对象
        child.strategy.threshold = 999.0
        self.assertNotEqual(child.strategy.threshold, parent.strategy.threshold)

    def test_child_resets_age(self) -> None:
        parent = MomentumAgent(cash=100_000, N=1, D=6)
        parent.age = 50
        child = self.engine._replicate(parent, N=1)
        self.assertEqual(child.age, 0)

    def test_child_holdings_reset(self) -> None:
        parent = MomentumAgent(cash=100_000, N=2, D=6)
        parent.holdings[0] = 100.0
        child = self.engine._replicate(parent, N=2)
        self.assertEqual(child.holdings[0], 0.0)
        self.assertEqual(child.holdings[1], 0.0)


# ═══════════════════════════════════════════════════════════════════
# EvolutionEngine — 突变
# ═══════════════════════════════════════════════════════════════════

class TestEvolutionEngineMutation(unittest.TestCase):
    """突变操作测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(
            seed=42,
            p_mut=1.0,           # 强制突变
            sigma_mut=0.05,
            sigma_theta=0.02,
            sigma_alpha=0.05,
            p_tau_up=0.50,
            p_tau_down=0.0,
        )
        self.rng = np.random.default_rng(42)
        self.engine = EvolutionEngine(self.config, rng=self.rng)

    def test_mutate_changes_weights(self) -> None:
        agent = TradingAgent(
            strategy=Strategy.random(D=6, rng=self.rng),
            cash=100_000, N=1,
        )
        orig_w = agent.strategy.weights.copy()
        self.engine._mutate(agent)
        # 权重应改变
        self.assertFalse(np.allclose(orig_w, agent.strategy.weights))
        # 但仍 L2 归一化
        self.assertAlmostEqual(np.linalg.norm(agent.strategy.weights), 1.0, places=6)

    def test_mutate_returns_count(self) -> None:
        agent = TradingAgent(
            strategy=Strategy.random(D=6, rng=self.rng),
            cash=100_000, N=1,
        )
        count = self.engine._mutate(agent)
        self.assertEqual(count, 4)  # p_mut=1.0 → 全部 4 类突变

    def test_mutate_no_mutation_when_prob_zero(self) -> None:
        config = EVOASMConfig(seed=42, p_mut=0.0)
        engine = EvolutionEngine(config, rng=self.rng)
        agent = TradingAgent(
            strategy=Strategy.random(D=6, rng=self.rng),
            cash=100_000, N=1,
        )
        orig_w = agent.strategy.weights.copy()
        orig_t = agent.strategy.threshold
        count = engine._mutate(agent)
        self.assertEqual(count, 0)
        np.testing.assert_array_equal(orig_w, agent.strategy.weights)
        self.assertEqual(orig_t, agent.strategy.threshold)

    def test_mutate_threshold_stays_in_bounds(self) -> None:
        config = EVOASMConfig(
            seed=42, p_mut=1.0,
            sigma_theta=10.0,  # 极大变异 → 应被 clamp
            theta_min=0.01, theta_max=0.50,
        )
        engine = EvolutionEngine(config, rng=self.rng)
        agent = TradingAgent(
            strategy=Strategy(weights=np.ones(6) / np.sqrt(6), threshold=0.25),
            cash=100_000, N=1,
        )
        engine._mutate(agent)
        self.assertGreaterEqual(agent.strategy.threshold, 0.01)
        self.assertLessEqual(agent.strategy.threshold, 0.50)

    def test_mutate_risk_appetite_stays_in_bounds(self) -> None:
        config = EVOASMConfig(seed=42, p_mut=1.0, sigma_alpha=10.0)
        engine = EvolutionEngine(config, rng=self.rng)
        agent = TradingAgent(
            strategy=Strategy(weights=np.ones(6) / np.sqrt(6), risk_appetite=0.5),
            cash=100_000, N=1,
        )
        engine._mutate(agent)
        self.assertIn(agent.strategy.risk_appetite, (0.0, 1.0))

    def test_mutate_holding_period_in_allowed_set(self) -> None:
        config = EVOASMConfig(
            seed=42, p_mut=1.0,
            p_tau_up=1.0, p_tau_down=0.0,
            holding_periods=(1, 3, 5, 10, 20, 60),
        )
        engine = EvolutionEngine(config, rng=self.rng)
        agent = TradingAgent(
            strategy=Strategy(
                weights=np.ones(6) / np.sqrt(6),
                holding_period=10,
            ),
            cash=100_000, N=1,
        )
        engine._mutate(agent)
        self.assertEqual(agent.strategy.holding_period, 20)  # 翻倍


# ═══════════════════════════════════════════════════════════════════
# EvolutionEngine — 完整 evolve 循环
# ═══════════════════════════════════════════════════════════════════

class TestEvolutionEngineFullCycle(unittest.TestCase):
    """完整 evolve() 循环测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(
            seed=42,
            M=50,
            P_eliminate=0.20,
            lambda_select=3.0,
            p_mut=0.20,
        )
        self.rng = np.random.default_rng(42)
        self.engine = EvolutionEngine(self.config, rng=self.rng)

    def test_evolve_preserves_population_size(self) -> None:
        agents = _make_agents(50, self.rng)
        _assign_returns(agents, [
            [self.rng.normal(0.001, 0.02)] * 30
            for _ in range(50)
        ])
        report = self.engine.evolve(agents, N=1)
        self.assertEqual(report.n_before, 50)
        self.assertEqual(report.n_after, 50)
        self.assertEqual(len(agents), 50)

    def test_evolve_increments_generation(self) -> None:
        agents = _make_agents(50, self.rng)
        _assign_returns(agents, [
            [self.rng.normal(0.001, 0.02)] * 30
            for _ in range(50)
        ])
        self.assertEqual(self.engine.generation, 0)
        self.engine.evolve(agents, N=1)
        self.assertEqual(self.engine.generation, 1)
        self.engine.evolve(agents, N=1)
        self.assertEqual(self.engine.generation, 2)

    def test_evolve_records_history(self) -> None:
        agents = _make_agents(50, self.rng)
        _assign_returns(agents, [
            [self.rng.normal(0.001, 0.02)] * 30
            for _ in range(50)
        ])
        self.engine.evolve(agents, N=1)
        self.engine.evolve(agents, N=1)
        self.assertEqual(len(self.engine.history), 2)
        self.assertIsInstance(self.engine.history[0], EvolutionReport)

    def test_multi_generation_lineage_tracking(self) -> None:
        """多代演化后 ancestor_id 应正确传播。"""
        agents = _make_agents(20, self.rng)
        _assign_returns(agents, [
            [self.rng.normal(0.001, 0.03)] * 30
            for _ in range(20)
        ])
        # 记录初始 ancestor_ids
        initial_ancestors = {a.ancestor_id for a in agents}
        self.assertEqual(len(initial_ancestors), 20)  # 每个 agent 独立祖先

        # 运行多代
        for _ in range(5):
            _assign_returns(agents, [
                [self.rng.normal(0.001, 0.03)] * 30
                for _ in range(len(agents))
            ])
            self.engine.evolve(agents, N=1)

        # 祖源集应缩小（淘汰 + 复制）
        current_ancestors = {a.ancestor_id for a in agents}
        self.assertLess(len(current_ancestors), 20)

    def test_elite_survival(self) -> None:
        """极强 agent 应在多代后仍有后代存活。"""
        agents = _make_agents(30, self.rng)
        # 除一个 super-agent 外，其余表现中等
        returns = [[self.rng.normal(0.0, 0.02)] * 30 for _ in range(29)]
        returns.append([0.10] * 30)  # super-agent #29
        _assign_returns(agents, returns)
        super_ancestor = agents[29].ancestor_id

        survived_generations = 0
        for gen in range(10):
            # 重新赋收益（super-agent 的祖先族保持优势）
            new_returns = []
            for a in agents:
                if a.ancestor_id == super_ancestor:
                    new_returns.append([self.rng.normal(0.08, 0.02)] * 30)
                else:
                    new_returns.append([self.rng.normal(0.0, 0.02)] * 30)
            _assign_returns(agents, new_returns)
            self.engine.evolve(agents, N=1)

            # 检查是否有 super_ancestor 的后代
            if any(a.ancestor_id == super_ancestor for a in agents):
                survived_generations += 1

        # 应在多数代中存活
        self.assertGreaterEqual(survived_generations, 7)

    def test_reset_clears_state(self) -> None:
        agents = _make_agents(20, self.rng)
        _assign_returns(agents, [
            [self.rng.normal(0.001, 0.02)] * 30
            for _ in range(20)
        ])
        self.engine.evolve(agents, N=1)
        self.engine.reset()
        self.assertEqual(self.engine.generation, 0)
        self.assertEqual(len(self.engine.history), 0)

    def test_entropy_decreases_with_strong_selection(self) -> None:
        """选择压力强时策略熵随时间下降（策略同质化）。"""
        config = EVOASMConfig(
            seed=42, M=50,
            P_eliminate=0.30,
            lambda_select=10.0,  # 极强选择
            p_mut=0.05,
        )
        engine = EvolutionEngine(config, rng=self.rng)
        agents = _make_agents(50, self.rng)
        # 一个 agent 显著优于其他
        returns = [[self.rng.normal(0.0, 0.02)] * 30 for _ in range(49)]
        returns.append([0.10] * 30)
        _assign_returns(agents, returns)

        # 初始熵
        entropies = []
        for gen in range(8):
            new_returns = []
            for a in agents:
                if a.ancestor_id == agents[49].ancestor_id:
                    new_returns.append([self.rng.normal(0.10, 0.02)] * 30)
                else:
                    new_returns.append([self.rng.normal(0.0, 0.02)] * 30)
            _assign_returns(agents, new_returns)
            report = engine.evolve(agents, N=1)
            entropies.append(report.strategy_entropy_before)

        # 熵应下降（精英家族统治）
        self.assertLess(entropies[-1], entropies[0] * 0.8)

    def test_evolve_with_momentum_agents(self) -> None:
        """验证 EvolutionEngine 可与 MomentumAgent 协同工作。"""
        agents = []
        for _ in range(20):
            a = MomentumAgent(cash=100_000, N=1, D=6, rng=self.rng)
            a.return_history = [self.rng.normal(0.002, 0.02) for _ in range(30)]
            agents.append(a)

        report = self.engine.evolve(agents, N=1)
        self.assertEqual(report.n_before, 20)
        self.assertEqual(report.n_after, 20)
        # 所有 agent 应该仍是 MomentumAgent 或其父类实例
        for a in agents:
            self.assertIsInstance(a, TradingAgent)


# ═══════════════════════════════════════════════════════════════════
# 策略熵
# ═══════════════════════════════════════════════════════════════════

class TestStrategyEntropy(unittest.TestCase):
    """策略熵计算测试。"""

    def test_empty_agents(self) -> None:
        self.assertEqual(EvolutionEngine._compute_strategy_entropy([]), 0.0)

    def test_single_agent(self) -> None:
        agents = _make_agents(1, np.random.default_rng(42))
        # 单 agent → 单一家族 → H = 0
        h = EvolutionEngine._compute_strategy_entropy(agents)
        self.assertEqual(h, 0.0)

    def test_all_different_ancestors(self) -> None:
        rng = np.random.default_rng(42)
        agents = _make_agents(10, rng)
        # 每个 agent 有独立 ancestor_id → H = ln(10)
        h = EvolutionEngine._compute_strategy_entropy(agents)
        self.assertAlmostEqual(h, math.log(10), places=4)

    def test_two_families(self) -> None:
        """一半 agent 共享 ancestor_id=1，另一半 ancestor_id=2。"""
        rng = np.random.default_rng(42)
        s = Strategy.random(D=6, rng=rng)
        a1 = TradingAgent(strategy=s, cash=100_000, N=1,
                           agent_id=1, ancestor_id=1)
        a2 = TradingAgent(strategy=s, cash=100_000, N=1,
                           agent_id=2, ancestor_id=2)
        a3 = TradingAgent(strategy=s, cash=100_000, N=1,
                           agent_id=3, ancestor_id=1)
        a4 = TradingAgent(strategy=s, cash=100_000, N=1,
                           agent_id=4, ancestor_id=2)
        agents = [a1, a2, a3, a4]
        h = EvolutionEngine._compute_strategy_entropy(agents)
        # p_1 = 0.5, p_2 = 0.5 → H = ln(2)
        self.assertAlmostEqual(h, math.log(2), places=4)


# ═══════════════════════════════════════════════════════════════════
# 运行
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
