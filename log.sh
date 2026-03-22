#!/usr/bin/env bash
# log.sh — Loggningsverktyg för träningspass
# Loggar ett pass till workouts.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKOUTS_FILE="$SCRIPT_DIR/workouts.json"
PLAN_FILE="$SCRIPT_DIR/plan.json"
AUTO_PUSH=false

# ── Argument parsing ──────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --push) AUTO_PUSH=true ;;
    *) echo "Okänt argument: $arg" >&2; exit 1 ;;
  esac
done

# ── Beroendekontroll ──────────────────────────────────────────────────────────
if ! command -v jq &>/dev/null; then
  echo "Fel: 'jq' är inte installerat. Installera med: sudo apt install jq" >&2
  exit 1
fi

if [[ ! -f "$WORKOUTS_FILE" ]]; then
  echo "Fel: $WORKOUTS_FILE saknas." >&2
  exit 1
fi

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "Fel: $PLAN_FILE saknas." >&2
  exit 1
fi

# ── Hjälpfunktioner ───────────────────────────────────────────────────────────

# Validera YYYY-MM-DD och att datumet faktiskt existerar
validate_date() {
  local d="$1"
  if [[ ! "$d" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    return 1
  fi
  date -d "$d" +%Y-%m-%d &>/dev/null || return 1
  # Kontrollera att datumet inte rundas (t.ex. 2026-02-30 → mars)
  local normalized
  normalized=$(date -d "$d" +%Y-%m-%d 2>/dev/null)
  [[ "$normalized" == "$d" ]] || return 1
  return 0
}

# Validera positivt heltal
validate_positive_int() {
  local v="$1"
  [[ "$v" =~ ^[1-9][0-9]*$ ]]
}

# Validera positivt tal (decimaltal ok)
validate_positive_number() {
  local v="$1"
  [[ "$v" =~ ^[0-9]+([.][0-9]+)?$ ]] && (( $(echo "$v > 0" | bc -l) ))
}

# Validera RPE 1-8
validate_rpe() {
  local v="$1"
  [[ "$v" =~ ^[1-8]$ ]]
}

# Läs input med standardvärde
prompt_with_default() {
  local prompt="$1"
  local default="$2"
  local result
  read -r -p "$prompt" result
  echo "${result:-$default}"
}

# ── Steg 1: Typ av pass ───────────────────────────────────────────────────────
echo ""
echo "Typ av pass:"
echo "  1) Löpning"
echo "  2) Långpass"
echo "  3) Tempo"
echo "  4) Gym"
echo ""

WORKOUT_TYPE=""
while true; do
  read -r -p "Välj (1-4): " type_choice
  case "$type_choice" in
    1) WORKOUT_TYPE="running"; break ;;
    2) WORKOUT_TYPE="long_run"; break ;;
    3) WORKOUT_TYPE="tempo"; break ;;
    4) WORKOUT_TYPE="gym"; break ;;
    *) echo "Ogiltigt val, ange 1-4." ;;
  esac
done

# ── Steg 2: Datum ─────────────────────────────────────────────────────────────
TODAY=$(date +%Y-%m-%d)
WORKOUT_DATE=""
while true; do
  WORKOUT_DATE=$(prompt_with_default "Datum [$TODAY]: " "$TODAY")
  if validate_date "$WORKOUT_DATE"; then
    break
  else
    echo "Ogiltigt datum. Använd formatet YYYY-MM-DD (t.ex. $TODAY)."
  fi
done

# ── Steg 3: Hitta planerat pass ───────────────────────────────────────────────
# Bestäm veckodagsnyckel (1=mån … 7=sön → mon/tue/wed/thu/fri/sat/sun)
DOW_NUM=$(date -d "$WORKOUT_DATE" +%u)
case "$DOW_NUM" in
  1) DOW_KEY="mon" ;;
  2) DOW_KEY="tue" ;;
  3) DOW_KEY="wed" ;;
  4) DOW_KEY="thu" ;;
  5) DOW_KEY="fri" ;;
  6) DOW_KEY="sat" ;;
  7) DOW_KEY="sun" ;;
esac

# Räkna ut datum i sekunder för jämförelse
WORKOUT_TS=$(date -d "$WORKOUT_DATE" +%s)

PLANNED_WEEK_ID=""
PLANNED_DAY_KEY=""
PLANNED_LABEL=""
PLANNED_DESCRIPTION=""
PLANNED_EXERCISES_JSON="null"

