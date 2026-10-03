def success_rate(rows: list[dict]) -> float:
    wins = sum(1 for row in rows if row["won"])
    return wins / len(rows)

def win_count(rows: list[dict]) -> int:
    return sum(1 for row in rows if row["won"])

def average_time_to_kill(rows: list[dict]) -> float | None:
    win_times = [row["duration_s"] for row in rows if row["won"]]
    if not win_times:
        return None
    return sum(win_times) / len(win_times)

def check_against_target(value: float | None, target: dict) -> dict:
    if value is None:
        return {"status": "no_data", "gap": None}
    if value < target["min"]:
        return {"status": "too_low", "gap": value - target["min"]}
    if value > target["max"]:
        return {"status": "too_high", "gap": value - target["max"]}
    return {"status": "on_target", "gap": 0.0}

def group_by_style(rows: list[dict]) -> dict[str, list[dict]]:
    groups = {}
    for row in rows:
        groups.setdefault(row["player_style"], []).append(row)
    return groups

def summarize_by_style(rows: list[dict]) -> dict[str, dict]:
    summary = {}
    for name, group in group_by_style(rows).items():
        summary[name] = {
            "fights": len(group),
            "wins": win_count(group),
            "success_rate": success_rate(group),
            "avg_time_to_kill": average_time_to_kill(group),
        }
    return summary