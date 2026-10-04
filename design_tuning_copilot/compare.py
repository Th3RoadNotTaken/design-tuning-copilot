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

def format_comparison(result: dict) -> str:
    lines = ["Suggested changes:"]
    for s in result["suggestions"]:
        lines.append(f"- {s['parameter']} -> {s['new_value']}: {s['reason']}")
    lines.append("")
    lines.append("Overall results (before -> after):")
    for metric in ("time_to_kill_s", "success_rate"):
        before = result["before"]["overall"][metric]
        after = result["after"]["overall"][metric]
        lines.append(
            f"- {metric}: {before['value']:.2f} ({before['status']}) -> "
            f"{after['value']:.2f} ({after['status']}), "
            f"target {before['target']['min']} to {before['target']['max']}"
        )
    lines.append("")
    lines.append("Success rate by style (before -> after):")
    for style, stats in result["before"]["by_style"].items():
        after_rate = result["after"]["by_style"][style]["success_rate"]
        lines.append(f"- {style}: {stats['success_rate']:.0%} -> {after_rate:.0%}")
    return "\n".join(lines)

def all_on_target(report: dict) -> bool:
    return all(metric["status"] == "on_target" for metric in report["overall"].values())

def tune_iteratively(enemy: dict, player: dict, targets: dict, max_rounds: int = 3) -> dict:
    initial = simulate_and_report(enemy, player, targets)
    current = initial
    history = []
    for round_number in range(1, max_rounds + 1):
        if all_on_target(current):
            break
        suggestions = suggest_changes(current, history)
        enemy, player = apply_suggestions(enemy, player, suggestions)
        current = simulate_and_report(enemy, player, targets)
        history.append(
            {"round": round_number, "changes": suggestions, "overall_after": current["overall"]}
        )
    return {"before": initial, "after": current, "history": history}