from enum import StrEnum


class BookStatus(StrEnum):
    TO_READ = "to_read"
    READING = "reading"
    READ = "read"


STATUS_LABELS: dict[BookStatus, str] = {
    BookStatus.TO_READ: "do przeczytania",
    BookStatus.READING: "czytam",
    BookStatus.READ: "przeczytana",
}

RATEABLE_STATUSES = frozenset({BookStatus.READING, BookStatus.READ})


def status_label(status: BookStatus | str) -> str:
    return STATUS_LABELS[BookStatus(status)]
