def success_rate(rows: list[dict]) -> float:
    wins = sum(1 for row in rows if row["won"])
    return wins / len(rows)


def average_time_to_kill(rows: list[dict]) -> float | None:
    win_times = [row["duration_s"] for row in rows if row["won"]]
    if not win_times:
        return None
    return sum(win_times) / len(win_times)