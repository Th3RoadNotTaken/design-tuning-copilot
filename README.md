# Design Tuning Copilot

Reads combat-encounter playtest telemetry, compares it to design targets
(time to kill, success rate), asks an LLM for specific tuning changes with
reasons, then re-simulates to show before and after.

All data in this repo is simulated. Nothing comes from a shipped game.

## Status

- [x] Data formats and sample data
- [x] Combat simulator with player styles that generates telemetry
- [ ] Metrics and comparison against targets
- [ ] LLM tuning suggestions
- [ ] Apply suggestions, re-simulate, before and after report

## Run it

From the repo root, with Python 3.10+:

    py -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m design_tuning_copilot

This writes `data/telemetry_before.csv` with 120 simulated fights. The random
seed is fixed, so every run gives the same file.

## Data files (in `data/`)

- `tunables.json`: enemy values a designer can change (health, damage, approach
  time range, windup, recovery).
- `targets.json`: what the designer wants (time to kill range, success rate range).
- `player_styles.json`: shared player rules (health, damage per hit, heal time,
  heal amount, number of heals) and per-style behavior (dodge chance, swing
  interval, when to heal, which enemy phase to attack in).
- `telemetry_before.csv`: one row per fight. Columns: player, style, attempt,
  duration, won, damage taken, damage dealt in the enemy's recovery window,
  heals used, time spent healing.

## How the simulator works

The enemy repeats approach, windup, strike, recovery. The approach time is random
within a range. The strike lands at the end of the windup, and the player gets a
dodge roll that gets easier as the windup gets longer. Players swing at the enemy
in the phase their style prefers, and heal when their health drops below their
style's threshold. A player cannot attack or dodge while healing.

## Limitations

- The dodge rule is invented, not taken from real combat data.
- Positions are not tracked, so players are assumed to be able to hit an
  approaching enemy.
- Time moves in 50 ms steps.
- Players do not learn between attempts.
- Heals always succeed and cannot be cancelled.

## What the AI part does and doesn't do

Planned: the LLM will only propose tuning changes, each with a reason and the
metric it should move. It does not know the game, and every suggestion is checked
by re-running the simulator.
