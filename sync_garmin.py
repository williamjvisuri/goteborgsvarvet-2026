#!/usr/bin/env python3
"""
sync_garmin.py — Synka löppass från Garmin Connect till workouts.json

Läser GARMIN_EMAIL och GARMIN_PASSWORD från miljövariabler.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

RUNNING_TYPES = {"running", "long_run", "tempo"}
GARMIN_RUNNING_TYPES = {"running", "trail_running"}

SCRIPT_DIR = Path(__file__).parent.resolve()
WORKOUTS_FILE = SCRIPT_DIR / "workouts.json"
PLAN_FILE = SCRIPT_DIR / "plan.json"

# Maps Python weekday() (0=Monday) to plan.json day keys
WEEKDAY_TO_KEY = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def format_pace_from_speed(speed_ms):
    """Convert m/s to 'M:SS' min/km pace. Returns None if speed is zero/None."""
    if not speed_ms:
        return None
    pace = (1000 / speed_ms) / 60
    mins = int(pace)
    secs = int(round((pace - mins) * 60))
    if secs == 60:
        mins += 1
        secs = 0
    return f"{mins}:{secs:02d}"


def estimate_rpe(avg_hr):
    """Uppskattar RPE från genomsnittspuls."""
    if avg_hr is None:
        return None
    if avg_hr < 130:
        return 3
    elif avg_hr < 145:
        return 4
    elif avg_hr < 160:
        return 5
    elif avg_hr < 175:
        return 6
    else:
        return 7


def match_plan(activity_date_str, plan):
    """Matchar ett aktivitetsdatum mot träningsplanen.

    Returnerar (planned_week, planned_day, session_type) eller (None, None, None).
    """
    activity_date = datetime.strptime(activity_date_str, "%Y-%m-%d").date()
    # Day key comes from actual calendar day, not offset from week start_date,
    # because weeks in plan.json do not always start on Monday.
    day_key = WEEKDAY_TO_KEY[activity_date.weekday()]

    for week in plan.get("weeks", []):
        start = datetime.strptime(week["start_date"], "%Y-%m-%d").date()
        end = start + timedelta(days=6)

        if start <= activity_date <= end:
            planned_day = week.get("days", {}).get(day_key)

            if planned_day and planned_day.get("type") in RUNNING_TYPES:
                return week["id"], day_key, planned_day["type"]
            else:
                return None, None, None

    return None, None, None


def build_dedup_set(workouts):
    """Bygger ett set av (date, type) för befintliga löppass."""
    seen = set()
    for w in workouts:
        if w.get("type") in RUNNING_TYPES:
            seen.add(w["date"])
    return seen


def garmin_activity_to_entry(activity, plan):
    """Konverterar ett Garmin-aktivitetsobjekt till ett workouts.json-inlägg."""
    start_time = activity.get("startTimeLocal", "")
    activity_date = start_time[:10] if start_time else None
    if not activity_date:
        return None

    distance_m = activity.get("distance") or 0
    distance_km = round(distance_m / 1000, 1)

    duration_s = activity.get("duration") or 0
    duration_min = round(duration_s / 60)

    avg_hr = activity.get("averageHR")
    rpe = estimate_rpe(avg_hr)

    planned_week, planned_day, plan_type = match_plan(activity_date, plan)
    activity_type = plan_type if plan_type in RUNNING_TYPES else "running"

    note = activity.get("activityName", "")

    # Enriched fields from activity summary
    max_hr = activity.get("maxHR")
    avg_speed = activity.get("averageSpeed")
    avg_pace = format_pace_from_speed(avg_speed)
    avg_cadence = activity.get("averageRunningCadenceInStepsPerMinute")
    if avg_cadence is not None:
        avg_cadence = round(avg_cadence)
    max_cadence = activity.get("maxRunningCadenceInStepsPerMinute")
    if max_cadence is not None:
        max_cadence = round(max_cadence)
    elevation_gain = activity.get("elevationGain")
    if elevation_gain is not None:
        elevation_gain = round(elevation_gain)
    elevation_loss = activity.get("elevationLoss")
    if elevation_loss is not None:
        elevation_loss = round(elevation_loss)
    aerobic_te = activity.get("aerobicTrainingEffect")
    anaerobic_te = activity.get("anaerobicTrainingEffect")
    training_load = activity.get("activityTrainingLoad")
    if training_load is not None:
        training_load = round(training_load)
    vo2max = activity.get("vO2MaxValue")
    calories = activity.get("calories")
    if calories is not None:
        calories = round(calories)
    activity_id = activity.get("activityId")

    return {
        "date": activity_date,
        "planned_week": planned_week,
        "planned_day": planned_day,
        "type": activity_type,
        "activity_id": activity_id,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "rpe": rpe,
        "avg_hr": round(avg_hr) if avg_hr is not None else None,
        "max_hr": round(max_hr) if max_hr is not None else None,
        "avg_pace": avg_pace,
        "avg_cadence": avg_cadence,
        "max_cadence": max_cadence,
        "elevation_gain": elevation_gain,
        "elevation_loss": elevation_loss,
        "aerobic_te": aerobic_te,
        "anaerobic_te": anaerobic_te,
        "training_load": training_load,
        "vo2max": vo2max,
        "calories": calories,
        "hr_zones": None,
        "splits": None,
        "note": note,
    }


def login_garmin(email, password):
    """Loggar in på Garmin Connect och returnerar klienten."""
    try:
        import garminconnect
    except ImportError:
        print("Fel: garminconnect-paketet är inte installerat.", file=sys.stderr)
        print("Kör: pip install garminconnect", file=sys.stderr)
        sys.exit(1)

    try:
        client = garminconnect.Garmin(email, password)
        client.login()
        return client
    except garminconnect.GarminConnectAuthenticationError:
        print(
            "Fel: Kunde inte logga in. Kontrollera GARMIN_EMAIL och GARMIN_PASSWORD.",
            file=sys.stderr,
        )
        sys.exit(1)
    except garminconnect.GarminConnectConnectionError:
        print(
            "Fel: Kunde inte ansluta till Garmin Connect. Kontrollera din internetanslutning.",
            file=sys.stderr,
        )
        sys.exit(1)
    except garminconnect.GarminConnectTooManyRequestsError:
        print(
            "Fel: För många förfrågningar till Garmin Connect. Försök igen senare.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        # Fånga MFA/TOTP-fel och övriga oväntade fel
        msg = str(e).lower()
        if "mfa" in msg or "totp" in msg or "2fa" in msg or "factor" in msg:
            print(
                "Fel: Garmin kräver tvåfaktorsautentisering (MFA/TOTP). "
                "Kontrollera att garminconnect-biblioteket stöder din konfiguration.",
                file=sys.stderr,
            )
        else:
            print(f"Fel vid inloggning: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_activities(client, days):
    """Hämtar aktiviteter från Garmin Connect för de senaste N dagarna."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    try:
        activities = client.get_activities_by_date(
            start_date.isoformat(), end_date.isoformat()
        )
        return activities or []
    except Exception as e:
        print(
            f"Fel: Kunde inte hämta aktiviteter från Garmin Connect: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def filter_running(activities):
    """Filtrerar och behåller bara löpaktiviteter."""
    result = []
    for a in activities:
        type_key = (
            a.get("activityType", {}).get("typeKey", "")
            if isinstance(a.get("activityType"), dict)
            else ""
        )
        if type_key in GARMIN_RUNNING_TYPES:
            result.append(a)
    return result


def fetch_hr_zones(client, activity_id):
    """Hämtar HR-zoner för en aktivitet. Returnerar lista eller None vid fel."""
    try:
        data = client.get_activity_hr_in_timezones(activity_id)
        if not data:
            return None
        zones = []
        for z in data:
            zones.append({
                "zone": z.get("zoneNumber"),
                "seconds": round(z.get("secsInZone", 0)),
            })
        return zones if zones else None
    except Exception:
        return None


def fetch_splits(client, activity_id):
    """Hämtar per-km splits för en aktivitet. Returnerar lista eller None vid fel."""
    try:
        data = client.get_activity_splits(activity_id)
        laps = data.get("lapDTOs", []) if isinstance(data, dict) else []
        if not laps:
            return None
        splits = []
        for i, lap in enumerate(laps, 1):
            avg_speed = lap.get("averageSpeed")
            pace = format_pace_from_speed(avg_speed)
            avg_hr = lap.get("averageHR")
            splits.append({
                "km": i,
                "pace": pace,
                "avg_hr": round(avg_hr) if avg_hr is not None else None,
            })
        return splits if splits else None
    except Exception:
        return None


def enrich_entry_details(client, entry):
    """Hämtar HR-zoner och splits för en entry. Modifierar entry in-place."""
    activity_id = entry.get("activity_id")
    if not activity_id:
        return
    entry["hr_zones"] = fetch_hr_zones(client, activity_id)
    entry["splits"] = fetch_splits(client, activity_id)


def print_summary(new_entries):
    """Skriver ut en sammanfattning av nya pass."""
    print(f"\n{'─'*50}")
    print(f"  Hittade {len(new_entries)} nytt/nya löppass att importera:")
    print(f"{'─'*50}")
    for i, e in enumerate(new_entries, 1):
        plan_info = ""
        if e["planned_week"]:
            plan_info = f"  → Planerat: {e['planned_week']} / {e['planned_day']}"
        rpe_str = str(e["rpe"]) if e["rpe"] is not None else "–"
        print(
            f"\n  {i}. {e['date']}  {e['type'].upper()}  "
            f"{e['distance_km']} km  {e['duration_min']} min  RPE {rpe_str}"
        )
        print(f"     \"{e['note']}\"")
        if plan_info:
            print(f"     {plan_info}")
    print(f"\n{'─'*50}")


def ask_confirmation():
    """Frågar användaren om de vill importera passen."""
    while True:
        answer = input("Importera dessa pass till workouts.json? [j/n]: ").strip().lower()
        if answer in ("j", "ja", "y", "yes"):
            return True
        elif answer in ("n", "nej", "no"):
            return False
        print("Ange j eller n.")


def git_push(new_entries):
    """Kör git add, commit och push."""
    count = len(new_entries)
    dates = ", ".join(e["date"] for e in new_entries)
    commit_msg = f"Lägg till {count} löppass från Garmin ({dates})"

    cmds = [
        ["git", "-C", str(SCRIPT_DIR), "add", "workouts.json"],
        ["git", "-C", str(SCRIPT_DIR), "commit", "-m", commit_msg],
        ["git", "-C", str(SCRIPT_DIR), "push"],
    ]

    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Fel vid git-kommando: {' '.join(cmd)}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False
    print(f"\nGit: Commit och push klar!")
    return True


def load_dotenv():
    """Läser .env-fil från samma katalog som skriptet, om den finns."""
    env_file = SCRIPT_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Synkronisera löppass från Garmin Connect till workouts.json"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        metavar="N",
        help="Antal dagar bakåt att hämta (standard: 7)",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Kör git add, commit och push automatiskt efter sparning",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Hoppa över bekräftelsefrågan och importera direkt",
    )
    args = parser.parse_args()

    # Läs miljövariabler
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    missing = []
    if not email:
        missing.append("GARMIN_EMAIL")
    if not password:
        missing.append("GARMIN_PASSWORD")
    if missing:
        print(
            f"Fel: Följande miljövariabler saknas: {', '.join(missing)}",
            file=sys.stderr,
        )
        print("Sätt dem med: export GARMIN_EMAIL=... GARMIN_PASSWORD=...", file=sys.stderr)
        sys.exit(1)

    # Läs befintlig data
    workouts = []
    if WORKOUTS_FILE.exists():
        try:
            with open(WORKOUTS_FILE, encoding="utf-8") as f:
                workouts = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Fel: Kunde inte läsa {WORKOUTS_FILE}: {e}", file=sys.stderr)
            sys.exit(1)

    plan = {}
    if PLAN_FILE.exists():
        try:
            with open(PLAN_FILE, encoding="utf-8") as f:
                plan = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Fel: Kunde inte läsa {PLAN_FILE}: {e}", file=sys.stderr)
            sys.exit(1)

    # Logga in och hämta aktiviteter
    print(f"Loggar in på Garmin Connect som {email}...")
    client = login_garmin(email, password)
    print(f"Inloggad! Hämtar aktiviteter de senaste {args.days} dagarna...")

    activities = fetch_activities(client, args.days)
    running_activities = filter_running(activities)

    print(
        f"Hittade {len(running_activities)} löpaktivitet(er) av totalt {len(activities)} aktiviteter."
    )

    if not running_activities:
        print(f"\nInga nya löppass hittade de senaste {args.days} dagarna.")
        sys.exit(0)

    # Deduplicera
    existing_dates = build_dedup_set(workouts)
    new_entries = []
    skipped = 0

    for activity in running_activities:
        entry = garmin_activity_to_entry(activity, plan)
        if entry is None:
            continue
        if entry["date"] in existing_dates:
            skipped += 1
            continue
        new_entries.append(entry)

    if skipped:
        print(f"Hoppar över {skipped} aktivitet(er) som redan finns i workouts.json.")

    if not new_entries:
        print(f"\nInga nya löppass hittade de senaste {args.days} dagarna.")
        sys.exit(0)

    # Hämta detaljdata (HR-zoner, splits) per aktivitet
    print(f"Hämtar detaljdata för {len(new_entries)} aktivitet(er)...")
    for i, entry in enumerate(new_entries):
        enrich_entry_details(client, entry)
        if i < len(new_entries) - 1:
            time.sleep(1)

    # Visa sammanfattning och fråga
    print_summary(new_entries)

    if not args.yes:
        confirmed = ask_confirmation()
        if not confirmed:
            print("Importering avbruten.")
            sys.exit(0)

    # Sortera nya inlägg efter datum och lägg till
    new_entries.sort(key=lambda e: e["date"])
    workouts.extend(new_entries)

    # Skriv till workouts.json
    try:
        with open(WORKOUTS_FILE, "w", encoding="utf-8") as f:
            json.dump(workouts, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"\n{len(new_entries)} pass sparade i workouts.json.")
    except OSError as e:
        print(f"Fel: Kunde inte skriva till {WORKOUTS_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    # Git push eller instruktioner
    if args.push:
        git_push(new_entries)
    else:
        dates_str = ", ".join(e["date"] for e in new_entries)
        print("\nKör följande för att committa:")
        print(f'  git add workouts.json')
        print(f'  git commit -m "Lägg till {len(new_entries)} löppass från Garmin ({dates_str})"')
        print(f'  git push')


if __name__ == "__main__":
    main()
