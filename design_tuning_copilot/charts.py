import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from design_tuning_copilot.metrics import win_rate_by_attempt
from matplotlib.colors import ListedColormap

STYLE_COLORS = {"aggressive": "#d95f02", "cautious": "#1b9e77"}

def plot_learning_curves(rows: list[dict], path: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    for style, color in STYLE_COLORS.items():
        curve = win_rate_by_attempt(rows, style)
        ax.plot(list(curve.keys()), list(curve.values()), label=style, color=color)
    ax.axvspan(10, 25, color="grey", alpha=0.15, label="target first-win window")
    ax.set_xlabel("Attempt")
    ax.set_ylabel("Win rate")
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)

def plot_before_after(before_rows: list[dict], after_rows: list[dict], path: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, rows, title in ((axes[0], before_rows, "Before tuning"), (axes[1], after_rows, "After tuning")):
        for style, color in STYLE_COLORS.items():
            curve = win_rate_by_attempt(rows, style)
            ax.plot(list(curve.keys()), list(curve.values()), label=style, color=color)
        ax.axvspan(10, 25, color="grey", alpha=0.15, label="target first-win window")
        ax.set_xlabel("Attempt")
        ax.set_title(title)
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Win rate")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)

def plot_player_view(rows: list[dict], path: str, max_players: int = 30) -> None:
    styles = list(STYLE_COLORS)
    fig, axes = plt.subplots(len(styles), 1, figsize=(10, 7), sharex=True)
    for ax, style in zip(axes, styles):
        by_player = {}
        for row in rows:
            if row["player_style"] == style:
                by_player.setdefault(row["player_id"], []).append(row)

        grids = []
        for fights in list(by_player.values())[:max_players]:
            ordered = sorted(fights, key=lambda f: f["attempt"])
            grids.append([1 if f["won"] else 0 for f in ordered])
        # Earliest winners at the top.
        grids.sort(key=lambda g: g.index(1) if 1 in g else len(g))

        cmap = ListedColormap(["#e6e6e6", STYLE_COLORS[style]])
        attempts = len(grids[0])
        ax.imshow(
            grids,
            aspect="auto",
            cmap=cmap,
            vmin=0,
            vmax=1,
            interpolation="nearest",
            extent=(0.5, attempts + 0.5, len(grids), 0),
        )
        ax.set_title(f"{style}: one row per player, coloured cell = win")
        ax.set_ylabel("Players")
        ax.set_yticks([])
    axes[-1].set_xlabel("Attempt")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)