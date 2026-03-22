# Göteborgsvarvet 2026 — Training Dashboard Design

## Overview

A static, single-page web dashboard for tracking training progress toward Göteborgsvarvet 2026 (half marathon, 21.1 km, May 23 2026). The page displays a 9-week + intro week training plan alongside logged workouts, letting friends follow progress via a public URL.

**Language:** Swedish
**Audience:** View-only for friends (no login, no interaction)
**Logging:** Owner logs workouts via a CLI script, pushes to git to update the live site

## Architecture

Single HTML file + two JSON data files, hosted on GitHub Pages. No build step, no framework, no backend.

```
goteborgsvarvet_2026/
├── index.html          # Dashboard (HTML + CSS + JS in one file)
├── plan.json           # Training plan (static, encoded from PDF)
├── workouts.json       # Logged workouts (updated via log.sh)
├── log.sh              # CLI logging tool
└── traningsplan_goteborgsvarvet.pdf  # Original plan
```

### Deployment

- GitHub Pages serving from `main` branch root
- `index.html` fetches `plan.json` and `workouts.json` via relative `fetch()` calls
- Every `git push` updates the live site immediately
- No CI/CD, no build step, no dependencies

## Data Model

### plan.json

Static file encoding the training plan from the PDF. Written once, never changes.

```json
{
  "goal": "Jogga hela vägen utan gångpauser",
  "race": {
    "name": "Göteborgsvarvet",
    "date": "2026-05-23",
    "distance_km": 21.1
  },
  "weeks": [
    {
      "id": "intro",
      "label": "Introvecka",
      "subtitle": "Kom igång",
      "start_date": "2026-03-19",
      "phase": "Basuppbyggnad",
      "total_km": 7,
      "days": {
        "mon": null,
        "tue": null,
        "wed": null,
        "thu": {
          "type": "running",
          "description": "Löpning: 20 min lätt",
          "distance_km": 3,
          "duration_min": 20,
          "rpe": "3-4",
          "note": "Ditt första pass!"
        },
        "fri": { "type": "rest" },
        "sat": { "type": "rest" },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 4 km",
          "distance_km": 4,
          "rpe": "3",
          "note": "Gå om det behövs"
        }
      }
    }
  ]
}
```

**Day types:** `running`, `long_run`, `tempo`, `gym`, `rest`, `race`

**Day value conventions:**
- `null` — No session scheduled (e.g., Mon-Wed of intro week, before the plan starts that week). Rendered as empty/grey.
- `{ "type": "rest" }` — Intentional rest day as part of the plan. Rendered as grey with "Vila" label.
- Week 9 has the race on **Saturday** (`sat`), not Sunday, with `"type": "race"`.

**Gym days** include an `exercises` array:
```json
{
  "type": "gym",
  "description": "Gym A: Marklyft, press, face pulls, vadpress",
  "duration_min": 30,
  "exercises": [
    { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Rak rygg" },
    { "name": "Stående press", "sets": 3, "reps": "8-10" },
    { "name": "Face pulls", "sets": 3, "reps": "15-20", "note": "Lätt vikt" },
    { "name": "Vadpress", "sets": 3, "reps": "15-20" }
  ]
}
```

### workouts.json

Array of logged workouts, appended to by `log.sh`.

```json
[
  {
    "date": "2026-03-19",
    "planned_week": "intro",
    "planned_day": "thu",
    "type": "running",
    "distance_km": 3.1,
    "duration_min": 21,
    "rpe": 4,
    "note": "Första passet!"
  },
  {
    "date": "2026-03-21",
    "planned_week": null,
    "planned_day": null,
    "type": "running",
    "distance_km": 2,
    "duration_min": 14,
    "rpe": 3,
    "note": "Extra liten runda"
  }
]
```

**Key fields:**
- `planned_week` + `planned_day`: Links workout to the plan. Both `null` for bonus/extra sessions.
- `type`: Matches plan day types (`running`, `long_run`, `tempo`, `gym`)
- Running workouts: `distance_km`, `duration_min`, `rpe`, `note`
- Gym workouts additionally include `exercises` array with actual weight/reps:

