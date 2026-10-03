import random

REFERENCE_WINDUP_S = 0.8
TIME_STEP_S = 0.05


def attack_is_dodged(dodge_chance: float, windup_s: float, rng: random.Random) -> bool:
    effective_chance = min(0.95, dodge_chance * windup_s / REFERENCE_WINDUP_S)
    return rng.random() < effective_chance

def build_enemy_schedule(tunables: dict, fight_length_s: float, rng: random.Random) -> list[dict]:
    schedule = []
    time_s = 0.0
    while True:
        windup_start = time_s + rng.uniform(tunables["approach_min_s"], tunables["approach_max_s"])
        if windup_start >= fight_length_s:
            return schedule
        strike_time = windup_start + tunables["windup_s"]
        recovery_end = strike_time + tunables["recovery_s"]
        schedule.append({
            "windup_start": windup_start,
            "strike_time": strike_time,
            "recovery_end": recovery_end,
        })
        time_s = recovery_end

def enemy_phase_at(time_s: float, schedule: list[dict]) -> str:
    for attack in schedule:
        if attack["windup_start"] <= time_s < attack["strike_time"]:
            return "windup"
        if attack["strike_time"] <= time_s < attack["recovery_end"]:
            return "recovery"
    return "approach"

def pick_attack_phase(weights: dict, rng: random.Random) -> str:
    return rng.choices(list(weights), weights=list(weights.values()))[0]

def simulate_fight(
    tunables: dict,
    player_rules: dict,
    style: dict,
    rng: random.Random,
    max_time_s: float = 120.0,
) -> dict:
    schedule = build_enemy_schedule(tunables, max_time_s, rng)
    enemy_health = tunables["health"]
    player_health = player_rules["player_max_health"]
    damage_taken = 0
    next_strike = 0
    time_s = 0.0
    next_attack_time_s = 0.0
    target_phase = None
    while enemy_health > 0 and player_health > 0 and time_s < max_time_s:
        if time_s >= next_attack_time_s:
            if target_phase is None:
                target_phase = pick_attack_phase(style["attack_phase_weights"], rng)
            if enemy_phase_at(time_s, schedule) == target_phase:
                enemy_health -= style["damage_per_hit"]
                next_attack_time_s = time_s + style["attack_interval_s"]
                target_phase = None
        if enemy_health > 0 and next_strike < len(schedule) and time_s >= schedule[next_strike]["strike_time"]:
            if not attack_is_dodged(style["dodge_chance"], tunables["windup_s"], rng):
                player_health -= tunables["damage"]
                damage_taken += tunables["damage"]
            next_strike += 1
        time_s += TIME_STEP_S
    return {
        "duration_s": round(time_s, 2),
        "won": enemy_health <= 0,
        "damage_taken": damage_taken,
    }