import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rbe_engine.rules import (
    tolerance_check, equipment_status_check, comment_present,
    value_range, duration_check, segregation_of_duties,
)


def test_tolerance_check_in_range():
    step = {"target_value": 100.0, "actual_value": 101.0, "tolerance_pct": 5.0}
    assert tolerance_check(step, {}) is None


def test_tolerance_check_out_of_range():
    step = {"target_value": 100.0, "actual_value": 120.0, "tolerance_pct": 5.0}
    assert tolerance_check(step, {}) is not None


def test_tolerance_check_param_override_wins():
    step = {"target_value": 100.0, "actual_value": 103.0, "tolerance_pct": 5.0}
    # step's own 5% would pass 103, but a tighter 2% override should trip it
    assert tolerance_check(step, {"tolerance_pct": 2.0}) is not None


def test_equipment_status_check():
    assert equipment_status_check({"equipment_status": "AVAILABLE"}, {}) is None
    assert equipment_status_check({"equipment_status": "DOWN"}, {}) is not None


def test_comment_present():
    assert comment_present({"comment": None}, {}) is None
    assert comment_present({"comment": "something happened"}, {}) is not None


def test_value_range():
    params = {"tag": "UV280", "min": 0.0, "max": 2.5}
    assert value_range({"tags": {"UV280": 1.0}}, params) is None
    assert value_range({"tags": {"UV280": 3.0}}, params) is not None
    assert value_range({"tags": {}}, params) is None  # tag absent -> no opinion


def test_duration_check():
    params = {"max_minutes": 60}
    ok_step = {"start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T00:30:00Z"}
    bad_step = {"start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T02:00:00Z"}
    assert duration_check(ok_step, params) is None
    assert duration_check(bad_step, params) is not None


def test_segregation_of_duties():
    assert segregation_of_duties({"performed_by": "a", "reviewed_by": "b"}, {}) is None
    assert segregation_of_duties({"performed_by": "a", "reviewed_by": "a"}, {}) is not None
