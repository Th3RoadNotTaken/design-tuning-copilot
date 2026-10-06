import statistics
import math

def average_time_to_kill(rows: list[dict]) -> float | None:
    win_times = [row["duration_s"] for row in rows if row["won"]]
    if not win_times:
        return None
    return sum(win_times) / len(win_times)

def first_win_attempts(rows: list[dict]) -> dict[str, int | None]:
    first = {}
    for row in rows:
        player = row["player_id"]
        first.setdefault(player, None)
        if row["won"] and (first[player] is None or row["attempt"] < first[player]):
            first[player] = row["attempt"]
    return first

def first_win_summary(rows: list[dict], style: str, max_attempt: int = 40) -> dict:
    first = first_win_attempts([r for r in rows if r["player_style"] == style])
    attempts = list(first.values())
    wins = sorted(a for a in attempts if a is not None)
    return {
        "players": len(attempts),
        "median_first_win": statistics.median(wins) if wins else None,
        "share_before_attempt_5": sum(1 for a in wins if a < 5) / len(attempts),
        "share_never_won": sum(1 for a in attempts if a is None) / len(attempts),
    }

def check_against_target(value: float | None, target: dict) -> dict:
    if value is None:
        return {"status": "no_data", "gap": None}
    if "min" in target and value < target["min"]:
        return {"status": "too_low", "gap": value - target["min"]}
    if "max" in target and value > target["max"]:
        return {"status": "too_high", "gap": value - target["max"]}
    return {"status": "on_target", "gap": 0.0}

def win_rate_by_attempt(rows: list[dict], style: str) -> dict[int, float]:
    totals = {}
    wins = {}
    for row in rows:
        if row["player_style"] != style:
            continue
        attempt = row["attempt"]
        totals[attempt] = totals.get(attempt, 0) + 1
        wins[attempt] = wins.get(attempt, 0) + (1 if row["won"] else 0)
    return {attempt: wins[attempt] / totals[attempt] for attempt in sorted(totals)}

def late_win_rate(rows: list[dict], style: str, from_attempt: int = 30) -> float | None:
    late = [r for r in rows if r["player_style"] == style and r["attempt"] >= from_attempt]
    if not late:
        return None
    return sum(1 for r in late if r["won"]) / len(late)

def relapse_rate(rows: list[dict], style: str) -> float | None:
    by_player = {}
    for row in rows:
        if row["player_style"] == style:
            by_player.setdefault(row["player_id"], []).append(row)
    fights_after_first_win = 0
    losses = 0
    for fights in by_player.values():
        outcomes = [f["won"] for f in sorted(fights, key=lambda f: f["attempt"])]
        if True not in outcomes:
            continue
        after = outcomes[outcomes.index(True):]
        fights_after_first_win += len(after)
        losses += sum(1 for won in after if not won)
    if fights_after_first_win == 0:
        return None
    return losses / fights_after_first_win

def target_for(targets: dict, style: str, name: str) -> dict:
    return targets.get("by_style", {}).get(style, {}).get(name, targets.get(name))

TUNABLE_ENEMY = ("health", "damage", "windup_s", "recovery_s")
TUNABLE_PLAYER = ("player_max_health", "damage_per_hit", "heal_amount", "max_heals")
FIRST_WIN_METRICS = ("median_first_win", "share_before_attempt_5", "share_never_won")

def hits_to_kill(health: float, damage_per_hit: float) -> int:
    return math.ceil(health / damage_per_hit)

def build_report(rows: list[dict], targets: dict, enemy: dict, player: dict) -> dict:
    ttk = average_time_to_kill(rows)
    by_style = {}
    for style in player["styles"]:
        summary = first_win_summary(rows, style)
        values = {
            **{name: summary[name] for name in FIRST_WIN_METRICS},
            "late_win_rate": late_win_rate(rows, style),
            "relapse_rate": relapse_rate(rows, style),
        }
        by_style[style] = {"players": summary["players"]}
        for name, value in values.items():
            target = target_for(targets, style, name)
            by_style[style][name] = {
                "value": value,
                "target": target,
                **check_against_target(value, target),
            }
    enemy_hits = hits_to_kill(player["player_max_health"], enemy["damage"])
    player_hits = hits_to_kill(enemy["health"], player["damage_per_hit"])
    return {
        "difficulty": targets["difficulty"],
        "tunable": {
            "enemy": {key: enemy[key] for key in TUNABLE_ENEMY},
            "player": {key: player[key] for key in TUNABLE_PLAYER},
        },
        "read_only": {
            "enemy": {k: v for k, v in enemy.items() if k not in TUNABLE_ENEMY},
            "player": {
                k: v for k, v in player.items()
                if k not in TUNABLE_PLAYER and k != "styles"
            },
            "player_styles": player["styles"],
        },
        "overall": {
            "time_to_kill_s": {
                "value": ttk,
                "target": targets["time_to_kill_s"],
                **check_against_target(ttk, targets["time_to_kill_s"]),
            },
            "enemy_hits_to_kill_player": {
                "value": enemy_hits,
                "target": targets["enemy_hits_to_kill_player"],
                **check_against_target(enemy_hits, targets["enemy_hits_to_kill_player"]),
            },
            "player_hits_to_kill_enemy": {
                "value": player_hits,
                "target": targets["player_hits_to_kill_enemy"],
                **check_against_target(player_hits, targets["player_hits_to_kill_enemy"]),
            },
        },
        "by_style": by_style,
    }