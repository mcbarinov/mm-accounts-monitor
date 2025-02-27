def multilines(value: str) -> list[str]:
    return [u.strip() for u in value.splitlines() if u.strip()]
