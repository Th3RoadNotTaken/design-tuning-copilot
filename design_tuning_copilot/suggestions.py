def allowed_parameters(report: dict) -> set[str]:
    allowed = set()
    for group, values in report["tunable"].items():
        for name, value in values.items():
            if isinstance(value, (int, float)):
                allowed.add(f"{group}.{name}")
    return allowed