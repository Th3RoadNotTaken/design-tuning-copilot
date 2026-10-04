import json
import anthropic
import copy

MODEL = "claude-sonnet-5-5"

def allowed_parameters(report: dict) -> set[str]:
    allowed = set()
    for group, values in report["tunable"].items():
        for name, value in values.items():
            if isinstance(value, (int, float)):
                allowed.add(f"{group}.{name}")
    return allowed

def validate_suggestion(suggestion: dict, allowed: set[str]) -> list[str]:
    problems = []
    for field in ("parameter", "new_value", "reason"):
        if field not in suggestion:
            problems.append(f"missing field: {field}")
    if problems:
        return problems
    if suggestion["parameter"] not in allowed:
        problems.append(f"unknown parameter: {suggestion['parameter']}")
    value = suggestion["new_value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        problems.append("new_value must be a number")
    if not isinstance(suggestion["reason"], str) or not suggestion["reason"].strip():
        problems.append("reason must be a non-empty string")
    return problems

PARAMETER_NOTES = {
    "enemy.health": "Total enemy health. More health means longer fights and more enemy strikes per fight.",
    "enemy.damage": "Damage of each enemy strike. Compare it with player.player_max_health to see how many hits a player survives.",
    "enemy.windup_s": "Seconds between the start of the enemy's wind-up and its strike. A longer wind-up gives players more time to learn the dodge timing; a shorter one is harder.",
    "enemy.recovery_s": "Seconds the enemy is open after its strike. Players do most of their damage here, so a longer recovery speeds fights up.",
    "player.player_max_health": "Player health. Higher means players survive more hits.",
    "player.damage_per_hit": "Damage of each player attack. Higher means shorter fights.",
    "player.heal_amount": "Health restored by each heal.",
    "player.max_heals": "Number of heals available per attempt.",
}

def build_prompt(report: dict, allowed: set[str], history: list[dict] | None = None) -> str:
    instructions = (
        "You are a game design assistant tuning a souls-like boss fight. "
        "Players should not beat the boss in their first few attempts, and should "
        "usually win for the first time somewhere in a target attempt window. "
        "Players get better with every attempt because they learn the boss, and each "
        "player learns at their own speed. That learning is read-only and cannot be changed. "
        "Below is a report from simulated playtests: current settings, design targets, "
        "overall time to kill, and for each player type the median attempt of the first win, "
        "the share of players who won before attempt 5, and the share who never won in 40 attempts. "
        "Making the fight harder moves first wins later, and making it easier moves them earlier. "
        "Shared settings affect both player types, so look at both. "
        "Time to kill must also stay inside its target. "
        "The report also gives the number of enemy strikes needed to kill a player and the "
        "number of player hits needed to kill the enemy. Both have target ranges, which "
        "limit how far enemy.damage, enemy.health, player.player_max_health and "
        "player.damage_per_hit can move. When those are fixed by their targets, use the "
        "other settings (wind-up, recovery, heals) to reach the first-win targets. "
        "Suggest between 1 and 4 changes that move the results toward the targets, "
        "preferring small steps. "
        "Only change the parameters listed under Allowed parameters. "
        "Everything under read_only is context and cannot be changed. "
        "Give each suggestion a short reason that cites numbers from the report. "
        "Reply with only a JSON list and no other text. Each item must look like: "
        '{"parameter": "enemy.health", "new_value": 350, "reason": "..."}'
    )
    prompt = (
        instructions
        + "\n\nAllowed parameters: "
        + ", ".join(sorted(allowed))
        + "\n\nWhat the parameters do:\n"
        + json.dumps(PARAMETER_NOTES, indent=2)
        + "\n\nReport:\n"
        + json.dumps(report, indent=2)
    )
    if history:
        prompt += (
            "\n\nPrevious rounds. These are changes already applied and the overall "
            "results they produced. The report above already includes them. "
            "Do not simply undo a change without a reason, and prefer small adjustments:\n"
            + json.dumps(history, indent=2)
        )
    return prompt

def ask_for_suggestions(prompt: str) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == "text")

def parse_suggestions(text: str, allowed: set[str]) -> list[dict]:
    try:
        suggestions = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"reply is not valid JSON: {error}")
    if not isinstance(suggestions, list):
        raise ValueError("reply must be a JSON list")
    problems = []
    for index, suggestion in enumerate(suggestions):
        if not isinstance(suggestion, dict):
            problems.append(f"item {index}: not an object")
            continue
        for problem in validate_suggestion(suggestion, allowed):
            problems.append(f"item {index}: {problem}")
    if problems:
        raise ValueError("; ".join(problems))
    return suggestions

def suggest_changes(report: dict, history: list[dict] | None = None) -> list[dict]:
    allowed = allowed_parameters(report)
    prompt = build_prompt(report, allowed, history)
    reply = ask_for_suggestions(prompt)
    return parse_suggestions(reply, allowed)

def apply_suggestions(enemy: dict, player: dict, suggestions: list[dict]) -> tuple[dict, dict]:
    new_enemy = copy.deepcopy(enemy)
    new_player = copy.deepcopy(player)
    groups = {"enemy": new_enemy, "player": new_player}
    for suggestion in suggestions:
        group, name = suggestion["parameter"].split(".", 1)
        groups[group][name] = suggestion["new_value"]
    return new_enemy, new_player