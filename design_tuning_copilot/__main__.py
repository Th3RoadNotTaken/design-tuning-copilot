from design_tuning_copilot.loaders import load_json
from design_tuning_copilot.simulator import generate_telemetry
from design_tuning_copilot.telemetry import write_telemetry_csv


def main() -> None:
    tunables = load_json("data/tunables.json")
    player_rules = load_json("data/player_styles.json")
    rows = generate_telemetry(
        tunables,
        player_rules,
        players_per_style=10,
        attempts_per_player=3,
        seed=42,
    )
    write_telemetry_csv(rows, "data/telemetry_before.csv")
    print(f"Wrote {len(rows)} fights to data/telemetry_before.csv")


if __name__ == "__main__":
    main()