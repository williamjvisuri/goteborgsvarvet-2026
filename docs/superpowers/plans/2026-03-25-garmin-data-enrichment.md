# Garmin Data Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich Garmin-synced workouts with HR, cadence, pace, elevation, training effect, HR zones, per-km splits, and race predictions — then surface this data in the coaching prompt.

**Architecture:** Modify `sync_garmin.py` in-place to extract more fields from the activity list response and make per-activity detail calls (HR zones, splits). Modify `gen_prompt.py` to include new data sections. No new modules.

**Tech Stack:** Python 3, garminconnect, pytest

---

### Task 1: Add pace-from-speed and HR zone formatting helpers to gen_prompt.py

New pure functions needed by both sync and prompt code.

**Files:**
- Modify: `gen_prompt.py` (add after `format_pace` at line 48)
- Test: `test_gen_prompt.py`

- [ ] **Step 1: Write failing tests for `format_pace_from_speed`**

Add to `test_gen_prompt.py`:

```python
from gen_prompt import format_pace_from_speed

def test_format_pace_from_speed():
    # 2.27 m/s = 1000/2.27/60 = 7.34 min/km = 7:20
    assert format_pace_from_speed(2.27) == "7:20"

def test_format_pace_from_speed_fast():
    # 3.33 m/s = 1000/3.33/60 = 5.005 min/km = 5:00
    assert format_pace_from_speed(3.33) == "5:00"

def test_format_pace_from_speed_zero():
    assert format_pace_from_speed(0) is None

def test_format_pace_from_speed_none():
    assert format_pace_from_speed(None) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest test_gen_prompt.py::test_format_pace_from_speed -v`
