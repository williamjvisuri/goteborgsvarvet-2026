# Göteborgsvarvet Training Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static, single-page training dashboard that shows a 9-week half marathon plan alongside logged workouts, hosted on GitHub Pages.

**Architecture:** Single `index.html` fetches two JSON files (`plan.json`, `workouts.json`) client-side and renders a dark-themed dashboard. A bash script (`log.sh`) provides ergonomic workout logging. No build step, no framework, no backend.

**Tech Stack:** Vanilla HTML/CSS/JS, Chart.js (CDN), bash + jq for the logging script.

---

## File Structure

```
goteborgsvarvet_2026/
├── .gitignore
├── index.html          # Complete dashboard (HTML + CSS + JS)
├── plan.json           # Training plan data (static)
├── workouts.json       # Logged workouts (updated via log.sh)
├── log.sh              # Interactive CLI logging tool
├── traningsplan_goteborgsvarvet.pdf
└── docs/superpowers/   # Design docs (specs + plans)
```

---

### Task 1: Project Setup

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Initialize git repo**

```bash
cd /home/willi/repo/goteborgsvarvet_2026
git init
```

- [ ] **Step 2: Create .gitignore**

```
.superpowers/
.DS_Store
```

- [ ] **Step 3: Initial commit**

```bash
git add .gitignore traningsplan_goteborgsvarvet.pdf docs/
git commit -m "Initial commit: training plan PDF and design docs"
```

---

### Task 2: Create plan.json

**Files:**
- Create: `plan.json`

This encodes the entire training plan from the PDF. All 10 weeks with every day's workout.

- [ ] **Step 1: Create plan.json with full training plan**

