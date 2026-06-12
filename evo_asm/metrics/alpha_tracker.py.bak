"""
AlphaTracker: Alpha????????

?? MODEL_SPEC 8.3: ????????? Alpha ???????
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AlphaLifecycle:
    """??????? Alpha ???????

    Attributes
    ----------
    family_id : int
        ???????ancestor_id??
    birth_step : int
        ????????? t_0?
    alpha_series : list[float]
        alpha_k(t) ?????
    crowding_series : list[float]
        ??? C_k(t) ?????
    wealth_series : list[float]
        ??????????
    agent_count_series : list[int]
        ?? agent ???????
    t_emerge : int | None
        ?? I -> II ????
    t_peak : int | None
        ?? II -> III ????Alpha ????
    t_half : int | None
        Alpha ????Alpha ???????????
    t_extinct : int | None
        ?? IV -> V ????????
    current_phase : str
        ?????????
    is_alive : bool
        ?????? agent?
    peak_alpha : float
        alpha_k(t_peak) ???
    """

    family_id: int
    birth_step: int
    alpha_series: list[float] = field(default_factory=list)
    crowding_series: list[float] = field(default_factory=list)
    wealth_series: list[float] = field(default_factory=list)
    agent_count_series: list[int] = field(default_factory=list)
    t_emerge: Optional[int] = None
    t_peak: Optional[int] = None
    t_half: Optional[int] = None
    t_extinct: Optional[int] = None
    current_phase: str = "exploration"
    is_alive: bool = True
    peak_alpha: float = 0.0


class AlphaTracker:
    """????????? Alpha ?????

    Parameters
    ----------
    window : int
        Alpha ???? Delta????? rolling alpha??
    alpha_thresh : float
        Alpha ?????
    eps_extinct : float
        ???????????????????

    Attributes
    ----------
    families : dict[int, AlphaLifecycle]
        key=ancestor_id, value=???????
    """

    PHASES = ["exploration", "burst", "crowding", "decay", "extinct", "recovery"]

    def __init__(
        self,
        window: int = 60,
        alpha_thresh: float = 0.002,
        eps_extinct: float = 0.0005,
    ) -> None:
        self.window: int = window
        self.alpha_thresh: float = alpha_thresh
        self.eps_extinct: float = eps_extinct
        self.families: dict[int, AlphaLifecycle] = {}

    def update(
        self,
        step: int,
        family_id: int,
        family_return: float,
        crowding: float,
        total_wealth: float,
        agent_count: int,
        total_wealth_all: float,
    ) -> None:
        """????????????????

        Parameters
        ----------
        step : int
            ?????
        family_id : int
            ???????
        family_return : float
            ????????????
        crowding : float
            ??? C_k(t)?
        total_wealth : float
            ??????
        agent_count : int
            ?? agent ???
        total_wealth_all : float
            ?? agent ?????
        """
        if agent_count == 0 or crowding < self.eps_extinct:
            if family_id in self.families:
                self.families[family_id].is_alive = False
                self.families[family_id].current_phase = "extinct"
            return

        if family_id not in self.families:
            self.families[family_id] = AlphaLifecycle(
                family_id=family_id,
                birth_step=step,
            )

        lc = self.families[family_id]
        lc.alpha_series.append(family_return)
        lc.crowding_series.append(crowding)
        lc.wealth_series.append(total_wealth)
        lc.agent_count_series.append(agent_count)
        lc.is_alive = True

        # ???? Alpha
        if len(lc.alpha_series) >= self.window:
            recent = lc.alpha_series[-self.window:]
            avg = sum(recent) / len(recent)
        else:
            avg = sum(lc.alpha_series) / len(lc.alpha_series)

        # ????????????
        self._update_phase(lc, step, abs(avg))
        if lc.peak_alpha < abs(avg):
            lc.peak_alpha = abs(avg)
            lc.t_peak = step

        # ?????
        if lc.t_half is None and lc.peak_alpha > self.alpha_thresh * 2:
            if abs(avg) < lc.peak_alpha / 2:
                lc.t_half = step

    def _update_phase(
        self, lc: AlphaLifecycle, step: int, alpha: float
    ) -> None:
        """???? Alpha ???????????"""
        if lc.is_alive and alpha < self.eps_extinct and len(lc.alpha_series) > self.window:
            lc.current_phase = "extinct"
            lc.is_alive = False
            lc.t_extinct = step
        elif lc.t_peak is None:
            lc.current_phase = "exploration"
        elif alpha > lc.peak_alpha * 0.8:
            lc.current_phase = "burst"
        elif alpha > lc.peak_alpha * 0.3:
            lc.current_phase = "crowding"
        elif alpha > self.eps_extinct:
            lc.current_phase = "decay"
        else:
            lc.current_phase = "extinct"
            lc.is_alive = False

    def get_phase(self, family_id: int) -> str:
        """????????????????

        Returns
        -------
        str
            ????? family_id ?????? "unknown"?
        """
        lc = self.families.get(family_id)
        return lc.current_phase if lc else "unknown"

    def get_active_families(self) -> list[int]:
        """???????????????? ID ???"""
        return [fid for fid, lc in self.families.items() if lc.is_alive]

    def get_alive_count(self) -> int:
        """???????????"""
        return len(self.get_active_families())

    def to_dataframe(self, step: int) -> "pd.DataFrame":
        """??????????? DataFrame?

        Returns
        -------
        pd.DataFrame
            ?: step, family_id, n_agents, total_wealth, wealth_share, alpha, phase?
        """
        import pandas as pd
        rows = []
        for fid, lc in self.families.items():
            n = lc.agent_count_series[-1] if lc.agent_count_series else 0
            tw = lc.wealth_series[-1] if lc.wealth_series else 0.0
            ws = lc.crowding_series[-1] if lc.crowding_series else 0.0
            alpha = (
                sum(lc.alpha_series[-self.window:]) / min(self.window, len(lc.alpha_series))
                if lc.alpha_series else 0.0
            )
            rows.append({
                "step": step,
                "family_id": fid,
                "n_agents": n,
                "total_wealth": tw,
                "wealth_share": ws,
                "alpha": alpha,
                "phase": lc.current_phase,
                "peak_alpha": lc.peak_alpha,
                "t_peak": lc.t_peak if lc.t_peak is not None else -1,
                "t_half": lc.t_half if lc.t_half is not None else -1,
                "birth_step": lc.birth_step,
            })
        return pd.DataFrame(rows)
