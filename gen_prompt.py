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


def calc_trends(weekly_stats):
    """Compute trends from weekly stats. Returns None if < 2 weeks."""
    if len(weekly_stats) < 2:
        return None
    paces = [w["pace"] for w in weekly_stats if w["pace"]]
    rpe_deltas = []
    km_devs = []
    for w in weekly_stats:
        if w["rpe_actual"] is not None and w["rpe_planned"] is not None:
            rpe_deltas.append(round(w["rpe_actual"] - w["rpe_planned"], 1))
        if w["km_planned"] > 0:
            dev = round((w["km_actual"] - w["km_planned"]) / w["km_planned"] * 100)
            km_devs.append(dev)
    return {"paces": paces, "rpe_deltas": rpe_deltas, "km_devs": km_devs}


def gym_summary(workouts):
    """Summarize gym workouts. Returns dict with count and formatted exercises."""
    gym_workouts = [w for w in workouts if w.get("type") == "gym"]
    exercises = []
    for w in gym_workouts:
        for ex in w.get("exercises", []):
            sets = ex.get("sets", [])
            if not sets:
                continue
            reps = sets[0].get("reps", "?")
            kg = sets[0].get("kg", "?")
            exercises.append(f"{ex['name']}: {len(sets)}×{reps} @ {kg} kg")
    return {"count": len(gym_workouts), "exercises": exercises}


def upcoming_sessions(plan, today=None):
    """Extract planned sessions for the next 7 days."""
    if today is None:
        today = date.today()
    end = today + timedelta(days=6)
    sv_days = {"mon": "mån", "tue": "tis", "wed": "ons", "thu": "tor", "fri": "fre", "sat": "lör", "sun": "sön"}
    sv_months = {1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "maj", 6: "jun",
                 7: "jul", 8: "aug", 9: "sep", 10: "okt", 11: "nov", 12: "dec"}
    results = []
    for week in plan["weeks"]:
        for idx, key in enumerate(DAY_KEYS):
            day = week["days"].get(key)
            if not day or day.get("type") == "rest":
                continue
            d = session_date(week["start_date"], idx)
            if today <= d <= end:
                label = f"{sv_days[key]} {d.day} {sv_months[d.month]}"
                results.append({
                    "day": label,
                    "type": day["type"],
                    "description": day.get("description", ""),
                })
    # No sort needed — weeks are chronological and day keys are mon-sun
    return results


def current_week_info(plan, today=None):
    """Find current week label and phase."""
    if today is None:
        today = date.today()
    for week in plan["weeks"]:
        start = session_date(week["start_date"], 0)
        end = start + timedelta(days=6)
        if start <= today <= end:
            return week["label"], week["phase"]
    return None, None