```json
{
  "date": "2026-03-24",
  "planned_week": "v1",
  "planned_day": "thu",
  "type": "gym",
  "duration_min": 42,
  "exercises": [
    { "name": "Marklyft", "sets": [{"reps": 8, "kg": 60}, {"reps": 7, "kg": 60}, {"reps": 6, "kg": 60}] },
    { "name": "Knäböj", "sets": [{"reps": 10, "kg": 50}, {"reps": 10, "kg": 50}, {"reps": 9, "kg": 50}] }
  ],
  "note": "Bra teknik på marklyft"
}
```

## Page Layout

Single scrollable page, dark theme (#0f172a base), with these sections top to bottom:

### 1. Hero
- Race name: "Göteborgsvarvet 2026"
- Distance and date: "21.1 km — Lördag 23 maj"
- Countdown: days and weeks remaining (calculated live from current date)

### 2. Progress Bar
- "Total framsteg: X av Y pass klara (Z%)"
- Horizontal bar showing completion percentage
- Only counts planned sessions toward adherence (bonus sessions excluded)

### 3. Stats Row
- 4-column grid: Km löpt | Pass klara | Gympass | Följsamhet %
- Adherence % = planned sessions completed / planned sessions elapsed

### 4. Current Week
- Week name, date range, phase label, target km
- Badge: "PÅGÅR" (in progress)
- 7-day grid (Mon-Sun) showing each day:
  - **Completed (green, checkmark):** Planned session done, shows actual km
  - **Planned/today (blue outline):** Upcoming planned session, shows target km + "IDAG" if today
  - **Rest (grey):** Rest day
  - **Bonus (purple, star):** Extra session not in plan, shows actual km
  - **Missed (red, if date has passed):** Planned session not logged
- Count display: "X/Y pass + Z extra" — separates plan adherence from bonus sessions

### 5. All Weeks
- Compact list of all 10 weeks (intro + V1-V9)
- Each row shows: week label, phase, planned km, completion count + mini progress bar
- Current week highlighted with blue left border
- Past weeks show completion status; future weeks are dimmed
- Expandable to show day-by-day detail (same grid as current week)

### 6. Volume Chart
- Bar chart showing km per week (all 10 weeks)
- Solid bars for completed weeks, dashed outline for future/planned weeks
- Legend: solid = genomfört, dashed = planerat

### Color Coding
| Color | Meaning |
|-------|---------|
| Green (#22c55e) | Completed session |
| Blue (#3b82f6) | Planned / today / active |
| Purple (#8b5cf6) | Bonus/extra session |
| Grey (#475569) | Rest day |
| Amber (#f59e0b) | Race day |
| Red (#ef4444) | Missed session |

### Responsive
- Mobile-first design (friends will mostly check on phones)
- The 7-day grid stacks compactly on narrow screens
- Stats row goes to 2x2 grid on mobile

## Logging Script (log.sh)

Interactive bash script for logging workouts to `workouts.json`.

### Flow

1. Prompt for workout type (Löpning / Gym / Långpass / Tempo)
2. Prompt for date (default: today)
3. Auto-detect the next planned session for that date and offer to link it (`y/n`)
4. Prompt for metrics based on type:
   - **Running/long run/tempo:** distance_km, duration_min, rpe, note
   - **Gym:** For each exercise in the plan: weight and reps per set, note
5. Append to `workouts.json`
6. Print confirmation and remind to `git add && git commit && git push`

### Behaviors

- Auto-detects current week and next planned session based on date
- If workout date doesn't match a planned day, sets `planned_week`/`planned_day` to `null` (bonus session)
- Validates input (positive numbers, RPE 1-8)
- Handles empty `workouts.json` (first run creates the array)
- `--push` flag optionally runs `git add workouts.json && git commit -m "Logg: <type> <date>" && git push`

## External Dependencies

- **None for the site.** Pure HTML + CSS + vanilla JS.
- **Chart.js** (loaded via CDN) for the volume bar chart. Single `<script>` tag. This is the only external dependency.
- **log.sh** requires `bash` and `jq` for JSON manipulation.

## Out of Scope

- User authentication or login
- Comments, reactions, or social features
- Backend or database
- Build tools, bundlers, or frameworks
- Multiple pages or routing
- Strava/Garmin integration
