def normalize_text(value: str) -> str:
    """Key used for duplicate detection and case-insensitive search (rule R1)."""
    return " ".join(value.split()).casefold()
