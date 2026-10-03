import random

REFERENCE_WINDUP_S = 0.8


def attack_is_dodged(dodge_chance: float, windup_s: float, rng: random.Random) -> bool:
    effective_chance = min(0.95, dodge_chance * windup_s / REFERENCE_WINDUP_S)
    return rng.random() < effective_chance