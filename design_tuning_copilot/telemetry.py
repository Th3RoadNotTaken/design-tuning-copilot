import csv
from pathlib import Path


def write_telemetry_csv(rows: list[dict], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def read_telemetry_csv(path: str | Path) -> list[dict]:
    rows = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            rows.append({
                "player_id": raw["player_id"],
                "player_style": raw["player_style"],
                "attempt": int(raw["attempt"]),
                "duration_s": float(raw["duration_s"]),
                "won": raw["won"] == "True",
                "damage_taken": float(raw["damage_taken"]),
                "damage_in_recovery": float(raw["damage_in_recovery"]),
                "heals_used": int(raw["heals_used"]),
                "time_spent_healing_s": float(raw["time_spent_healing_s"]),
            })
    return rows