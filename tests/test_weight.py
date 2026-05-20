from datetime import datetime, timedelta, timezone

from memoir.config import MemoirConfig
from memoir.core.weight import (
    decay_schedule,
    compute_decay,
    compute_boost,
)


class TestDecaySchedule:
    def test_default_schedule(self):
        config = MemoirConfig()
        sched = decay_schedule(config)
        assert sched[5] == (None, None)  # Never decays
        assert sched[4] == (60, 3)
        assert sched[3] == (30, 2)
        assert sched[2] == (60, 1)
        assert sched[1] == (90, "archive")

    def test_custom_schedule(self):
        config = MemoirConfig()
        config.weight.decay[4] = config.weight.decay[4].model_copy(
            update={"days": 30, "to": 2}
        )
        sched = decay_schedule(config)
        assert sched[4] == (30, 2)


class TestComputeDecay:
    def test_weight_5_never_decays(self, default_config):
        fm = {"weight": 5, "last_triggered": "2020-01-01T00:00:00"}
        result = compute_decay(fm, config=default_config)
        assert result is None

    def test_weight_4_decays_after_60_days(self, default_config):
        old = datetime.now(timezone.utc) - timedelta(days=61)
        fm = {"weight": 4, "last_triggered": old.isoformat()}
        result = compute_decay(fm, config=default_config)
        assert result == 3

    def test_weight_4_no_decay_before_threshold(self, default_config):
        recent = datetime.now(timezone.utc) - timedelta(days=30)
        fm = {"weight": 4, "last_triggered": recent.isoformat()}
        result = compute_decay(fm, config=default_config)
        assert result is None

    def test_weight_3_decays_after_30_days(self, default_config):
        old = datetime.now(timezone.utc) - timedelta(days=31)
        fm = {"weight": 3, "last_triggered": old.isoformat()}
        result = compute_decay(fm, config=default_config)
        assert result == 2

    def test_weight_1_archives_after_90_days(self, default_config):
        old = datetime.now(timezone.utc) - timedelta(days=91)
        fm = {"weight": 1, "last_triggered": old.isoformat()}
        result = compute_decay(fm, config=default_config)
        assert result == "archive"

    def test_no_timestamp_returns_none(self, default_config):
        fm = {"weight": 3}
        result = compute_decay(fm, config=default_config)
        assert result is None

    def test_fallback_to_updated(self, default_config):
        old = datetime.now(timezone.utc) - timedelta(days=35)
        fm = {"weight": 3, "updated": old.isoformat()}
        result = compute_decay(fm, config=default_config)
        assert result == 2


class TestComputeBoost:
    def test_no_boost_below_threshold(self, default_config):
        fm = {"weight": 3, "trigger_count": 2}
        result = compute_boost(fm, default_config)
        assert result == 3

    def test_boost_at_threshold_5(self, default_config):
        fm = {"weight": 3, "trigger_count": 5}
        result = compute_boost(fm, default_config)
        assert result == 4

    def test_double_boost_at_15(self, default_config):
        fm = {"weight": 3, "trigger_count": 15}
        result = compute_boost(fm, default_config)
        assert result == 5

    def test_capped_at_5(self, default_config):
        fm = {"weight": 4, "trigger_count": 30}
        result = compute_boost(fm, default_config)
        assert result == 5
