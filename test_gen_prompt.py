import json
import pytest
from pathlib import Path
from gen_prompt import parse_rpe


@pytest.fixture
def sample_plan():
    return json.loads((Path(__file__).parent / "plan.json").read_text())

@pytest.fixture
def sample_workouts():
    return json.loads((Path(__file__).parent / "workouts.json").read_text())

def test_parse_rpe_range():
    assert parse_rpe("3-4") == 3.5

def test_parse_rpe_single():
    assert parse_rpe("3") == 3.0

def test_parse_rpe_int():
    assert parse_rpe(5) == 5.0

def test_parse_rpe_none():
    assert parse_rpe(None) is None


from gen_prompt import session_date
from datetime import date

def test_session_date_monday():
    # start_date is Monday 2026-03-16, idx 0 (mon) -> March 16
    assert session_date("2026-03-16", 0) == date(2026, 3, 16)

def test_session_date_thursday():
    # start_date is Monday 2026-03-16, idx 3 (thu) -> March 19
    assert session_date("2026-03-16", 3) == date(2026, 3, 19)

def test_session_date_sunday():
    # start_date is Monday 2026-03-16, idx 6 (sun) -> March 22
    assert session_date("2026-03-16", 6) == date(2026, 3, 22)


from gen_prompt import format_pace

def test_format_pace():
    # 22 min / 3 km = 7.333 min/km = 7:20
    assert format_pace(22, 3.0) == "7:20"

def test_format_pace_even():
    # 30 min / 5 km = 6.0 min/km = 6:00
    assert format_pace(30, 5.0) == "6:00"

def test_format_pace_zero_distance():
    assert format_pace(30, 0) is None


from gen_prompt import calc_overall_stats

def test_overall_stats_intro_week_complete(sample_plan, sample_workouts):
    """With today=2026-03-23, intro week is fully elapsed (thu+sun passed)."""
    stats = calc_overall_stats(sample_plan, sample_workouts, today=date(2026, 3, 23))
    assert stats["adherence_completed"] == 2
    assert stats["adherence_elapsed"] == 2
    assert stats["adherence_pct"] == 100
    assert stats["km_actual"] == 7.0  # 3.0 + 4.0
    assert stats["km_planned"] == 7.0  # 3 + 4
    assert stats["longest_run_km"] == 4.0
    assert stats["longest_run_date"] == "2026-03-22"
    assert stats["bonus_count"] == 1  # gym bonus

def test_overall_stats_no_workouts(sample_plan):
    stats = calc_overall_stats(sample_plan, [], today=date(2026, 3, 23))
    assert stats["adherence_completed"] == 0
    assert stats["adherence_elapsed"] == 2
    assert stats["adherence_pct"] == 0
    assert stats["km_actual"] == 0
    assert stats["longest_run_km"] == 0


from gen_prompt import calc_weekly_stats

def test_weekly_stats_intro(sample_plan, sample_workouts):
    """Intro week should show 2/2 sessions, correct km, pace, RPE."""
    weeks = calc_weekly_stats(sample_plan, sample_workouts, today=date(2026, 3, 23))
    assert len(weeks) == 1  # only intro is elapsed
    intro = weeks[0]
    assert intro["label"] == "Introvecka"
    assert intro["sessions_done"] == 2
    assert intro["sessions_planned"] == 2
    assert intro["km_planned"] == 7.0
    assert intro["km_actual"] == 7.0
    assert intro["pace"] is not None  # should have a pace string
    assert intro["rpe_planned"] is not None
    assert intro["rpe_actual"] is not None
