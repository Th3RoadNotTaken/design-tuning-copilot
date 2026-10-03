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

def build_report(rows: list[dict], targets: dict, enemy: dict, player: dict) -> dict:
    ttk = average_time_to_kill(rows)
    rate = success_rate(rows)
    shared_rules = {key: value for key, value in player.items() if key != "styles"}
    return {
        "difficulty": targets["difficulty"],
        "tunable": {
            "enemy": enemy,
            "player": shared_rules,
        },
        "read_only_player_styles": player["styles"],
        "overall": {
            "time_to_kill_s": {
                "value": ttk,
                "target": targets["time_to_kill_s"],
                **check_against_target(ttk, targets["time_to_kill_s"]),
            },
            "success_rate": {
                "value": rate,
                "target": targets["success_rate"],
                **check_against_target(rate, targets["success_rate"]),
            },
        },
        "by_style": summarize_by_style(rows),
    }