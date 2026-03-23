import json
from pathlib import Path
from gen_prompt import parse_rpe

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
