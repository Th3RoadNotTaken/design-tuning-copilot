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