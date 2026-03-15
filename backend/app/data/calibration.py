"""Data calibration — uses public dataset distributions to parameterize generators.

All datasets are optional. If not available, hardcoded defaults are used.
This bridges the synthetic generator path and the PaySim path by providing
statistically grounded parameters from real-world datasets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Distribution:
    """Log-normal distribution parameters."""
    mu: float = 3.5
    sigma: float = 1.2
    min_val: float = 1.0
    max_val: float = 50_000.0


@dataclass
class DemographicParams:
    """Demographic profile from Feedzai BAF data."""
    income_range: tuple[float, float] = (30_000.0, 80_000.0)
    employment_rate: float = 0.65
    avg_daily_transactions: float = 1.5
    fraud_prevalence: float = 0.012


@dataclass
class CalibrationResult:
    """Complete calibration output for the generators."""
    amount_distributions: dict[str, Distribution] = field(default_factory=dict)
    demographic_profiles: dict[str, DemographicParams] = field(default_factory=dict)
    timing_weights: list[float] = field(default_factory=list)
    chat_templates: dict[str, list[str]] = field(default_factory=dict)


_DEFAULT_AMOUNT_DISTRIBUTIONS: dict[str, Distribution] = {
    "grocery": Distribution(mu=3.2, sigma=0.8, min_val=2.0, max_val=500.0),
    "pharmacy": Distribution(mu=2.8, sigma=0.6, min_val=5.0, max_val=200.0),
    "restaurant": Distribution(mu=3.0, sigma=0.7, min_val=5.0, max_val=300.0),
    "online_retail": Distribution(mu=3.5, sigma=1.3, min_val=1.0, max_val=5000.0),
    "utility": Distribution(mu=4.2, sigma=0.5, min_val=20.0, max_val=500.0),
    "transfer": Distribution(mu=5.5, sigma=1.8, min_val=10.0, max_val=50000.0),
    "default": Distribution(mu=3.5, sigma=1.2, min_val=1.0, max_val=50000.0),
}

_DEFAULT_DEMOGRAPHIC_PROFILES: dict[str, DemographicParams] = {
    "18-25": DemographicParams(
        income_range=(15_000, 40_000), employment_rate=0.55,
        avg_daily_transactions=1.8, fraud_prevalence=0.018,
    ),
    "26-35": DemographicParams(
        income_range=(35_000, 85_000), employment_rate=0.82,
        avg_daily_transactions=2.2, fraud_prevalence=0.015,
    ),
    "36-50": DemographicParams(
        income_range=(50_000, 120_000), employment_rate=0.88,
        avg_daily_transactions=2.5, fraud_prevalence=0.010,
    ),
    "51-65": DemographicParams(
        income_range=(45_000, 100_000), employment_rate=0.75,
        avg_daily_transactions=1.5, fraud_prevalence=0.008,
    ),
    "66+": DemographicParams(
        income_range=(25_000, 60_000), employment_rate=0.15,
        avg_daily_transactions=0.8, fraud_prevalence=0.020,
    ),
}

_DEFAULT_TIMING_WEIGHTS = [
    0.01, 0.01, 0.01, 0.01, 0.01, 0.02,  # 0-5
    0.03, 0.05, 0.07, 0.08, 0.08, 0.07,  # 6-11
    0.08, 0.07, 0.06, 0.06, 0.05, 0.05,  # 12-17
    0.05, 0.04, 0.03, 0.03, 0.02, 0.01,  # 18-23
]


class DataCalibrator:
    """Calibrates generator parameters from public datasets.

    Falls back to hardcoded defaults if dataset files are not present.
    """

    def __init__(
        self,
        ieee_path: str | Path | None = None,
        baf_path: str | Path | None = None,
        paysim_path: str | Path | None = None,
    ) -> None:
        self._ieee_path = Path(ieee_path) if ieee_path else None
        self._baf_path = Path(baf_path) if baf_path else None
        self._paysim_path = Path(paysim_path) if paysim_path else None

        self._amount_dists: dict[str, Distribution] = dict(_DEFAULT_AMOUNT_DISTRIBUTIONS)
        self._demographics: dict[str, DemographicParams] = dict(_DEFAULT_DEMOGRAPHIC_PROFILES)
        self._timing: list[float] = list(_DEFAULT_TIMING_WEIGHTS)
        self._chat_templates: dict[str, list[str]] = {}

        self._calibrated = False

    def calibrate(self) -> CalibrationResult:
        """Run calibration from available datasets, filling gaps with defaults."""
        if self._ieee_path and self._ieee_path.exists():
            self._calibrate_from_ieee()

        if self._baf_path and self._baf_path.exists():
            self._calibrate_from_baf()

        if self._paysim_path and self._paysim_path.exists():
            self._calibrate_from_paysim()

        self._calibrated = True
        return CalibrationResult(
            amount_distributions=self._amount_dists,
            demographic_profiles=self._demographics,
            timing_weights=self._timing,
            chat_templates=self._chat_templates,
        )

    def get_amount_distribution(self, merchant_category: str) -> Distribution:
        if not self._calibrated:
            self.calibrate()
        return self._amount_dists.get(
            merchant_category, self._amount_dists["default"]
        )

    def get_demographic_profile(self, age_group: str) -> DemographicParams:
        if not self._calibrated:
            self.calibrate()
        return self._demographics.get(
            age_group, DemographicParams()
        )

    def get_timing_weights(self) -> list[float]:
        if not self._calibrated:
            self.calibrate()
        return self._timing

    def get_chat_template(self, persona_type: str, intent: str) -> str | None:
        if not self._calibrated:
            self.calibrate()
        key = f"{persona_type}:{intent}"
        templates = self._chat_templates.get(key, [])
        return templates[0] if templates else None

    def sample_amount(self, merchant_category: str, rng: Any = None) -> float:
        """Sample a transaction amount from the calibrated distribution."""
        dist = self.get_amount_distribution(merchant_category)
        import random as _random
        r = rng if rng else _random
        raw = r.gauss(dist.mu, dist.sigma)
        amount = math.exp(raw)
        return max(dist.min_val, min(dist.max_val, round(amount, 2)))

    def _calibrate_from_ieee(self) -> None:
        """Extract amount distributions from IEEE-CIS dataset."""
        try:
            from app.datasets.ieee_cis import extract_distributions
            dists = extract_distributions(self._ieee_path)
            self._amount_dists.update(dists)
        except (ImportError, Exception):
            pass

    def _calibrate_from_baf(self) -> None:
        """Extract demographic profiles from Feedzai BAF dataset."""
        try:
            from app.datasets.feedzai_baf import extract_demographics
            demos = extract_demographics(self._baf_path)
            self._demographics.update(demos)
        except (ImportError, Exception):
            pass

    def _calibrate_from_paysim(self) -> None:
        """Extract timing distributions from PaySim data."""
        try:
            from app.datasets.ieee_cis import extract_timing
            timing = extract_timing(self._paysim_path)
            if len(timing) == 24:
                self._timing = timing
        except (ImportError, Exception):
            pass
