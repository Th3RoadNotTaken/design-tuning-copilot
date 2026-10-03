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

def simulate_fight(tunables: dict, style: dict, max_time_s: float = 120.0) -> float:
    enemy_health = tunables["health"]
    time_s = 0.0
    next_attack_s = 0.0
    while enemy_health > 0 and time_s < max_time_s:
        if time_s >= next_attack_s:
            enemy_health -= style["damage_per_hit"]
            next_attack_s += style["attack_interval_s"]
        time_s += TIME_STEP_S
    return time_s