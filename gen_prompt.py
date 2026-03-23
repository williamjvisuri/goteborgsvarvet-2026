#!/usr/bin/env python3
"""Generate an AI coaching prompt from plan.json + workouts.json."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
RUNNING_TYPES = {"running", "long_run", "tempo"}


def load_data():
    plan = json.loads((HERE / "plan.json").read_text())
    workouts = json.loads((HERE / "workouts.json").read_text())
    return plan, workouts


def parse_rpe(val):
    """Parse RPE from plan (string like '3-4') or workout (int). Returns float or None."""
    if val is None:
        return None
    s = str(val)
    if "-" in s:
        parts = s.split("-")
        return (float(parts[0]) + float(parts[1])) / 2
    return float(s)


def session_date(start_date_str, day_idx):
    """Calendar date for a day-key index within a week."""
    y, m, d = map(int, start_date_str.split("-"))
    return date(y, m, d) + timedelta(days=day_idx)


def format_pace(duration_min, distance_km):
    """Format pace as 'M:SS'. Returns None if distance is zero."""
    if not distance_km:
        return None
    pace = duration_min / distance_km
    mins = int(pace)
    secs = int(round((pace - mins) * 60))
    if secs == 60:
        mins += 1
        secs = 0
    return f"{mins}:{secs:02d}"
