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
    healing_until = None
    heals_used = 0
    time_spent_healing_s = 0.0
    damage_in_recovery = 0
    while enemy_health > 0 and player_health > 0 and time_s < max_time_s:
        if healing_until is not None and time_s >= healing_until:
            player_health = min(
                player_rules["player_max_health"],
                player_health + player_rules["heal_amount"],
            )
            healing_until = None
        if (
            healing_until is None
            and heals_used < player_rules["max_heals"]
            and player_health < style["heal_below_health_fraction"] * player_rules["player_max_health"]
        ):
            healing_until = time_s + player_rules["heal_time_s"]
            heals_used += 1
            time_spent_healing_s += player_rules["heal_time_s"]
        if healing_until is None and time_s >= next_attack_time_s:
            if target_phase is None:
                target_phase = pick_attack_phase(style["attack_phase_weights"], rng)
            if enemy_phase_at(time_s, schedule) == target_phase:
                enemy_health -= player_rules["damage_per_hit"]
                next_attack_time_s = time_s + style["attack_interval_s"]
                if target_phase == "recovery":
                    damage_in_recovery += player_rules["damage_per_hit"]
                target_phase = None
        if enemy_health > 0 and next_strike < len(schedule) and time_s >= schedule[next_strike]["strike_time"]:
            player_dodged = healing_until is None and attack_is_dodged(
                style["dodge_chance"], tunables["windup_s"], rng
            )
            if not player_dodged:
                player_health -= tunables["damage"]
                damage_taken += tunables["damage"]
            next_strike += 1
        time_s += TIME_STEP_S
    return {
        "duration_s": round(time_s, 2),
        "won": enemy_health <= 0,
        "damage_taken": damage_taken,
        "damage_in_recovery": damage_in_recovery,
        "heals_used": heals_used,
        "time_spent_healing_s": round(time_spent_healing_s, 2),
    }

def generate_telemetry(
    tunables: dict,
    player_rules: dict,
    players_per_style: int,
    attempts_per_player: int,
    seed: int,
) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for style_name, style in player_rules["styles"].items():
        for player_number in range(1, players_per_style + 1):
            for attempt in range(1, attempts_per_player + 1):
                result = simulate_fight(tunables, player_rules, style, rng)
                rows.append({
                    "player_id": f"{style_name}_{player_number}",
                    "player_style": style_name,
                    "attempt": attempt,
                    **result,
                })
    return rows