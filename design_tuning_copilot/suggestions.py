import json
import anthropic

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

def build_prompt(report: dict, allowed: set[str]) -> str:
    instructions = (
        "You are a game design assistant helping tune a combat encounter. "
        "Below is a playtest report: current settings, design targets, overall results "
        "and results per player style. "
        "Suggest between 1 and 5 changes that move the results toward the targets. "
        "Only change the parameters listed under Allowed parameters. "
        "The player styles are read-only context and cannot be changed. "
        "Give each suggestion a short reason that cites numbers from the report. "
        "Reply with only a JSON list and no other text. Each item must look like: "
        '{"parameter": "enemy.health", "new_value": 350, "reason": "..."}'
    )
    return (
        instructions
        + "\n\nAllowed parameters: "
        + ", ".join(sorted(allowed))
        + "\n\nReport:\n"
        + json.dumps(report, indent=2)
    )

def ask_for_suggestions(prompt: str) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == "text")