# Iterera veckor och leta efter matchande vecka+dag
week_count=$(jq '.weeks | length' "$PLAN_FILE")
for (( i=0; i<week_count; i++ )); do
  week_start=$(jq -r ".weeks[$i].start_date" "$PLAN_FILE")
  week_start_ts=$(date -d "$week_start" +%s)
  week_end_ts=$(( week_start_ts + 7*24*3600 ))

  if (( WORKOUT_TS >= week_start_ts && WORKOUT_TS < week_end_ts )); then
    # Datumet faller i denna vecka
    week_id=$(jq -r ".weeks[$i].id" "$PLAN_FILE")
    week_label=$(jq -r ".weeks[$i].label" "$PLAN_FILE")

    # Kolla om det finns ett planerat pass för denna dag
    day_type=$(jq -r ".weeks[$i].days.$DOW_KEY.type // \"null\"" "$PLAN_FILE")

    if [[ "$day_type" != "null" && "$day_type" != "rest" && "$day_type" != "race" ]]; then
      PLANNED_WEEK_ID="$week_id"
      PLANNED_DAY_KEY="$DOW_KEY"
      PLANNED_LABEL="$week_label"
      PLANNED_DESCRIPTION=$(jq -r ".weeks[$i].days.$DOW_KEY.description // \"\"" "$PLAN_FILE")
      PLANNED_EXERCISES_JSON=$(jq -c ".weeks[$i].days.$DOW_KEY.exercises // null" "$PLAN_FILE")
    fi
    break
  fi
done

# Konvertera dagsnyckel till svenska
day_sv() {
  case "$1" in
    mon) echo "mån" ;;
    tue) echo "tis" ;;
    wed) echo "ons" ;;
    thu) echo "tor" ;;
    fri) echo "fre" ;;
    sat) echo "lör" ;;
    sun) echo "sön" ;;
    *) echo "$1" ;;
  esac
}

LINK_TO_PLAN=false
FINAL_PLANNED_WEEK="null"
FINAL_PLANNED_DAY="null"

if [[ -n "$PLANNED_WEEK_ID" ]]; then
  DAY_SV=$(day_sv "$PLANNED_DAY_KEY")
  echo ""
  echo "Kopplat till plan? ($PLANNED_LABEL, $DAY_SV — $PLANNED_DESCRIPTION)"
  while true; do
    read -r -p "  j/n > " link_choice
    case "${link_choice,,}" in
      j|ja)
        LINK_TO_PLAN=true
        FINAL_PLANNED_WEEK="\"$PLANNED_WEEK_ID\""
        FINAL_PLANNED_DAY="\"$PLANNED_DAY_KEY\""
        break
        ;;
      n|nej)
        LINK_TO_PLAN=false
        PLANNED_EXERCISES_JSON="null"
        break
        ;;
      *) echo "Ange j eller n." ;;
    esac
  done
fi

# ── Steg 4: Mätvärden ─────────────────────────────────────────────────────────

DURATION_MIN=""
NOTE=""

if [[ "$WORKOUT_TYPE" == "gym" ]]; then
  # Tid
  while true; do
    read -r -p "Tid (min): " DURATION_MIN
    if validate_positive_int "$DURATION_MIN"; then
      break
    else
      echo "Ange ett positivt heltal."
    fi
  done

  # Övningar
  EXERCISES_JSON="[]"

  if [[ "$LINK_TO_PLAN" == true && "$PLANNED_EXERCISES_JSON" != "null" ]]; then
    # Planerade övningar — loopa igenom var och en
    exercise_count=$(echo "$PLANNED_EXERCISES_JSON" | jq 'length')
    for (( ei=0; ei<exercise_count; ei++ )); do
      ex_name=$(echo "$PLANNED_EXERCISES_JSON" | jq -r ".[$ei].name")
      ex_sets=$(echo "$PLANNED_EXERCISES_JSON" | jq -r ".[$ei].sets")
      ex_reps=$(echo "$PLANNED_EXERCISES_JSON" | jq -r ".[$ei].reps")

      echo ""
      echo "$ex_name ($ex_sets set × $ex_reps reps):"

      sets_array="[]"
      for (( s=1; s<=ex_sets; s++ )); do
        # Vikt
        while true; do
          read -r -p "  Set $s - Vikt (kg): " kg_val
          if validate_positive_number "$kg_val"; then
            break
          else
            echo "  Ange ett positivt tal (decimaler ok)."
          fi
        done
        # Reps
        while true; do
          read -r -p "  Set $s - Reps: " reps_val
          if validate_positive_int "$reps_val"; then
            break
          else
            echo "  Ange ett positivt heltal."
          fi
        done
        sets_array=$(echo "$sets_array" | jq ". += [{\"reps\": $reps_val, \"kg\": $kg_val}]")
      done

      ex_obj=$(jq -n --arg name "$ex_name" --argjson sets "$sets_array" \
        '{"name": $name, "sets": $sets}')
      EXERCISES_JSON=$(echo "$EXERCISES_JSON" | jq ". += [$ex_obj]")
    done

  else
    # Bonuspass eller ej kopplat — fri inmatning av övningar
    echo ""
    echo "Ange övningar (lämna tomt för att avsluta):"
    while true; do
      read -r -p "  Övningsnamn (eller Enter för att avsluta): " ex_name
      [[ -z "$ex_name" ]] && break

      while true; do
        read -r -p "  Antal set: " ex_sets
        validate_positive_int "$ex_sets" && break
        echo "  Ange ett positivt heltal."
      done

      sets_array="[]"
      for (( s=1; s<=ex_sets; s++ )); do
        while true; do
          read -r -p "  Set $s - Vikt (kg): " kg_val
          validate_positive_number "$kg_val" && break
          echo "  Ange ett positivt tal."
        done
        while true; do
          read -r -p "  Set $s - Reps: " reps_val
          validate_positive_int "$reps_val" && break
          echo "  Ange ett positivt heltal."
        done
        sets_array=$(echo "$sets_array" | jq ". += [{\"reps\": $reps_val, \"kg\": $kg_val}]")
      done

      ex_obj=$(jq -n --arg name "$ex_name" --argjson sets "$sets_array" \
        '{"name": $name, "sets": $sets}')
      EXERCISES_JSON=$(echo "$EXERCISES_JSON" | jq ". += [$ex_obj]")
    done
  fi

  # Anteckning
  read -r -p "Anteckning (valfritt): " NOTE

