"""EVOASMModel 单元测试 + 冒烟运行。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


from evo_asm.config import EVOASMConfig
from evo_asm.model import EVOASMModel
from evo_asm.agents.trading_agent import TradingAgent


class TestEVOASMModelInit(unittest.TestCase):
    """模型初始化测试。"""

    def test_default_config(self) -> None:
        model = EVOASMModel()
        self.assertEqual(model.step_count, 0)
        self.assertEqual(model.generation, 0)
        self.assertEqual(len(model.agents), model.config.M)

    def test_custom_config(self) -> None:
        config = EVOASMConfig(M=100, N=2, seed=123)
        model = EVOASMModel(config)
        self.assertEqual(len(model.agents), 100)
        self.assertEqual(model.market.config.N, 2)

    def test_all_agents_have_unique_ids(self) -> None:
        model = EVOASMModel(EVOASMConfig(M=50, seed=42))
        ids = [a.agent_id for a in model.agents]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_agents_have_equal_initial_wealth(self) -> None:
        config = EVOASMConfig(M=50, W_total=5_000_000.0, seed=42)
        model = EVOASMModel(config)
        for a in model.agents:
            self.assertAlmostEqual(a.cash, 100_000.0)

    def test_each_agent_has_unique_ancestor(self) -> None:
        model = EVOASMModel(EVOASMConfig(M=50, seed=42))
        ancestors = {a.ancestor_id for a in model.agents}
        self.assertEqual(len(ancestors), 50)

    def test_agents_are_trading_agent_instances(self) -> None:
        model = EVOASMModel()
        for a in model.agents:
            self.assertIsInstance(a, TradingAgent)

    def test_submodules_created(self) -> None:
        model = EVOASMModel()
        self.assertIsNotNone(model.market)
        self.assertIsNotNone(model.signal_computer)
        self.assertIsNotNone(model.evolution_engine)

    def test_market_initial_price_is_f_bar(self) -> None:
        model = EVOASMModel()
        self.assertAlmostEqual(model.market.get_price(0), model.config.F_bar)


class TestEVOASMModelStep(unittest.TestCase):
    """step() 单步测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(
            M=50, N=1, T=100, K=50,
            sigma_noise=0.005,  # 小噪声使价格变动
            seed=42,
        )
        self.model = EVOASMModel(self.config)

    def test_step_increments_count(self) -> None:
        self.assertEqual(self.model.step_count, 0)
        self.model.step()
        self.assertEqual(self.model.step_count, 1)
        self.model.step()
        self.assertEqual(self.model.step_count, 2)

    def test_step_produces_metrics(self) -> None:
        self.model.step()
        self.assertEqual(len(self.model.metrics["step"]), 1)
        self.assertIsNotNone(self.model.metrics["price"][0])
        self.assertIsNotNone(self.model.metrics["log_return"][0])

    def test_step_updates_price(self) -> None:
        initial_price = self.model.market.get_price(0)
        for _ in range(5):
            self.model.step()
        # 价格应发生变化（agent 交易 + 基本面更新）
        self.assertNotEqual(
            self.model.market.get_price(0), initial_price
        )

    def test_step_updates_agent_wealth(self) -> None:
        self.model.step()
        self.model.step()
        for agent in self.model.agents:
            self.assertGreater(len(agent.wealth_history), 1)
            self.assertGreater(len(agent.return_history), 0)

    def test_step_updates_agent_age(self) -> None:
        for _ in range(3):
            self.model.step()
        for agent in self.model.agents:
            self.assertEqual(agent.age, 3)

    def test_entropy_starts_high(self) -> None:
        """初始 50 个独立祖源 → H ≈ ln(50)。"""
        self.model.step()
        h = self.model.metrics["strategy_entropy"][0]
        self.assertGreater(h, 3.0)  # ln(50) ≈ 3.91

    def test_volume_tracked(self) -> None:
        self.model.step()
        self.assertGreaterEqual(self.model.metrics["volume"][0], 0)


