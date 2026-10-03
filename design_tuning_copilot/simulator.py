import random

REFERENCE_WINDUP_S = 0.8


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