import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from design_tuning_copilot.metrics import win_rate_by_attempt

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