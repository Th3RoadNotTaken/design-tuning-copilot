from design_tuning_copilot.metrics import build_report
from design_tuning_copilot.simulator import generate_telemetry
from design_tuning_copilot.suggestions import apply_suggestions, suggest_changes


def simulate_and_report(enemy: dict, player: dict, targets: dict) -> dict:
    rows = generate_telemetry(
        enemy,
        player,
        players_per_style=10,
        attempts_per_player=3,
        seed=42,
    )
    return build_report(rows, targets, enemy, player)

def tune(enemy: dict, player: dict, targets: dict) -> dict:
    before = simulate_and_report(enemy, player, targets)
    suggestions = suggest_changes(before)
    new_enemy, new_player = apply_suggestions(enemy, player, suggestions)
    after = simulate_and_report(new_enemy, new_player, targets)
    return {"suggestions": suggestions, "before": before, "after": after}