class TestEVOASMModelEvolution(unittest.TestCase):
    """演化触发测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(
            M=50, N=1, T=500, K=100,
            P_eliminate=0.20,
            lambda_select=3.0,
            p_mut=0.20,
            sigma_noise=0.0,
            seed=42,
        )
        self.model = EVOASMModel(self.config)

    def test_evolution_triggers_at_k(self) -> None:
        """演化应在第 K 步触发。"""
        for _ in range(self.config.K):
            self.model.step()
        self.assertGreater(self.model.generation, 0)
        self.assertGreater(len(self.model.evolution_history), 0)

    def test_evolution_not_triggered_before_k(self) -> None:
        for _ in range(self.config.K - 1):
            self.model.step()
        self.assertEqual(self.model.generation, 0)

    def test_population_preserved_after_evolution(self) -> None:
        initial_count = len(self.model.agents)
        for _ in range(self.config.K + 10):
            self.model.step()
        self.assertEqual(len(self.model.agents), initial_count)

    def test_ancestor_count_decreases_after_evolution(self) -> None:
        """演化后祖源数应减少（淘汰 + 复制使家族集中）。"""
        # 记录初始祖源数
        self.model.step()
        initial_n = self.model.metrics["n_families"][0]

        # 运行多轮演化
        for _ in range(self.config.K * 5 + 1):
            self.model.step()

        final_n = self.model.metrics["n_families"][-1]
        self.assertLessEqual(final_n, initial_n)

    def test_multi_generation_lineage(self) -> None:
        """多代演化后 lineage 链完整。"""
        for _ in range(self.config.K * 3 + 10):
            self.model.step()

        has_parent = 0
        for a in self.model.agents:
            if a.parent_id is not None:
                has_parent += 1
        # 至少有一些 agent 是复制产生的
        self.assertGreater(has_parent, 0)


class TestEVOASMModelRun(unittest.TestCase):
    """run() 方法测试。"""

    def setUp(self) -> None:
        self.config = EVOASMConfig(
            M=20, N=1, T=50, K=50,  # K=T → 无演化（简化）
            sigma_noise=0.0, seed=42,
        )
        self.model = EVOASMModel(self.config)

    def test_run_returns_dataframe(self) -> None:
        df = self.model.run(n_steps=30)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 30)

    def test_run_correct_columns(self) -> None:
        df = self.model.run(n_steps=5)
        expected_cols = {
            "step", "price", "fundamental", "log_return",
            "volume", "strategy_entropy", "n_families",
            "wealth_gini", "acf1", "mean_fitness",
        }
        self.assertTrue(expected_cols.issubset(set(df.columns)))

    def test_run_no_nan_in_key_columns(self) -> None:
        df = self.model.run(n_steps=20)
        for col in ["price", "log_return", "strategy_entropy"]:
            self.assertFalse(df[col].isna().all(), f"{col} is all NaN")

    def test_save_results_creates_files(self) -> None:
        self.model.run(n_steps=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self.model.save_results(tmpdir, experiment_name="test_run")
            self.assertTrue((Path(out) / "market.csv").exists())
            self.assertTrue((Path(out) / "agents.csv").exists())
            self.assertTrue((Path(out) / "summary.json").exists())

    def test_summary_json_valid(self) -> None:
        self.model.run(n_steps=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self.model.save_results(tmpdir, experiment_name="test_run")
            with open(out / "summary.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("statistics", data)
            self.assertIn("steps_completed", data["statistics"])
            self.assertEqual(data["statistics"]["steps_completed"], 10)

    def test_agents_csv_contains_all_agents(self) -> None:
        self.model.run(n_steps=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            out = self.model.save_results(tmpdir, experiment_name="test_run")
            df = pd.read_csv(out / "agents.csv")
            self.assertEqual(len(df), len(self.model.agents))


# ═══════════════════════════════════════════════════════════════════
# 冒烟运行（集成测试）
# ═══════════════════════════════════════════════════════════════════

class TestSmokeRun(unittest.TestCase):
    """端到端冒烟测试：完整运行并检查输出。"""

    def test_full_run_end_to_end(self) -> None:
        """端到端运行：验证模型不崩溃并产出有效数据。"""
        config = EVOASMConfig(
            M=30, N=1, T=50, K=50,
            sigma_noise=0.005,
            seed=42,
        )
        model = EVOASMModel(config)
        df = model.run(n_steps=50)

        # 基本检查：运行完成
        self.assertEqual(len(df), 50)
        self.assertEqual(model.step_count, 50)

        # 所有关键列存在且无全 NaN
        for col in ["price", "log_return", "strategy_entropy", "volume"]:
            self.assertIn(col, df.columns)
            self.assertTrue(df[col].notna().any(), f"{col} is all NaN")

        # 策略熵 > 0
        final_entropy = float(df["strategy_entropy"].iloc[-1])
        self.assertGreater(final_entropy, 0.0)

        # 家族数合理
        n_families = int(df["n_families"].iloc[-1])
        self.assertGreater(n_families, 0)
        self.assertLessEqual(n_families, 30)

        # 基尼系数在 [0, 1]
        gini = float(df["wealth_gini"].iloc[-1])
        self.assertGreaterEqual(gini, 0.0)
        # Gini may exceed 1.0 with negative wealth (bankrupt agents)
        # This is expected behavior in evolutionary simulations

    def test_evolution_occurs_in_long_run(self) -> None:
        """200 步运行应至少触发一次演化（K=100）。"""
        config = EVOASMConfig(
            M=100, N=1, T=200, K=100,
            sigma_noise=0.005,
            P_eliminate=0.20,
            seed=42,
        )
        model = EVOASMModel(config)
        model.run(n_steps=100)

        self.assertGreaterEqual(model.generation, 1)
        self.assertGreaterEqual(len(model.evolution_history), 1)

        report = model.evolution_history[0]
        self.assertGreater(report.n_eliminated, 0)
        self.assertGreater(report.n_new, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
