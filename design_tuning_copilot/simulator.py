import random

TIME_STEP_S = 0.05

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

def blend(start: float, end: float, skill: float) -> float:
    return start + (end - start) * skill

def attack_probability(style: dict, phase: str, skill: float) -> float:
    chances = style["attack_probability"]
    return blend(chances["start"][phase], chances["end"][phase], skill)

def dodge_weights(style: dict, skill: float) -> dict:
    weights = style["dodge_weights"]
    return {
        phase: blend(weights["start"][phase], weights["end"][phase], skill)
        for phase in weights["start"]
    }

def pick_dodge_phase(style: dict, skill: float, rng: random.Random) -> str:
    weights = dodge_weights(style, skill)
    return rng.choices(list(weights), weights=list(weights.values()))[0]

def plan_dodge(
    schedule: list[dict], index: int, style: dict, learning: dict, skill: float, rng: random.Random
) -> float | None:
    phase = pick_dodge_phase(style, skill, rng)
    if phase == "none":
        return None
    attack = schedule[index]
    previous_end = schedule[index - 1]["recovery_end"] if index > 0 else 0.0
    if phase == "windup":
        fractions = learning["dodge_start_fraction"]
        spreads = learning["dodge_start_spread"]
        mean = blend(fractions["skill_0"], fractions["skill_1"], skill)
        spread = blend(spreads["skill_0"], spreads["skill_1"], skill)
        fraction = min(1.0, max(0.0, rng.gauss(mean, spread)))
        return attack["windup_start"] + fraction * (attack["strike_time"] - attack["windup_start"])
    if phase == "approach" or index == 0:
        return rng.uniform(previous_end, attack["windup_start"])
    previous = schedule[index - 1]
    return rng.uniform(previous["strike_time"], previous["recovery_end"])

def dodge_covers(start: float | None, strike_time: float, duration_s: float) -> bool:
    return start is not None and start <= strike_time < start + duration_s

def skill_at_attempt(learning_rate: float, skill_cap: float, attempt: int) -> float:
    return skill_cap * (1 - (1 - learning_rate) ** (attempt - 1))

def simulate_fight(
    tunables: dict,
    player_rules: dict,
    style: dict,
    rng: random.Random,
    max_time_s: float = 120.0,
    skill: float = 0.0,
) -> dict:
    schedule = build_enemy_schedule(tunables, max_time_s, rng)
    dodge_plans = [
        plan_dodge(schedule, i, style, player_rules["learning"], skill, rng)
        for i in range(len(schedule))
    ]
    dodge_starts = []
    dodge_ready_at = 0.0
    next_dodge = 0
    enemy_health = tunables["health"]
    player_health = player_rules["player_max_health"]
    damage_taken = 0
    next_strike = 0
    time_s = 0.0
    next_attack_time_s = 0.0
    attack_ends_at = 0.0
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
        if next_dodge < len(dodge_plans):
            planned = dodge_plans[next_dodge]
            if planned is None:
                next_dodge += 1
            elif time_s >= planned:
                if healing_until is None and time_s >= dodge_ready_at and time_s >= attack_ends_at:
                    dodge_starts.append(planned)
                    dodge_ready_at = (
                        planned + player_rules["dodge_duration_s"] + player_rules["dodge_recovery_s"]
                    )
                next_dodge += 1
        if healing_until is None and time_s >= dodge_ready_at and time_s >= next_attack_time_s:
            phase = enemy_phase_at(time_s, schedule)
            if rng.random() < attack_probability(style, phase, skill):
                enemy_health -= player_rules["damage_per_hit"]
                next_attack_time_s = time_s + player_rules["attack_gap_s"]
                attack_ends_at = next_attack_time_s
                if phase == "recovery":
                    damage_in_recovery += player_rules["damage_per_hit"]
            else:
                next_attack_time_s = time_s + player_rules["attack_check_interval_s"]
        if enemy_health > 0 and next_strike < len(schedule) and time_s >= schedule[next_strike]["strike_time"]:
            strike_time = schedule[next_strike]["strike_time"]
            player_dodged = any(
                dodge_covers(start, strike_time, player_rules["dodge_duration_s"])
                for start in dodge_starts
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
    learning = player_rules["learning"]
    rows = []
    for style_name, style in player_rules["styles"].items():
        for player_number in range(1, players_per_style + 1):
            rng = random.Random(f"{seed}-{style_name}-{player_number}")
            learning_rate = rng.uniform(
                learning["learning_rate_min"], learning["learning_rate_max"]
            )
            for attempt in range(1, attempts_per_player + 1):
                skill = skill_at_attempt(learning_rate, learning["skill_cap"], attempt)
                result = simulate_fight(tunables, player_rules, style, rng, skill=skill)
                rows.append({
                    "player_id": f"{style_name}_{player_number}",
                    "player_style": style_name,
                    "attempt": attempt,
                    "skill": round(skill, 3),
                    **result,
                })
    return rows