else
  # Löpning / långpass / tempo
  DISTANCE_KM=""
  RPE=""

  while true; do
    read -r -p "Distans (km): " DISTANCE_KM
    if validate_positive_number "$DISTANCE_KM"; then
      break
    else
      echo "Ange ett positivt tal (decimaler ok, t.ex. 5.2)."
    fi
  done

  while true; do
    read -r -p "Tid (min): " DURATION_MIN
    if validate_positive_int "$DURATION_MIN"; then
      break
    else
      echo "Ange ett positivt heltal."
    fi
  done

  while true; do
    read -r -p "RPE (1-8): " RPE
    if validate_rpe "$RPE"; then
      break
    else
      echo "Ange ett heltal mellan 1 och 8."
    fi
  done

  read -r -p "Anteckning (valfritt): " NOTE
fi

# ── Steg 5: Bygg JSON-post och spara ─────────────────────────────────────────

# Bygg nytt post-objekt med jq
if [[ "$WORKOUT_TYPE" == "gym" ]]; then
  NEW_ENTRY=$(jq -n \
    --arg date "$WORKOUT_DATE" \
    --argjson planned_week "$FINAL_PLANNED_WEEK" \
    --argjson planned_day "$FINAL_PLANNED_DAY" \
    --arg type "$WORKOUT_TYPE" \
    --argjson duration_min "$DURATION_MIN" \
    --argjson exercises "$EXERCISES_JSON" \
    --arg note "$NOTE" \
    '{
      date: $date,
      planned_week: $planned_week,
      planned_day: $planned_day,
      type: $type,
      duration_min: $duration_min,
      exercises: $exercises,
      note: $note
    }')
else
  NEW_ENTRY=$(jq -n \
    --arg date "$WORKOUT_DATE" \
    --argjson planned_week "$FINAL_PLANNED_WEEK" \
    --argjson planned_day "$FINAL_PLANNED_DAY" \
    --arg type "$WORKOUT_TYPE" \
    --argjson distance_km "$DISTANCE_KM" \
    --argjson duration_min "$DURATION_MIN" \
    --argjson rpe "$RPE" \
    --arg note "$NOTE" \
    '{
      date: $date,
      planned_week: $planned_week,
      planned_day: $planned_day,
      type: $type,
      distance_km: $distance_km,
      duration_min: $duration_min,
      rpe: $rpe,
      note: $note
    }')
fi

# Lägg till i workouts.json
jq ". += [$NEW_ENTRY]" "$WORKOUTS_FILE" > "$WORKOUTS_FILE.tmp" \
  && mv "$WORKOUTS_FILE.tmp" "$WORKOUTS_FILE"

# ── Steg 6: Bekräftelse ───────────────────────────────────────────────────────

# Typnamn på svenska för commit-meddelandet
type_sv() {
  case "$1" in
    running)  echo "löpning" ;;
    long_run) echo "långpass" ;;
    tempo)    echo "tempo" ;;
    gym)      echo "gym" ;;
    *)        echo "$1" ;;
  esac
}

TYPE_SV=$(type_sv "$WORKOUT_TYPE")

echo ""
echo "✓ Sparat till workouts.json"
echo "  git add workouts.json && git commit -m \"Logg: $TYPE_SV $WORKOUT_DATE\" && git push"

# ── Steg 7 (valfritt): Auto-push ─────────────────────────────────────────────
if [[ "$AUTO_PUSH" == true ]]; then
  echo ""
  echo "Kör git add + commit + push..."
  cd "$SCRIPT_DIR"
  git add workouts.json
  git commit -m "Logg: $TYPE_SV $WORKOUT_DATE"
  git push
  echo "✓ Push klar."
fi
