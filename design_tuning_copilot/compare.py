from design_tuning_copilot.metrics import build_report
from design_tuning_copilot.simulator import generate_telemetry


def simulate_and_report(enemy: dict, player: dict, targets: dict) -> dict:
    rows = generate_telemetry(
        enemy,
        player,
        players_per_style=10,
        attempts_per_player=3,
        seed=42,
    )
    return build_report(rows, targets, enemy, player)