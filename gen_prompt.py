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


def calc_overall_stats(plan, workouts, today=None):
    """Calculate overall adherence, km, longest run, bonus count."""
    if today is None:
        today = date.today()

    # Elapsed planned sessions (exclude rest, null, race)
    elapsed = 0
    planned_km = 0.0
    for week in plan["weeks"]:
        for idx, key in enumerate(DAY_KEYS):
            day = week["days"].get(key)
            if not day or day.get("type") in ("rest", "race"):
                continue
            if session_date(week["start_date"], idx) <= today:
                elapsed += 1
                planned_km += day.get("distance_km", 0)

    # Completed planned sessions
    completed = sum(1 for w in workouts if w.get("planned_week") is not None)

    # Actual km (all running workouts, including bonus)
    km_actual = sum(w.get("distance_km", 0) for w in workouts if w.get("type") in RUNNING_TYPES)

    # Longest run
    running = [w for w in workouts if w.get("type") in RUNNING_TYPES]
    if running:
        longest = max(running, key=lambda w: w.get("distance_km", 0))
        longest_km = longest["distance_km"]
        longest_date = longest["date"]
    else:
        longest_km = 0
        longest_date = None

    # Bonus count
    bonus = sum(1 for w in workouts if w.get("planned_week") is None)

    pct = round(completed / elapsed * 100) if elapsed else 0

    return {
        "adherence_elapsed": elapsed,
        "adherence_completed": completed,
        "adherence_pct": pct,
        "km_planned": planned_km,
        "km_actual": km_actual,
        "longest_run_km": longest_km,
        "longest_run_date": longest_date,
        "bonus_count": bonus,
    }


def calc_weekly_stats(plan, workouts, today=None):
    """Per-week stats for all weeks with at least one elapsed session."""
    if today is None:
        today = date.today()

    results = []
    for week in plan["weeks"]:
        week_id = week["id"]
        # Count elapsed planned sessions in this week
        sessions_planned = 0
        km_planned = 0.0
        rpe_planned_vals = []
        for idx, key in enumerate(DAY_KEYS):
            day = week["days"].get(key)
            if not day or day.get("type") in ("rest", "race"):
                continue
            if session_date(week["start_date"], idx) <= today:
                sessions_planned += 1
                km_planned += day.get("distance_km", 0)
                rpe = parse_rpe(day.get("rpe"))
                if rpe is not None:
                    rpe_planned_vals.append(rpe)

        if sessions_planned == 0:
            continue

        # Workouts logged for this week
        week_workouts = [w for w in workouts if w.get("planned_week") == week_id]
        sessions_done = len(week_workouts)
        km_actual = sum(w.get("distance_km", 0) for w in week_workouts)

        # Pace from running workouts in this week
        run_workouts = [w for w in week_workouts if w.get("type") in RUNNING_TYPES]
        total_dur = sum(w["duration_min"] for w in run_workouts if w.get("duration_min"))
        total_dist = sum(w["distance_km"] for w in run_workouts if w.get("distance_km"))
        pace = format_pace(total_dur, total_dist)

        # RPE
        rpe_actual_vals = [w["rpe"] for w in week_workouts if w.get("rpe") is not None]
        rpe_planned = round(sum(rpe_planned_vals) / len(rpe_planned_vals), 1) if rpe_planned_vals else None
        rpe_actual = round(sum(rpe_actual_vals) / len(rpe_actual_vals), 1) if rpe_actual_vals else None

        results.append({
            "id": week_id,
            "label": week["label"],
            "phase": week["phase"],
            "sessions_planned": sessions_planned,
            "sessions_done": sessions_done,
            "km_planned": km_planned,
            "km_actual": km_actual,
            "pace": pace,
            "rpe_planned": rpe_planned,
            "rpe_actual": rpe_actual,
        })
    return results
