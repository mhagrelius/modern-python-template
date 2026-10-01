"""A small typed example; replace it with your package's public API."""


def normalize_name(value: str) -> str:
    """Trim a name and collapse whitespace without changing its case."""
    return " ".join(value.split())
