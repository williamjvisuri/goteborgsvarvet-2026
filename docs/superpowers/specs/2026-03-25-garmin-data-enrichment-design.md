# Garmin Data Enrichment

Enrich synced Garmin data with heart rate, cadence, pace, elevation, training effect, HR zones, per-km splits, and race predictions. Update the coaching prompt to surface this data.

## Context

`sync_garmin.py` currently captures only distance, duration, averageHR (discarded after RPE estimation), and activity name. The Garmin Connect API returns far more per activity, and detail endpoints provide HR zones and split data. This data would let the coaching prompt give much richer feedback.

Only 3 entries are currently logged. The first run (2026-03-19, 3.0 km) was synced from Garmin — remove it and re-sync to get enriched data. The gym session (2026-03-21) and second run (2026-03-22, 4 km long run) were manually logged and should be kept as-is (they won't have the new Garmin fields, which is fine — all new fields are nullable).

## Approach

Modify `sync_garmin.py` in-place. No new modules or architectural changes.

## workouts.json Schema Changes

Each running entry gains these nullable fields:

```json
{
  "activity_id": 123456789,
  "avg_hr": 142,
  "max_hr": 168,
  "avg_pace": "7:20",
  "avg_cadence": 164,
  "max_cadence": 172,
  "elevation_gain": 45,
  "elevation_loss": 42,
  "aerobic_te": 3.2,
  "anaerobic_te": 0.8,
  "training_load": 87,
  "vo2max": 38.5,
  "calories": 280,
  "hr_zones": [
    {"zone": 1, "seconds": 120},
    {"zone": 2, "seconds": 480},
    {"zone": 3, "seconds": 600},
    {"zone": 4, "seconds": 100},
    {"zone": 5, "seconds": 20}
  ],
  "splits": [
    {"km": 1, "pace": "7:15", "avg_hr": 138},
    {"km": 2, "pace": "7:25", "avg_hr": 145},
    {"km": 3, "pace": "7:18", "avg_hr": 148}
  ]
}
```

Existing fields (`date`, `planned_week`, `planned_day`, `type`, `distance_km`, `duration_min`, `rpe`, `note`) stay unchanged. Gym entries are unaffected.

## race_predictions.json

New top-level file, written at the end of each sync:

```json
{
  "fetched": "2026-03-25",
  "half_marathon_seconds": 7200,
  "half_marathon_formatted": "2:00:00"
}
```

## sync_garmin.py Changes

### Summary field extraction

Extract from the existing activity list response (no extra API calls):
- `activityId`, `averageHR`, `maxHR`, `averageSpeed` (convert to M:SS min/km), `averageRunningCadenceInStepsPerMinute`, `maxRunningCadenceInStepsPerMinute`, `elevationGain`, `elevationLoss`, `aerobicTrainingEffect`, `anaerobicTrainingEffect`, `activityTrainingLoad`, `vO2MaxValue`, `calories`

### Per-activity detail calls

For each new activity, after building the entry from summary data:
1. `get_activity_hr_in_timezones(activity_id)` — extract zone number and seconds per zone into `hr_zones`
2. `get_activity_splits(activity_id)` — extract per-lap distance, pace (from `averageSpeed`), and `averageHR` into `splits`
3. 1 second sleep between activities to avoid rate limiting

### Graceful degradation

Each detail call is wrapped in try/except. On failure, the field is set to `null` and the entry is still saved with summary data.

### Race predictions

One call to `get_race_predictions()` at the end of sync. Extract half marathon prediction. Write to `race_predictions.json`. Skip silently on failure.

### Dedup

Unchanged — still by date. `activity_id` is stored but not used for dedup to maintain compatibility with `log.sh` entries.

### Print summary

Updated to show HR, cadence, and training effect in the confirmation output.

## gen_prompt.py Changes

### Enriched existing tables

- Per-week table: add avg HR, avg cadence, avg training effect columns
- Per-session table: add avg HR, cadence, elevation gain columns

### New prompt sections

**HR zone distribution** — per session, compact: `Z1:40% Z2:35% Z3:25%`. Weekly aggregate to spot easy runs done too hard.

**Split analysis** — for long runs and tempo runs only. Per-km pace table so the coach can see fade or negative splits.

**Race prediction** — if `race_predictions.json` exists, show Garmin's half marathon estimate alongside the existing `estimated_finish()` calculation.

### Raw data block

Full `hr_zones` and `splits` arrays per session go in the existing `<details>` raw data section for the coach LLM to reference if needed.

### Unchanged

Overall stats, trends, gym summary, upcoming sessions, phase instructions — all unchanged.

## Testing

- Add tests for new formatting/calculation functions: pace conversion from m/s, HR zone percentage calculation, split formatting. Same pattern as existing tests (pin `today`, use fixtures).
- Update `workouts.json` sample data with new fields so fixture-based tests work.
- No mocking of Garmin API calls.