Expected: FAIL with `ImportError` (function doesn't exist)

- [ ] **Step 3: Implement `format_pace_from_speed`**

Add to `gen_prompt.py` after the `format_pace` function (after line 48):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest test_gen_prompt.py::test_format_pace_from_speed -v`
Expected: All 4 PASS

- [ ] **Step 5: Write failing tests for `format_hr_zones`**

Add to `test_gen_prompt.py`:

```python
from gen_prompt import format_hr_zones

def test_format_hr_zones():
    zones = [
        {"zone": 1, "seconds": 300},
        {"zone": 2, "seconds": 600},
        {"zone": 3, "seconds": 300},
        {"zone": 4, "seconds": 0},
        {"zone": 5, "seconds": 0},
    ]
    assert format_hr_zones(zones) == "Z1:25% Z2:50% Z3:25%"

def test_format_hr_zones_none():
    assert format_hr_zones(None) is None

def test_format_hr_zones_empty():
    assert format_hr_zones([]) is None

def test_format_hr_zones_all_zero():
    zones = [{"zone": 1, "seconds": 0}, {"zone": 2, "seconds": 0}]
    assert format_hr_zones(zones) is None
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `python -m pytest test_gen_prompt.py::test_format_hr_zones -v`
Expected: FAIL with `ImportError`

- [ ] **Step 7: Implement `format_hr_zones`**

Add to `gen_prompt.py` after `format_pace_from_speed`:

```python
def format_hr_zones(hr_zones):
    """Format HR zones as compact string like 'Z1:25% Z2:50% Z3:25%'. Omits 0% zones."""
    if not hr_zones:
        return None
    total = sum(z["seconds"] for z in hr_zones)
    if total == 0:
        return None
    parts = []
    for z in hr_zones:
        pct = round(z["seconds"] / total * 100)
        if pct > 0:
            parts.append(f"Z{z['zone']}:{pct}%")
    return " ".join(parts) if parts else None
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest test_gen_prompt.py::test_format_hr_zones -v`
Expected: All 4 PASS

- [ ] **Step 9: Write failing test for `format_splits`**

Add to `test_gen_prompt.py`:

```python
from gen_prompt import format_splits

def test_format_splits():
    splits = [
        {"km": 1, "pace": "7:15", "avg_hr": 138},
        {"km": 2, "pace": "7:25", "avg_hr": 145},
        {"km": 3, "pace": "7:18", "avg_hr": 148},
    ]
    result = format_splits(splits)
    assert "Km 1: 7:15 (138 bpm)" in result
    assert "Km 2: 7:25 (145 bpm)" in result
    assert "Km 3: 7:18 (148 bpm)" in result

def test_format_splits_none():
    assert format_splits(None) is None

def test_format_splits_empty():
    assert format_splits([]) is None

def test_format_splits_missing_hr():
    splits = [{"km": 1, "pace": "7:15", "avg_hr": None}]
    result = format_splits(splits)
    assert "Km 1: 7:15" in result
    assert "bpm" not in result
```

- [ ] **Step 10: Run tests to verify they fail**

Run: `python -m pytest test_gen_prompt.py::test_format_splits -v`
Expected: FAIL with `ImportError`

- [ ] **Step 11: Implement `format_splits`**

Add to `gen_prompt.py` after `format_hr_zones`:

```python
def format_splits(splits):
    """Format splits as compact string. Returns None if no splits."""
    if not splits:
        return None
    parts = []
    for s in splits:
        hr_str = f" ({s['avg_hr']} bpm)" if s.get("avg_hr") else ""
        parts.append(f"Km {s['km']}: {s['pace']}{hr_str}")
    return " | ".join(parts)
```

- [ ] **Step 12: Run tests to verify they pass**

Run: `python -m pytest test_gen_prompt.py::test_format_splits -v`
Expected: All 4 PASS

- [ ] **Step 13: Run all tests**

Run: `python -m pytest test_gen_prompt.py -v`
Expected: All tests PASS (existing + new)

- [ ] **Step 14: Commit**

```bash
git add gen_prompt.py test_gen_prompt.py
git commit -m "Add format helpers: pace from speed, HR zones, splits"
```

---

### Task 2: Enrich `garmin_activity_to_entry` in sync_garmin.py

Extract all summary fields from the Garmin activity dict.

**Files:**
- Modify: `sync_garmin.py:77-113` (`garmin_activity_to_entry` function)

- [ ] **Step 1: Add `import time` to sync_garmin.py**

Add `time` to the imports at the top of `sync_garmin.py` (line 12, after `import sys`):

```python
import time
```

- [ ] **Step 2: Add `format_pace_from_speed` to sync_garmin.py**

Add after the `WEEKDAY_TO_KEY` constant (after line 24):

```python
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
```

Note: This duplicates `gen_prompt.py`'s version. Both files are standalone scripts and share no imports — duplication is preferable to coupling them.

- [ ] **Step 3: Replace `garmin_activity_to_entry` with enriched version**

Replace the entire `garmin_activity_to_entry` function (lines 77-113) with:

```python
def garmin_activity_to_entry(activity, plan):
    """Konverterar ett Garmin-aktivitetsobjekt till ett workouts.json-inlägg."""
    # Datum
    start_time = activity.get("startTimeLocal", "")
    activity_date = start_time[:10] if start_time else None
    if not activity_date:
        return None

    # Distans och tid
    distance_m = activity.get("distance") or 0
    distance_km = round(distance_m / 1000, 1)

    duration_s = activity.get("duration") or 0
    duration_min = round(duration_s / 60)

    # Puls → RPE
    avg_hr = activity.get("averageHR")
    rpe = estimate_rpe(avg_hr)

    # Planmatchning
    planned_week, planned_day, plan_type = match_plan(activity_date, plan)

    # Typ: använd planens typ om vi matchade ett löppass, annars "running"
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
```

- [ ] **Step 4: Commit**

```bash
git add sync_garmin.py
git commit -m "Enrich garmin_activity_to_entry with summary fields"
```

---

### Task 3: Add per-activity detail fetching (HR zones + splits)

**Files:**
- Modify: `sync_garmin.py` (add new functions + modify `main`)

- [ ] **Step 1: Add `fetch_hr_zones` function**

Add after `filter_running` (after line 190):

```python
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
```

- [ ] **Step 2: Add `fetch_splits` function**

Add after `fetch_hr_zones`:

```python
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
```

- [ ] **Step 3: Add `enrich_entry_details` function**

Add after `fetch_splits`:

```python
def enrich_entry_details(client, entry):
    """Hämtar HR-zoner och splits för en entry. Modifierar entry in-place."""
    activity_id = entry.get("activity_id")
    if not activity_id:
        return
    entry["hr_zones"] = fetch_hr_zones(client, activity_id)
    entry["splits"] = fetch_splits(client, activity_id)
```

- [ ] **Step 4: Add detail fetching loop in `main`**

In `main`, after the line `new_entries.append(entry)` (line 349) and before the `if skipped:` line (line 351), add the detail fetching. Replace the block from `if skipped:` (line 351) through `sys.exit(0)` (line 356) with:

```python
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
```

- [ ] **Step 5: Commit**

```bash
git add sync_garmin.py
git commit -m "Add per-activity detail fetching: HR zones and splits"
```

---

### Task 4: Add race predictions fetching

**Files:**
- Modify: `sync_garmin.py` (add function + call in `main`)

- [ ] **Step 1: Add `RACE_PREDICTIONS_FILE` constant**

Add after the `PLAN_FILE` constant (line 21):

```python
RACE_PREDICTIONS_FILE = SCRIPT_DIR / "race_predictions.json"
```

- [ ] **Step 2: Add `fetch_and_save_race_predictions` function**

Add after `enrich_entry_details`:

```python
def fetch_and_save_race_predictions(client):
    """Hämtar och sparar loppprognos från Garmin. Skriver race_predictions.json."""
    try:
        predictions = client.get_race_predictions()
        if not predictions:
            return
        # Find half marathon prediction
        hm_seconds = None
        for p in predictions:
            distance = p.get("raceDistanceInMeters") or p.get("racePredictionDistance")
            if distance and abs(distance - 21097.5) < 500:
                hm_seconds = p.get("raceTimeInSeconds") or p.get("racePredictionTime")
                break
        if hm_seconds is None:
            return
        hm_seconds = round(hm_seconds)
        hours = hm_seconds // 3600
        mins = (hm_seconds % 3600) // 60
        secs = hm_seconds % 60
        formatted = f"{hours}:{mins:02d}:{secs:02d}"
        data = {
            "fetched": date.today().isoformat(),
            "half_marathon_seconds": hm_seconds,
            "half_marathon_formatted": formatted,
        }
        with open(RACE_PREDICTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Loppprognos uppdaterad: Halvmaraton {formatted}")
    except Exception:
        pass
```

- [ ] **Step 3: Call race predictions in `main`**

In `main`, after the workouts.json is written (after the `print(f"\n{len(new_entries)} pass sparade i workouts.json.")` line), add:

```python
    # Hämta loppprognos
    fetch_and_save_race_predictions(client)
```

- [ ] **Step 4: Add `race_predictions.json` to git push**

In the `git_push` function, update the `cmds` list to also add `race_predictions.json`:

```python
    cmds = [
        ["git", "-C", str(SCRIPT_DIR), "add", "workouts.json", "race_predictions.json"],
        ["git", "-C", str(SCRIPT_DIR), "commit", "-m", commit_msg],
        ["git", "-C", str(SCRIPT_DIR), "push"],
    ]
```

- [ ] **Step 5: Commit**

```bash
git add sync_garmin.py
git commit -m "Add race predictions fetching and race_predictions.json"
```

---

### Task 5: Update print_summary to show enriched data

**Files:**
- Modify: `sync_garmin.py:193-210` (`print_summary` function)

- [ ] **Step 1: Replace `print_summary`**

Replace the entire `print_summary` function with:

```python
def print_summary(new_entries):
    """Skriver ut en sammanfattning av nya pass."""
    print(f"\n{'─'*60}")
    print(f"  Hittade {len(new_entries)} nytt/nya löppass att importera:")
    print(f"{'─'*60}")
    for i, e in enumerate(new_entries, 1):
        plan_info = ""
        if e["planned_week"]:
            plan_info = f"  → Planerat: {e['planned_week']} / {e['planned_day']}"
        rpe_str = str(e["rpe"]) if e["rpe"] is not None else "–"
        hr_str = f"HR {e['avg_hr']}/{e['max_hr']}" if e.get("avg_hr") else ""
        cadence_str = f"Kadans {e['avg_cadence']}" if e.get("avg_cadence") else ""
        te_str = f"TE {e['aerobic_te']}" if e.get("aerobic_te") else ""
        details = "  ".join(s for s in [hr_str, cadence_str, te_str] if s)
        print(
            f"\n  {i}. {e['date']}  {e['type'].upper()}  "
            f"{e['distance_km']} km  {e['duration_min']} min  RPE {rpe_str}"
        )
        if e.get("avg_pace"):
            print(f"     Tempo: {e['avg_pace']} min/km")
        if details:
            print(f"     {details}")
        print(f"     \"{e['note']}\"")
        if plan_info:
            print(f"     {plan_info}")
    print(f"\n{'─'*60}")
```

- [ ] **Step 2: Commit**

```bash
git add sync_garmin.py
git commit -m "Update print_summary to show enriched fields"
```

---

### Task 6: Remove old Garmin-synced entry from workouts.json

**Files:**
- Modify: `workouts.json`

- [ ] **Step 1: Remove the 2026-03-19 Garmin-synced entry**

Edit `workouts.json` to remove the second entry (the 3.0 km Trollhättan Running run). Keep the gym session (2026-03-21) and the manually logged long run (2026-03-22). The file should become:

```json
[
  {
    "date": "2026-03-21",
    "planned_week": null,
    "planned_day": null,
    "type": "gym",
    "duration_min": 45,
    "exercises": [
      {
        "name": "Knäböj",
        "sets": [
          {"reps": 10, "kg": 40},
          {"reps": 10, "kg": 40},
          {"reps": 10, "kg": 40}
        ]
      },
      {
        "name": "Skivstångsrodd",
        "sets": [
          {"reps": 8, "kg": 40},
          {"reps": 8, "kg": 40},
          {"reps": 8, "kg": 40}
        ]
      },
      {
        "name": "Tåhävningar",
        "sets": [
          {"reps": 12, "kg": 84},
          {"reps": 12, "kg": 84},
          {"reps": 12, "kg": 84}
        ]
      }
    ],
    "note": ""
  },
  {
    "date": "2026-03-22",
    "planned_week": "intro",
    "planned_day": "sun",
    "type": "long_run",
    "distance_km": 4,
    "duration_min": 28,
    "rpe": 4,
    "note": "gick bra. tungt i mitten, lätt avslutning."
  }
]
```

- [ ] **Step 2: Commit**

```bash
git add workouts.json
git commit -m "Remove Garmin-synced entry, keep manually logged workouts"
```

---

### Task 7: Update test fixtures for enriched workouts

Existing tests use `sample_workouts` from disk. After Task 6, `workouts.json` has 2 entries (no Garmin fields). Tests that check `km_actual == 7.0` will fail because the 3 km run was removed. Fix the affected tests.

**Files:**
- Modify: `test_gen_prompt.py`

- [ ] **Step 1: Update `test_overall_stats_intro_week_complete`**

The 3.0 km run was removed, so only the 4 km long run remains as a planned running workout. Update:

```python
def test_overall_stats_intro_week_complete(sample_plan, sample_workouts):
    """With today=2026-03-23, intro week has 2 elapsed planned sessions but only 1 running completed."""
    stats = calc_overall_stats(sample_plan, sample_workouts, today=date(2026, 3, 23))
    assert stats["adherence_completed"] == 1  # only long_run has planned_week set
    assert stats["adherence_elapsed"] == 2
    assert stats["adherence_pct"] == 50
    assert stats["km_actual"] == 4.0  # only 4 km long run
    assert stats["km_planned"] == 7.0  # 3 + 4
    assert stats["longest_run_km"] == 4.0
    assert stats["longest_run_date"] == "2026-03-22"
    assert stats["bonus_count"] == 1  # gym bonus
```

- [ ] **Step 2: Update `test_weekly_stats_intro`**

```python
def test_weekly_stats_intro(sample_plan, sample_workouts):
    """Intro week should show 1/2 sessions after removing synced run."""
    weeks = calc_weekly_stats(sample_plan, sample_workouts, today=date(2026, 3, 23))
    assert len(weeks) == 1  # only intro is elapsed
    intro = weeks[0]
    assert intro["label"] == "Introvecka"
    assert intro["sessions_done"] == 1  # only long_run
    assert intro["sessions_planned"] == 2
    assert intro["km_planned"] == 7.0
    assert intro["km_actual"] == 4.0
    assert intro["pace"] is not None
    assert intro["rpe_planned"] is not None
    assert intro["rpe_actual"] is not None
```

- [ ] **Step 3: Run all tests**

Run: `python -m pytest test_gen_prompt.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add test_gen_prompt.py
git commit -m "Update test expectations after removing Garmin-synced entry"
```

---

### Task 8: Enrich per-week table in gen_prompt.py

**Files:**
- Modify: `gen_prompt.py:101-155` (`calc_weekly_stats`) and `gen_prompt.py:428-445` (per-week table in `build_prompt`)

- [ ] **Step 1: Add avg HR, avg cadence, avg training effect to `calc_weekly_stats`**

In `calc_weekly_stats`, after the RPE calculation (line 141) and before the `results.append` (line 143), add:

```python
        # Enriched averages
        hr_vals = [w["avg_hr"] for w in run_workouts if w.get("avg_hr") is not None]
        avg_hr = round(sum(hr_vals) / len(hr_vals)) if hr_vals else None

        cadence_vals = [w["avg_cadence"] for w in run_workouts if w.get("avg_cadence") is not None]
        avg_cadence = round(sum(cadence_vals) / len(cadence_vals)) if cadence_vals else None

        te_vals = [w["aerobic_te"] for w in run_workouts if w.get("aerobic_te") is not None]
        avg_te = round(sum(te_vals) / len(te_vals), 1) if te_vals else None
```

Then add these to the `results.append` dict:

```python
            "avg_hr": avg_hr,
            "avg_cadence": avg_cadence,
            "avg_te": avg_te,
```

- [ ] **Step 2: Update per-week table in `build_prompt`**

Replace the per-week table header and row formatting (lines 431-444) with:

```python
            lines.append("| Vecka | Fas | Pass | Km plan | Km faktisk | Δ km% | Tempo | Snitt HR | Kadans | TE | RPE plan → faktisk |")
            lines.append("|-------|-----|------|---------|------------|-------|-------|----------|--------|----|--------------------|")
            prev_km = None
            for w in weekly:
                if prev_km and prev_km > 0:
                    km_change = f"{round((w['km_planned'] - prev_km) / prev_km * 100):+d}%"
                else:
                    km_change = "—"
                lines.append(
                    f"| {w['label']} | {w['phase']} | {w['sessions_done']}/{w['sessions_planned']} "
                    f"| {w['km_planned']} | {w['km_actual']} | {km_change} | {w['pace'] or '—'} "
                    f"| {w['avg_hr'] or '—'} | {w['avg_cadence'] or '—'} | {w['avg_te'] or '—'} "
                    f"| {w['rpe_planned'] or '—'} → {w['rpe_actual'] or '—'} |"
                )
                prev_km = w["km_planned"]
```

- [ ] **Step 3: Run all tests**

Run: `python -m pytest test_gen_prompt.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add gen_prompt.py
git commit -m "Add avg HR, cadence, training effect to per-week table"
```

---

### Task 9: Enrich per-session table in gen_prompt.py

**Files:**
- Modify: `gen_prompt.py:228-297` (`individual_sessions`) and `gen_prompt.py:448-457` (session table in `build_prompt`)

- [ ] **Step 1: Add enriched fields to `individual_sessions` rows**

In `individual_sessions`, where `wo` exists (the `if wo:` block starting at line 253), add these lines after `status = "Done"`:

```python
                avg_hr = wo.get("avg_hr", "—")
                cadence = wo.get("avg_cadence", "—")
                elev = wo.get("elevation_gain", "—")
```

In the `else:` block (MISSED), add:

```python
                avg_hr = "—"
                cadence = "—"
                elev = "—"
```

Add these to the `rows.append` dict:

```python
                "avg_hr": avg_hr,
                "cadence": cadence,
                "elevation_gain": elev,
```

Do the same for bonus workouts at the end of the function:

```python
            "avg_hr": w.get("avg_hr", "—"),
            "cadence": w.get("avg_cadence", "—"),
            "elevation_gain": w.get("elevation_gain", "—"),
```

- [ ] **Step 2: Update session table header and rows in `build_prompt`**

Replace the session table (lines 449-456) with:

```python
            lines.append("### Alla pass (detalj)")
            lines.append("| Datum | Vecka | Typ | Km plan | Km faktisk | RPE plan → faktisk | Tempo | HR | Kadans | Höjdm | Status | Anteckning |")
            lines.append("|-------|-------|-----|---------|------------|-------------------|-------|----|--------|-------|--------|------------|")
            for s in sessions:
                lines.append(
                    f"| {s['date']} | {s['week']} | {s['type']} | {s['plan_km']} | {s['actual_km']} "
                    f"| {s['plan_rpe']} → {s['actual_rpe']} | {s['pace']} | {s['avg_hr']} | {s['cadence']} | {s['elevation_gain']} "
                    f"| {s['status']} | {s['note']} |"
                )
```

- [ ] **Step 3: Run all tests**

Run: `python -m pytest test_gen_prompt.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add gen_prompt.py
git commit -m "Add HR, cadence, elevation to per-session table"
```

---

### Task 10: Add HR zone distribution section to prompt

**Files:**
- Modify: `gen_prompt.py` (`build_prompt` function, after the individual sessions table)

- [ ] **Step 1: Add HR zone section in `build_prompt`**

After the individual sessions table block (after the `lines.append("")` that closes it), add:

```python
        # HR zone distribution per session
        hr_zone_lines = []
        for s_wo in workouts:
            if s_wo.get("type") not in RUNNING_TYPES:
                continue
            zones_str = format_hr_zones(s_wo.get("hr_zones"))
            if zones_str:
                hr_zone_lines.append(f"- {s_wo['date']}: {zones_str}")
        if hr_zone_lines:
            lines.append("### Pulszoner per pass")
            lines.extend(hr_zone_lines)
            lines.append("")
```

- [ ] **Step 2: Run prompt generation to verify output**

Run: `python gen_prompt.py --prompt 2>&1 | head -80`
Expected: Output includes the existing sections. HR zone section will appear once enriched workouts exist.

- [ ] **Step 3: Commit**

```bash
git add gen_prompt.py
git commit -m "Add HR zone distribution section to coaching prompt"
```

---

### Task 11: Add split analysis section for long runs and tempo

**Files:**
- Modify: `gen_prompt.py` (`build_prompt` function, after HR zone section)

- [ ] **Step 1: Add split analysis section**

After the HR zone section added in Task 10, add:

```python
        # Split analysis for long runs and tempo
        split_lines = []
        for s_wo in workouts:
            if s_wo.get("type") not in ("long_run", "tempo"):
                continue
            splits_str = format_splits(s_wo.get("splits"))
            if splits_str:
                split_lines.append(f"- {s_wo['date']} ({s_wo['type']}): {splits_str}")
        if split_lines:
            lines.append("### Splitanalys (långpass & tempo)")
            lines.extend(split_lines)
            lines.append("")
```

- [ ] **Step 2: Commit**

```bash
git add gen_prompt.py
git commit -m "Add split analysis section for long runs and tempo"
```

---

### Task 12: Add race prediction to prompt

**Files:**
- Modify: `gen_prompt.py` (add `load_race_predictions` function + use in `build_prompt`)

- [ ] **Step 1: Add `load_race_predictions` function**

Add after `load_data`:

```python
def load_race_predictions():
    """Load race_predictions.json if it exists. Returns dict or None."""
    path = HERE / "race_predictions.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
```

- [ ] **Step 2: Use race prediction in `build_prompt`**

In `build_prompt`, after `est_finish = estimated_finish(workouts)` (line 391), add:

```python
    race_pred = load_race_predictions()
```

Then in the summary section, after the `est_finish` line (around line 422), add:

```python
        if race_pred:
            lines.append(f"- Garmin loppprognos (halvmaraton): {race_pred['half_marathon_formatted']} (hämtad {race_pred['fetched']})")
```

- [ ] **Step 3: Commit**

```bash
git add gen_prompt.py
git commit -m "Add Garmin race prediction to coaching prompt"
```

---

### Task 13: Add coaching instruction for enriched data

**Files:**
- Modify: `gen_prompt.py` (the "Vad jag vill ha" section in `build_prompt`)

- [ ] **Step 1: Update coaching instructions**

In `build_prompt`, after instruction 5 about gym (line 515), add a new instruction:

```python
    lines.append("6. **Pulsanalys** — kommentera pulszoner och kadans om data finns. Varnas om lätta pass har för mycket tid i zon 4+.")
```

- [ ] **Step 2: Run all tests**

Run: `python -m pytest test_gen_prompt.py -v`
Expected: All PASS

- [ ] **Step 3: Test prompt output end-to-end**

Run: `python gen_prompt.py --prompt > /dev/null && echo "OK"`
Expected: "OK" (no errors)

- [ ] **Step 4: Commit**

```bash
git add gen_prompt.py
git commit -m "Add pulse analysis coaching instruction"
```

---

### Task 14: Final integration test

- [ ] **Step 1: Run all tests**

Run: `python -m pytest test_gen_prompt.py -v`
Expected: All PASS

- [ ] **Step 2: Verify prompt generates without errors**

Run: `python gen_prompt.py --prompt | wc -l`
Expected: Non-zero line count, no errors

- [ ] **Step 3: Verify sync_garmin.py imports cleanly**

Run: `python -c "import sync_garmin; print('OK')"`
Expected: "OK"

- [ ] **Step 4: Commit any remaining changes**

If there are any unstaged changes, commit them:

```bash
git status
```
