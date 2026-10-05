from design_tuning_copilot.metrics import build_report
from design_tuning_copilot.simulator import generate_telemetry
from design_tuning_copilot.suggestions import apply_suggestions, suggest_changes


def simulate_and_report(enemy: dict, player: dict, targets: dict) -> dict:
    rows = generate_telemetry(
    enemy,
    player,
    players_per_style=30,
    attempts_per_player=40,
    seed=42,
    )
    return build_report(rows, targets, enemy, player)

def tune(enemy: dict, player: dict, targets: dict) -> dict:
    before = simulate_and_report(enemy, player, targets)
    suggestions = suggest_changes(before)
    new_enemy, new_player = apply_suggestions(enemy, player, suggestions)
    after = simulate_and_report(new_enemy, new_player, targets)
    return {"suggestions": suggestions, "before": before, "after": after}

def format_run(result: dict) -> str:
    lines = []
    if not result["history"]:
        lines.append("Already on target, no changes needed.")
    for entry in result["history"]:
        lines.append(f"Round {entry['round']}:")
        for change in entry["changes"]:
            lines.append(f"- {change['parameter']} -> {change['new_value']}: {change['reason']}")
        lines.append("")
    lines.append("Settings changed overall (before -> after):")
    for group in ("enemy", "player"):
        old = result["before"]["tunable"][group]
        new = result["after"]["tunable"][group]
        for name, old_value in old.items():
            if new[name] != old_value:
                lines.append(f"- {group}.{name}: {old_value} -> {new[name]}")
    lines.append("")
    lines.append("Overall results (before -> after):")
    for metric, before in result["before"]["overall"].items():
        after = result["after"]["overall"][metric]
        lines.append(
            f"- {metric}: {before['value']:g} ({before['status']}) -> "
            f"{after['value']:g} ({after['status']}), target {before['target']}"
        )
    lines.append("")
    lines.append("First-win results by player type (before -> after):")
    for style, metrics in result["before"]["by_style"].items():
        lines.append(f"{style}:")
        for name in ("median_first_win", "share_before_attempt_5", "share_never_won", "late_win_rate"):
            old = metrics[name]
            new = result["after"]["by_style"][style][name]
            lines.append(
                f"- {name}: {old['value']} ({old['status']}) -> "
                f"{new['value']} ({new['status']}), target {old['target']}"
            )
    return "\n".join(lines)

def all_on_target(report: dict) -> bool:
    metrics = list(report["overall"].values())
    for style_metrics in report["by_style"].values():
        metrics += [m for key, m in style_metrics.items() if key != "players"]
    return all(metric["status"] == "on_target" for metric in metrics)

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
            {
                "round": round_number,
                "changes": suggestions,
                "results_after": {
                    "overall": current["overall"],
                    "by_style": current["by_style"],
                },
            }
        )
    return {
        "before": initial,
        "after": current,
        "history": history,
        "final_enemy": enemy,
        "final_player": player,
    }