The file must contain the complete plan. Below is the full content. Note:
- `null` days = no session scheduled (before that week's training starts)
- `{ "type": "rest" }` = intentional rest day
- Week 9 race is on Saturday

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
    },
    {
      "id": "v1",
      "label": "Vecka 1",
      "subtitle": "Basuppbyggnad",
      "start_date": "2026-03-24",
      "phase": "Basuppbyggnad",
      "total_km": 12,
      "days": {
        "mon": { "type": "rest" },
        "tue": { "type": "rest" },
        "wed": {
          "type": "running",
          "description": "Löpning: 25 min lätt",
          "distance_km": 3.5,
          "duration_min": 25,
          "rpe": "3-4"
        },
        "thu": {
          "type": "gym",
          "description": "Gym: Helkropp (samlat program)",
          "duration_min": 45,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Teknik framför vikt. Rak rygg." },
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Parallellt djup. Lätt vikt." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Överhead, stabil bål." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Dra mot nedre bröstkorgen." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM. Pausa i topp och botten." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 25 min lätt",
          "distance_km": 3.5,
          "duration_min": 25,
          "rpe": "3-4"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 5.5 km",
          "distance_km": 5.5,
          "rpe": "3-4"
        }
      }
    },
    {
      "id": "v2",
      "label": "Vecka 2",
      "subtitle": "Basuppbyggnad",
      "start_date": "2026-03-31",
      "phase": "Basuppbyggnad",
      "total_km": 14,
      "days": {
        "mon": { "type": "rest" },
        "tue": { "type": "rest" },
        "wed": {
          "type": "running",
          "description": "Löpning: 30 min lätt",
          "distance_km": 4,
          "duration_min": 30,
          "rpe": "4"
        },
        "thu": {
          "type": "gym",
          "description": "Gym: Helkropp (samlat program)",
          "duration_min": 45,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Teknik framför vikt. Rak rygg." },
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Parallellt djup. Lätt vikt." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Överhead, stabil bål." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Dra mot nedre bröstkorgen." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM. Pausa i topp och botten." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 25 min lätt",
          "distance_km": 4,
          "duration_min": 25,
          "rpe": "4"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 6 km",
          "distance_km": 6,
          "rpe": "3-4"
        }
      }
    },
    {
      "id": "v3",
      "label": "Vecka 3",
      "subtitle": "Basuppbyggnad + Gym split",
      "start_date": "2026-04-07",
      "phase": "Basuppbyggnad",
      "total_km": 16,
      "days": {
        "mon": {
          "type": "gym",
          "description": "Gym A: Marklyft, press, face pulls, vadpress",
          "duration_min": 30,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Rak rygg, tryck golvet ifrån dig." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Överhead, stabil bål." },
            { "name": "Face pulls", "sets": 3, "reps": "15-20", "note": "Lätt vikt." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." }
          ]
        },
        "tue": { "type": "rest" },
        "wed": {
          "type": "running",
          "description": "Löpning: 30 min lätt",
          "distance_km": 4.5,
          "duration_min": 30,
          "rpe": "4"
        },
        "thu": {
          "type": "gym",
          "description": "Gym B: Knäböj, rodd, vadpress, maghjul",
          "duration_min": 30,
          "exercises": [
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Teknik framför vikt. Parallellt djup." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Dra mot nedre bröstkorgen." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." },
            { "name": "Maghjul", "sets": 3, "reps": "8-12", "note": "Kontrollerad ut- och inrullning." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 30 min lätt",
          "distance_km": 4.5,
          "duration_min": 30,
          "rpe": "4"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 7 km",
          "distance_km": 7,
          "rpe": "3-4"
        }
      }
    },
    {
      "id": "v4",
      "label": "Vecka 4",
      "subtitle": "Avlastning (−25%)",
      "start_date": "2026-04-14",
      "phase": "Avlastning",
      "total_km": 12,
      "days": {
        "mon": {
          "type": "gym",
          "description": "Gym A: Lättare vikter (−30–40%)",
          "duration_min": 25,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Lättare vikter, −30–40%." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Lättare vikter." },
            { "name": "Face pulls", "sets": 3, "reps": "15-20", "note": "Lätt vikt." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." }
          ]
        },
        "tue": { "type": "rest" },
        "wed": {
          "type": "running",
          "description": "Löpning: 20 min lätt",
          "distance_km": 3,
          "duration_min": 20,
          "rpe": "3"
        },
        "thu": {
          "type": "gym",
          "description": "Gym B: Lättare vikter (−30–40%)",
          "duration_min": 25,
          "exercises": [
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Lättare vikter, −30–40%." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Lättare vikter." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." },
            { "name": "Maghjul", "sets": 3, "reps": "8-12", "note": "Kontrollerat." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 20 min lätt",
          "distance_km": 3,
          "duration_min": 20,
          "rpe": "3"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 6 km",
          "distance_km": 6,
          "rpe": "3"
        }
      }
    },
    {
      "id": "v5",
      "label": "Vecka 5",
      "subtitle": "Toppfas + tempo",
      "start_date": "2026-04-21",
      "phase": "Toppfas",
      "total_km": 19,
      "days": {
        "mon": {
          "type": "gym",
          "description": "Gym A: Marklyft, press, rev. flyes, vadpress",
          "duration_min": 30,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Rak rygg." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Stabil bål." },
            { "name": "Reverse flyes", "sets": 3, "reps": "15-20", "note": "Lätt vikt." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." }
          ]
        },
        "tue": { "type": "rest" },
        "wed": {
          "type": "tempo",
          "description": "Löpning: 30 min med 4×2 min tempo, 1 min gång mellan",
          "distance_km": 4.5,
          "duration_min": 30,
          "rpe": "5-6"
        },
        "thu": {
          "type": "gym",
          "description": "Gym B: Knäböj, rodd, vadpress, maghjul",
          "duration_min": 30,
          "exercises": [
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Parallellt djup." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Kontrollerat." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." },
            { "name": "Maghjul", "sets": 3, "reps": "8-12", "note": "Spänn bålen." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 30 min lätt",
          "distance_km": 4.5,
          "duration_min": 30,
          "rpe": "4"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 10 km",
          "distance_km": 10,
          "rpe": "4"
        }
      }
    },
    {
      "id": "v6",
      "label": "Vecka 6",
      "subtitle": "Toppfas",
      "start_date": "2026-04-28",
      "phase": "Toppfas",
      "total_km": 22,
      "days": {
        "mon": {
          "type": "gym",
          "description": "Gym A: Marklyft, press, face pulls, vadpress",
          "duration_min": 30,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Rak rygg." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Stabil bål." },
            { "name": "Face pulls", "sets": 3, "reps": "15-20", "note": "Lätt vikt." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." }
          ]
        },
        "tue": { "type": "rest" },
        "wed": {
          "type": "tempo",
          "description": "Löpning: 35 min med 5×2 min tempo, 1 min gång mellan",
          "distance_km": 5.5,
          "duration_min": 35,
          "rpe": "5-6"
        },
        "thu": {
          "type": "gym",
          "description": "Gym B: Knäböj, rodd, vadpress, maghjul",
          "duration_min": 30,
          "exercises": [
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Parallellt djup." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Kontrollerat." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." },
            { "name": "Maghjul", "sets": 3, "reps": "8-12", "note": "Spänn bålen." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 30 min lätt",
          "distance_km": 4.5,
          "duration_min": 30,
          "rpe": "4"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 12 km",
          "distance_km": 12,
          "rpe": "4"
        }
      }
    },
    {
      "id": "v7",
      "label": "Vecka 7",
      "subtitle": "Toppfas",
      "start_date": "2026-05-05",
      "phase": "Toppfas",
      "total_km": 25,
      "days": {
        "mon": {
          "type": "gym",
          "description": "Gym A: Marklyft, press, rev. flyes, vadpress",
          "duration_min": 30,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Rak rygg." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Stabil bål." },
            { "name": "Reverse flyes", "sets": 3, "reps": "15-20", "note": "Lätt vikt." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." }
          ]
        },
        "tue": { "type": "rest" },
        "wed": {
          "type": "tempo",
          "description": "Löpning: 35 min med 4×3 min tempo, 90 sek gång mellan",
          "distance_km": 6,
          "duration_min": 35,
          "rpe": "5-6"
        },
        "thu": {
          "type": "gym",
          "description": "Gym B: Knäböj, rodd, vadpress, maghjul",
          "duration_min": 30,
          "exercises": [
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Parallellt djup." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Kontrollerat." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." },
            { "name": "Maghjul", "sets": 3, "reps": "8-12", "note": "Spänn bålen." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 35 min lätt",
          "distance_km": 5,
          "duration_min": 35,
          "rpe": "4"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 14 km",
          "distance_km": 14,
          "rpe": "4"
        }
      }
    },
    {
      "id": "v8",
      "label": "Vecka 8",
      "subtitle": "Längsta passet",
      "start_date": "2026-05-12",
      "phase": "Toppfas",
      "total_km": 27,
      "days": {
        "mon": {
          "type": "gym",
          "description": "Gym A: Lättare vikter",
          "duration_min": 25,
          "exercises": [
            { "name": "Marklyft", "sets": 3, "reps": "6-8", "note": "Lättare vikter." },
            { "name": "Stående press", "sets": 3, "reps": "8-10", "note": "Lättare vikter." },
            { "name": "Face pulls", "sets": 3, "reps": "15-20", "note": "Lätt vikt." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." }
          ]
        },
        "tue": { "type": "rest" },
        "wed": {
          "type": "tempo",
          "description": "Löpning: 30 min med 4×2 min tempo, 1 min gång mellan",
          "distance_km": 5,
          "duration_min": 30,
          "rpe": "5"
        },
        "thu": {
          "type": "gym",
          "description": "Gym B: Lättare vikter",
          "duration_min": 25,
          "exercises": [
            { "name": "Knäböj", "sets": 3, "reps": "8-10", "note": "Lättare vikter." },
            { "name": "Rodd", "sets": 3, "reps": "10-12", "note": "Lättare vikter." },
            { "name": "Vadpress", "sets": 3, "reps": "15-20", "note": "Full ROM." },
            { "name": "Maghjul", "sets": 3, "reps": "8-12", "note": "Kontrollerat." }
          ]
        },
        "fri": { "type": "rest" },
        "sat": {
          "type": "running",
          "description": "Löpning: 35 min lätt",
          "distance_km": 5,
          "duration_min": 35,
          "rpe": "4"
        },
        "sun": {
          "type": "long_run",
          "description": "Långpass: 17 km",
          "distance_km": 17,
          "rpe": "4",
          "note": "Ditt längsta pass!"
        }
      }
    },
    {
      "id": "v9",
      "label": "Vecka 9",
      "subtitle": "Taper + Loppdag",
      "start_date": "2026-05-19",
      "phase": "Taper",
      "total_km": 25,
      "days": {
        "mon": {
          "type": "gym",
          "description": "Gym: Lätt helkropp",
          "duration_min": 20,
          "exercises": [
            { "name": "Marklyft", "sets": 2, "reps": "6-8", "note": "Lätt, låg intensitet." },
            { "name": "Knäböj", "sets": 2, "reps": "8-10", "note": "Lätt, låg intensitet." },
            { "name": "Stående press", "sets": 2, "reps": "8-10", "note": "Lätt." },
            { "name": "Rodd", "sets": 2, "reps": "10-12", "note": "Lätt." },
            { "name": "Vadpress", "sets": 2, "reps": "15-20", "note": "Full ROM." }
          ]
        },
        "tue": { "type": "rest" },
        "wed": {
          "type": "running",
          "description": "Löpning: 20 min lätt med 4×30 sek ökningar",
          "distance_km": 3.9,
          "duration_min": 20,
          "rpe": "3-4"
        },
        "thu": { "type": "rest" },
        "fri": {
          "type": "rest",
          "note": "Total vila. Packa kläder kvällen."
        },
        "sat": {
          "type": "race",
          "description": "GÖTEBORGSVARVET!",
          "distance_km": 21.1,
          "note": "Njut av loppet!"
        },
        "sun": null
      }
    }
  ]
}
```

- [ ] **Step 2: Validate JSON is valid**

Run: `python3 -c "import json; json.load(open('plan.json')); print('Valid JSON')"`
Expected: `Valid JSON`

- [ ] **Step 3: Commit**

```bash
git add plan.json
git commit -m "Add plan.json: full 10-week training plan from PDF"
```

---

### Task 3: Create workouts.json with Seed Data

**Files:**
- Create: `workouts.json`

Seed with the three workouts already completed (March 19, 21, and 22).

- [ ] **Step 1: Create workouts.json**

```json
[
  {
    "date": "2026-03-19",
    "planned_week": "intro",
    "planned_day": "thu",
    "type": "running",
    "distance_km": 3,
    "duration_min": 20,
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

Note: The March 22 workout (4 km långpass) will be logged via `log.sh` once that's built. Leave it out for now — the user hasn't run it yet.

- [ ] **Step 2: Validate JSON**

Run: `python3 -c "import json; json.load(open('workouts.json')); print('Valid JSON')"`
Expected: `Valid JSON`

- [ ] **Step 3: Commit**

```bash
git add workouts.json
git commit -m "Add workouts.json: seed with first two workouts"
```

---

### Task 4: Create index.html — Page Shell, CSS, and Hero Section

**Files:**
- Create: `index.html`

Build the HTML document with all CSS, the hero section, and the JS data-loading skeleton. This task creates the file; subsequent tasks add sections.

- [ ] **Step 1: Create index.html with document structure, full CSS, and hero**

The file starts with the complete `<head>`, all CSS custom properties and styles, the hero section HTML, and the JS skeleton that fetches both JSON files.

Key CSS design decisions:
- Dark theme: `--bg: #0f172a`, `--surface: #1e293b`, `--text: #e2e8f0`
- Color coding: `--green: #22c55e` (done), `--blue: #3b82f6` (planned), `--purple: #8b5cf6` (bonus), `--grey: #475569` (rest), `--amber: #f59e0b` (race), `--red: #ef4444` (missed)
- Mobile-first responsive design
- System font stack: `system-ui, -apple-system, sans-serif`
- Chart.js loaded via CDN `<script>` tag

The hero renders:
- Race name and date
- Countdown (days + weeks) calculated from current date to race date

JS skeleton:
- `fetch('plan.json')` and `fetch('workouts.json')` on load
- Parse both, call `render(plan, workouts)` function
- `render()` calls section-specific functions: `renderHero()`, `renderProgress()`, `renderStats()`, `renderCurrentWeek()`, `renderAllWeeks()`, `renderChart()`
- Helper: `getWeekForDate(plan, date)` — returns which week a date falls in
- Helper: `getDayKey(date)` — returns `"mon"`, `"tue"`, etc.
- Helper: `getWorkoutsForWeek(workouts, weekId)` — filters workouts by `planned_week`
- Helper: `countPlannedSessions(week)` — counts non-null, non-rest days
- Helper: `countCompletedPlanned(workouts, weekId)` — counts workouts where `planned_week === weekId`
- Helper: `countBonusSessions(workouts, weekId, weekStartDate)` — counts workouts where `planned_week === null` within the week's date range

Write the full `index.html` with:
1. Complete `<!DOCTYPE html>` through `</html>`
2. All CSS in a `<style>` block (no external stylesheet)
3. Hero section HTML (race name, date, countdown placeholder)
4. Empty `<div>` containers with IDs for each section: `#progress`, `#stats`, `#current-week`, `#all-weeks`, `#chart`
5. `<script>` at the bottom with the fetch + render skeleton and all helper functions
6. `renderHero(plan)` fully implemented — fills in countdown

- [ ] **Step 2: Verify it loads in browser**

Run: `python3 -m http.server 8080 &` then open `http://localhost:8080` in browser.
Expected: Dark page with "Göteborgsvarvet 2026" header, countdown showing ~62 days, rest of page empty.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add index.html: page shell, CSS, hero with countdown"
```

---

### Task 5: index.html — Progress Bar and Stats Row

**Files:**
- Modify: `index.html`

Add the `renderProgress()` and `renderStats()` functions.

- [ ] **Step 1: Implement renderProgress(plan, workouts)**

Renders into `#progress`:
- Text: "Total framsteg: X av Y pass klara (Z%)"
- Horizontal progress bar (CSS: rounded, gradient fill `--blue` to `#60a5fa`)
- Calculation: X = total workouts with non-null `planned_week`, Y = total planned sessions across all elapsed weeks (weeks where `start_date <= today`), Z = X/Y as percentage

- [ ] **Step 2: Implement renderStats(plan, workouts)**

Renders into `#stats`:
- 4-column grid (2x2 on mobile via CSS media query)
- Cells: Km löpt (sum of all `distance_km`) | Pass klara (count all workouts) | Gympass (count where `type === "gym"`) | Följsamhet (adherence %)
- Each cell: large number on top, small uppercase label below

- [ ] **Step 3: Verify in browser**

Expected: Progress bar showing "1 av 1 pass klara" (1 planned session elapsed so far — Thu — and 1 logged for it). Stats row shows 5 km total, 2 pass, 0 gympass, 100% följsamhet.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Add progress bar and stats row"
```

---

### Task 6: index.html — Current Week Section

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Implement renderCurrentWeek(plan, workouts)**

Renders into `#current-week`:
- Header: week label, date range, phase, target km, "PÅGÅR" badge
- 7-day grid (Mon-Sun), each day as a card:
  - `null` day → dim empty cell with "—"
  - `rest` day → grey cell with "Vila"
  - Planned session (future) → blue outline, shows target distance + "IDAG" badge if today
  - Completed planned session → green background, checkmark, actual distance
  - Bonus session → purple background, star, actual distance
  - Missed session (planned, date passed, no workout logged) → red outline, "!"
- Count line below grid: "X/Y pass + Z extra" format

The day-card matching logic:
1. For each day of the week, check if there's a planned session in `plan.days[dayKey]`
2. Look for a matching workout in `workouts` where `planned_week === week.id && planned_day === dayKey`
3. Look for bonus workouts: `planned_week === null` and date falls within the week's date range and matches the day

- [ ] **Step 2: Verify in browser**

Expected: Intro week grid showing Thu with green checkmark (3 km), Sat with purple star (2 km bonus), Sun with blue outline (4 km planned, "IDAG").

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add current week section with day grid"
```

---

### Task 7: index.html — All Weeks Section

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Implement renderAllWeeks(plan, workouts)**

Renders into `#all-weeks`:
- Section header: "ALLA VECKOR"
- Compact list of all 10 weeks, each row contains:
  - Left: week label + phase subtitle
  - Right: completion count ("X/Y + Z extra") + mini progress bar (60px wide)
  - Current week: highlighted with blue left border, full opacity
  - Past weeks: show completion state, full opacity
  - Future weeks: dimmed (opacity 0.5), show only target km
- Each week row is clickable — toggles an expanded view showing the same 7-day grid as the current week section (reuse the day-card rendering logic, extract it into a shared function `renderDayGrid(week, workouts, container)`)

- [ ] **Step 2: Verify in browser**

Expected: List of all 10 weeks. Intro week highlighted with blue border and showing "1/2 + 1 extra". Future weeks dimmed with their target km.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add all weeks section with expandable week details"
```

---

### Task 8: index.html — Volume Chart

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Implement renderChart(plan, workouts)**

Renders into `#chart`:
- Section header: "KILOMETERVOLYM"
- `<canvas>` element for Chart.js bar chart
- Chart.js bar chart with:
  - X-axis: week labels (Intro, V1, V2, ..., V9)
  - Y-axis: km
  - Two datasets:
    1. "Planerat" — target km per week, dashed border, semi-transparent fill (`rgba(59,130,246,0.2)`)
    2. "Genomfört" — actual km logged per week, solid fill (`#3b82f6`)
  - For future weeks: only the planned bar shows
  - For past/current weeks: both bars show (grouped)
- Chart.js config: dark theme (grid lines `rgba(255,255,255,0.06)`, tick color `#64748b`), no legend border, responsive

- [ ] **Step 2: Verify in browser**

Expected: Bar chart showing intro week with a small blue solid bar (~5 km actual) alongside a dashed bar (~7 km planned). Future weeks show only dashed planned bars.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add volume chart with Chart.js"
```

---

### Task 9: index.html — Responsive Design Polish

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add responsive breakpoints**

Add CSS media queries if not already present:
- `max-width: 640px` (mobile):
  - Stats row: 2x2 grid instead of 4 columns
  - Day grid cells: smaller padding, smaller font
  - Chart: reduce height
  - Hero countdown: smaller font
- `max-width: 380px` (small mobile):
  - Day grid: abbreviate day labels to single letter (M, T, O, T, F, L, S)

- [ ] **Step 2: Add page footer**

Small footer at bottom:
- "Träningsplan för Göteborgsvarvet 2026"
- "Senast uppdaterad: [date of newest workout]"

- [ ] **Step 3: Test on mobile viewport**

Open browser DevTools, toggle device toolbar, test at 375px and 768px widths.
Expected: Clean layout at all breakpoints, no horizontal scroll, readable text.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Add responsive design and page footer"
```

---

### Task 10: Create log.sh — Workout Logging Script

**Files:**
- Create: `log.sh`

**Dependencies:** `bash`, `jq` (for JSON manipulation)

- [ ] **Step 1: Create log.sh**

The script must:

1. **Prompt for workout type** — numbered menu:
   ```
   Typ av pass:
     1) Löpning
     2) Långpass
     3) Tempo
     4) Gym
   ```

2. **Prompt for date** — default today, accept `YYYY-MM-DD` format:
   ```
   Datum [2026-03-22]:
   ```

3. **Auto-detect planned session** — read `plan.json`, find which week the date falls in, check if the day has a planned session. If yes, offer to link:
   ```
   Kopplat till plan? (Introvecka, tor — Löpning: 20 min lätt)
     j/n >
   ```
   If `j`: set `planned_week` and `planned_day`. If `n`: set both to `null`.

4. **Prompt for metrics based on type:**
   - Running/long_run/tempo: `distance_km`, `duration_min`, `rpe` (1-8), `note` (optional)
   - Gym: `duration_min`, then for each exercise in the planned session (or freeform if bonus): prompt for weight and reps per set. `note` (optional).

5. **Input validation:**
   - Distance: positive number
   - Duration: positive integer
   - RPE: integer 1-8
   - Date: valid `YYYY-MM-DD` format

6. **Append to workouts.json** using `jq`:
   ```bash
   jq ". += [$new_entry]" workouts.json > workouts.tmp && mv workouts.tmp workouts.json
   ```

7. **Print confirmation:**
   ```
   ✓ Sparat till workouts.json
     git add workouts.json && git commit -m "Logg: löpning 2026-03-22" && git push
   ```

8. **Optional `--push` flag:** If passed, auto-run the git add + commit + push.

- [ ] **Step 2: Make executable**

```bash
chmod +x log.sh
```

- [ ] **Step 3: Test the script**

Run: `./log.sh`
Walk through the prompts, log a test workout, verify `workouts.json` is correctly updated.
Then revert the test entry: `git checkout workouts.json`

- [ ] **Step 4: Commit**

```bash
git add log.sh
git commit -m "Add log.sh: interactive workout logging script"
```

---

### Task 11: Final Integration Verification

**Files:** None (verification only)

- [ ] **Step 1: Start local server and verify full page**

```bash
python3 -m http.server 8080
```

Open `http://localhost:8080`. Verify:
- Hero shows countdown
- Progress bar shows correct numbers
- Stats row shows correct totals
- Current week (intro) shows correct day states
- All weeks list renders correctly
- Volume chart shows intro week data
- Page looks good on mobile viewport (375px)

- [ ] **Step 2: Test log.sh end-to-end**

Run `./log.sh`, log the March 22 långpass (4 km). Refresh the page. Verify:
- Progress bar updates
- Stats update (km, session count)
- Intro week Sunday cell turns green with checkmark
- Volume chart intro bar grows

- [ ] **Step 3: Commit the logged workout**

```bash
git add workouts.json
git commit -m "Logg: långpass 2026-03-22"
```

- [ ] **Step 4: Set up GitHub Pages**

1. Create GitHub repo (if not already): `gh repo create goteborgsvarvet-2026 --public --source=. --push`
2. Enable GitHub Pages: `gh api repos/{owner}/goteborgsvarvet-2026/pages -X POST -f source.branch=main -f source.path=/`
3. Wait for deployment, verify live URL works

- [ ] **Step 5: Commit .gitignore update if needed, final push**

```bash
git push
```