def build_prompt(plan, workouts, free_question=None, today=None):
    """Assemble the full prompt string."""
    if today is None:
        today = date.today()

    race_date = date.fromisoformat(plan["race"]["date"])
    days_left = (race_date - today).days
    week_label, week_phase = current_week_info(plan, today)
    overall = calc_overall_stats(plan, workouts, today)
    weekly = calc_weekly_stats(plan, workouts, today)
    trends = calc_trends(weekly)
    gym = gym_summary(workouts)
    upcoming = upcoming_sessions(plan, today)

    lines = []

    # 1. System role
    lines.append("Du är en erfaren löpcoach. Nedan finns min träningsdata med förberäknad statistik.")
    lines.append("Analysera hur det går och ge mig konkret feedback.\n")

    # 2. Om mig
    lines.append("## Om mig")
    lines.append("- Nybörjarlöpare, första halvmaran")
    lines.append("- Mål: jogga hela Göteborgsvarvet (21,1 km, 23 maj 2026) utan gångpauser")
    lines.append("- Gymträning 2×/vecka parallellt med löpningen")
    lines.append(f"- Dagens datum: {today}")
    if week_label:
        lines.append(f"- Aktuell vecka: {week_label} ({week_phase})")
    lines.append(f"- Dagar till lopp: {days_left}\n")

    # 3. Sammanfattning
    lines.append("## Sammanfattning")
    if not workouts:
        lines.append("Inga loggade pass ännu.\n")
    else:
        lines.append(f"- Följsamhet: {overall['adherence_completed']}/{overall['adherence_elapsed']} planerade pass ({overall['adherence_pct']}%)")
        lines.append(f"- Km löpt: {overall['km_actual']} av {overall['km_planned']} km planerat")
        if overall["longest_run_km"]:
            lines.append(f"- Längsta löppass: {overall['longest_run_km']} km ({overall['longest_run_date']}) — mål: 21,1 km")
        if overall["bonus_count"]:
            lines.append(f"- Bonuspass (utanför plan): {overall['bonus_count']}")
        lines.append("")

        # Per-week table
        if weekly:
            lines.append("### Per vecka")
            lines.append("| Vecka | Fas | Pass | Km plan | Km faktisk | Tempo | RPE plan | RPE faktisk |")
            lines.append("|-------|-----|------|---------|------------|-------|----------|-------------|")
            for w in weekly:
                lines.append(
                    f"| {w['label']} | {w['phase']} | {w['sessions_done']}/{w['sessions_planned']} "
                    f"| {w['km_planned']} | {w['km_actual']} | {w['pace'] or '—'} "
                    f"| {w['rpe_planned'] or '—'} | {w['rpe_actual'] or '—'} |"
                )
            lines.append("")

        # Trends
        if trends:
            lines.append("### Trender")
            if trends["paces"]:
                lines.append(f"- Tempo vecka för vecka: {', '.join(trends['paces'])} min/km")
            if trends["rpe_deltas"]:
                deltas = ", ".join(f"{d:+.1f}" for d in trends["rpe_deltas"])
                lines.append(f"- RPE-delta (faktisk − planerad): {deltas}")
            if trends["km_devs"]:
                devs = ", ".join(f"{d:+d}%" for d in trends["km_devs"])
                lines.append(f"- Km-avvikelse: {devs}")
            lines.append("")

        # Gym
        if gym["count"]:
            lines.append("### Gym")
            lines.append(f"- Genomförda gympass: {gym['count']}")
            for ex in gym["exercises"]:
                lines.append(f"  - {ex}")
            lines.append("")

    # 4. Fri fråga
    if free_question:
        lines.append("## Min fråga (prioriterad)")
        lines.append(f"{free_question}\n")

    # 5. Kommande pass
    if upcoming:
        lines.append("## Kommande pass (nästa 7 dagar)")
        for s in upcoming:
            lines.append(f"- **{s['day']}**: {s['description']} ({s['type']})")
        lines.append("")

    # 6. Instruktioner
    lines.append("## Vad jag vill ha")
    if free_question:
        lines.append("Adressera min fråga först, ge sedan den vanliga analysen.\n")
    lines.append("1. **Följsamhet** — hur väl följer jag planen? Missade pass, avvikelser?")
    lines.append("2. **Tempo/distans** — avviker mina faktiska resultat (km, tid, RPE) mycket från planen?")
    lines.append("3. **Belastning** — ser du risk för överträning eller underträning?")
    lines.append("4. **Rekommendation** — konkreta justeringar för kommande vecka, om några behövs.")
    lines.append("5. **Gym** — kommentar på gympass om det finns loggade sådana.")
    lines.append("\nSvara på svenska. Var rak och konkret — ingen fluff.\n")

    # 7. Rådata
    lines.append("## Rådata")
    lines.append("<details><summary>plan.json</summary>\n")
    lines.append("```json")
    lines.append(json.dumps(plan, ensure_ascii=False, indent=2))
    lines.append("```\n</details>\n")
    lines.append("<details><summary>workouts.json</summary>\n")
    lines.append("```json")
    lines.append(json.dumps(workouts, ensure_ascii=False, indent=2))
    lines.append("```\n</details>")

    return "\n".join(lines)


def main():
    plan, workouts = load_data()
    free_question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    print(build_prompt(plan, workouts, free_question))


if __name__ == "__main__":
    main()
