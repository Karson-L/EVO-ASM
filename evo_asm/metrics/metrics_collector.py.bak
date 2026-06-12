"""
MetricsCollector: ????????

?? ARCHITECTURE 4.12: ???? MODEL_SPEC 8 ??????????
???????????? CSV ???
"""
from __future__ import annotations

import math
from typing import Any, TYPE_CHECKING

import numpy as np

from evo_asm.config import EVOASMConfig
from evo_asm.metrics.alpha_tracker import AlphaTracker

if TYPE_CHECKING:
    from evo_asm.model import EVOASMModel


class MetricsCollector:
    """????????

    ??????????????????????
    ??????????????? AlphaTracker ????

    Parameters
    ----------
    config : EVOASMConfig
        ???????????????
    model_ref : EVOASMModel
        ??????????? agent ?????????

    Attributes
    ----------
    data : dict[str, list]
        ???: key=???, value=???????
    alpha_tracker : AlphaTracker
        Alpha ????????
    """

    def __init__(
        self,
        config: EVOASMConfig,
        model_ref: "EVOASMModel",
    ) -> None:
        self.config: EVOASMConfig = config
        self._model: "EVOASMModel" = model_ref

        # ?????
        self.data: dict[str, list[Any]] = {
            "step": [],
            "price": [],
            "fundamental": [],
            "log_return": [],
            "volume": [],
            "strategy_entropy": [],
            "n_families": [],
            "wealth_gini": [],
            "acf1": [],
            "mean_fitness": [],
        }
        self._return_buffer: list[float] = []

        # Alpha ???
        self.alpha_tracker: AlphaTracker = AlphaTracker(
            window=config.delta_alpha,
            alpha_thresh=config.alpha_thresh,
            eps_extinct=config.eps_extinct,
        )

    def record_step(self) -> None:
        """?????????????

        ? model ????????????????? data ???
        """
        model = self._model
        step = model.step_count
        market = model.market
        agents = model.agents

        price = market.get_price(0)

        # ?????
        if len(self.data["price"]) > 0:
            prev_price = self.data["price"][-1]
            if prev_price > 0:
                log_ret = math.log(price / prev_price)
            else:
                log_ret = 0.0
        else:
            log_ret = 0.0

        # ??????????????
        volume = 0.0
        for a in agents:
            dh = float(a.holdings[0]) - float(a._prev_holdings[0]) if hasattr(a, '_prev_holdings') else 0.0
            volume += abs(dh)

        # ???
        entropy = self._compute_strategy_entropy(agents)

        # ?????
        ancestor_ids = {a.ancestor_id for a in agents}
        n_families = len(ancestor_ids)

        # ??????
        gini = self._compute_wealth_gini(agents, price)

        # ???????
        self._return_buffer.append(log_ret)
        acf1 = self._compute_rolling_acf1(60)

        # ???????????????
        mean_fitness = 0.0
        if len(agents) > 0:
            wealths = [a.compute_wealth(price) for a in agents]
            mean_fitness = sum(wealths) / len(wealths) if wealths else 0.0

        # ????
        self.data["step"].append(step)
        self.data["price"].append(price)
        self.data["fundamental"].append(market._fundamentals[0] if hasattr(market, '_fundamentals') else price)
        self.data["log_return"].append(log_ret)
        self.data["volume"].append(volume)
        self.data["strategy_entropy"].append(entropy)
        self.data["n_families"].append(n_families)
        self.data["wealth_gini"].append(gini)
        self.data["acf1"].append(acf1)
        self.data["mean_fitness"].append(mean_fitness)

        # AlphaTracker ??
        self._update_alpha_tracker(step, agents, price, ancestor_ids)

    def _update_alpha_tracker(
        self, step: int, agents: list, price: float, ancestor_ids: set
    ) -> None:
        """?? AlphaTracker: ???????????"""
        total_wealth_all = sum(a.compute_wealth(price) for a in agents)
        if total_wealth_all <= 0:
            return

        families_by_id: dict[int, list] = {}
        for a in agents:
            families_by_id.setdefault(a.ancestor_id, []).append(a)

        for fid in ancestor_ids:
            fam_agents = families_by_id.get(fid, [])
            if not fam_agents:
                continue

            fam_wealth = sum(a.compute_wealth(price) for a in fam_agents)
            crowding = fam_wealth / total_wealth_all
            n = len(fam_agents)

            # ?????????????
            family_return = 0.0
            if len(self._return_buffer) > 0:
                family_return = self._return_buffer[-1]

            self.alpha_tracker.update(
                step=step,
                family_id=fid,
                family_return=family_return,
                crowding=crowding,
                total_wealth=fam_wealth,
                agent_count=n,
                total_wealth_all=total_wealth_all,
            )

        # ????????
        for fid in list(self.alpha_tracker.families.keys()):
            if fid not in ancestor_ids:
                lc = self.alpha_tracker.families[fid]
                if lc.is_alive:
                    lc.is_alive = False
                    lc.current_phase = "extinct"

    @staticmethod
    def _compute_strategy_entropy(agents: list) -> float:
        """????? H_strat = -sum_k p_k * ln(p_k)?

        ?? p_k ?? ancestor_id ????????
        """
        n = len(agents)
        if n <= 1:
            return 0.0

        counts: dict[int, int] = {}
        for a in agents:
            counts[a.ancestor_id] = counts.get(a.ancestor_id, 0) + 1

        entropy = 0.0
        for c in counts.values():
            p = c / n
            if p > 0:
                entropy -= p * math.log(p)
        return entropy

    @staticmethod
    def _compute_wealth_gini(agents: list, price: float) -> float:
        """?????????

        G = (1/(2*n^2*mu)) * sum_i sum_j |w_i - w_j|
        """
        n = len(agents)
        if n <= 1:
            return 0.0

        wealths = np.array([a.compute_wealth(price) for a in agents], dtype=np.float64)
        total = wealths.sum()
        if total <= 0:
            return 0.0

        # ?????
        sorted_w = np.sort(wealths)
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * sorted_w) - (n + 1) * total) / (n * total)
        return float(gini)

    def _compute_rolling_acf1(self, window: int = 60) -> float:
        """???????????????????

        Parameters
        ----------
        window : int
            ???????

        Returns
        -------
        float
            rho_1(t|window)???????????? 0.0?
        """
        buf = self._return_buffer
        if len(buf) < window + 1:
            return 0.0

        recent = np.array(buf[-window:], dtype=np.float64)
        if len(recent) < 2:
            return 0.0

        std = np.std(recent, ddof=1)
        if std < 1e-12:
            return 0.0

        mean = np.mean(recent)
        acf = np.mean((recent[:-1] - mean) * (recent[1:] - mean)) / (std ** 2)
        return float(acf)

    def to_dataframe(self) -> "pd.DataFrame":
        """?????????? DataFrame?"""
        import pandas as pd
        return pd.DataFrame(self.data)

    def to_families_dataframe(self) -> "pd.DataFrame":
        """???? AlphaTracker ?????? DataFrame?"""
        return self.alpha_tracker.to_dataframe(self._model.step_count)

    def reset(self) -> None:
        """??????????????"""
        for key in self.data:
            self.data[key].clear()
        self._return_buffer.clear()
        self.alpha_tracker = AlphaTracker(
            window=self.config.delta_alpha,
            alpha_thresh=self.config.alpha_thresh,
            eps_extinct=self.config.eps_extinct,
        )

    def get_summary(self) -> dict:
        """?????????

        Returns
        -------
        dict
            ?? final_price, mean_return, return_std, final_entropy,
            final_gini, final_n_families ?????
        """
        import numpy as np

        prices = self.data.get("price", [])
        returns = np.array(self.data.get("log_return", []), dtype=np.float64)
        returns = returns[np.isfinite(returns)]

        summary = {
            "steps_completed": len(self.data.get("step", [])),
            "final_price": float(prices[-1]) if prices else 0.0,
            "mean_return": float(np.mean(returns)) if len(returns) > 0 else 0.0,
            "return_std": float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0,
            "final_entropy": float(self.data["strategy_entropy"][-1]) if self.data["strategy_entropy"] else 0.0,
            "final_gini": float(self.data["wealth_gini"][-1]) if self.data["wealth_gini"] else 0.0,
            "final_n_families": int(self.data["n_families"][-1]) if self.data["n_families"] else 0,
            "active_families": self.alpha_tracker.get_alive_count(),
        }

        if len(returns) > 2:
            from scipy import stats
            try:
                summary["return_skewness"] = float(stats.skew(returns))
                summary["return_kurtosis"] = float(stats.kurtosis(returns))
            except Exception:
                pass

        return summary
