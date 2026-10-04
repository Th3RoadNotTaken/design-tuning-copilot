import json

from design_tuning_copilot.charts import plot_before_after
from design_tuning_copilot.compare import format_run, tune_iteratively
from design_tuning_copilot.loaders import load_json
from design_tuning_copilot.simulator import generate_telemetry
from design_tuning_copilot.telemetry import write_telemetry_csv


def main() -> None:
    tunables = load_json("data/enemy.json")
    player_rules = load_json("data/players.json")
    targets = load_json("data/targets.json")
    before_rows = generate_telemetry(
        tunables,
        player_rules,
        players_per_style=30,
        attempts_per_player=40,
        seed=42,
    )
    write_telemetry_csv(before_rows, "data/telemetry_before.csv")
    print(f"Wrote {len(before_rows)} fights to data/telemetry_before.csv")

    result = tune_iteratively(tunables, player_rules, targets)
    print()
    print(format_run(result))
    final_enemy = result["final_enemy"]
    final_player = result["final_player"]
    after_rows = generate_telemetry(
        final_enemy,
        final_player,
        players_per_style=30,
        attempts_per_player=40,
        seed=42,
    )
    write_telemetry_csv(after_rows, "data/telemetry_after.csv")
    with open("data/enemy_tuned.json", "w") as file:
        json.dump(final_enemy, file, indent=2)
    with open("data/players_tuned.json", "w") as file:
        json.dump(final_player, file, indent=2)
    plot_before_after(before_rows, after_rows, "learning_curves.png")
    print()
    print("Wrote data/telemetry_after.csv, data/enemy_tuned.json, data/players_tuned.json")
    print("Wrote learning_curves.png")


if __name__ == "__main__":
    main()