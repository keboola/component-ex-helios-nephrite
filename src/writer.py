import csv
from typing import TextIO


class TableWriter:
    """CSV writer with lazy initialization - columns inferred from first row."""

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._file: TextIO | None = None
        self._writer: csv.DictWriter | None = None
        self._columns: list[str] | None = None
        self._row_count = 0

    def writerow(self, row: dict) -> None:
        if not row:
            return

        if self._writer is None:
            self._columns = list(row.keys())
            self._file = open(self._file_path, "w", newline="", encoding="utf-8")
            self._writer = csv.DictWriter(
                self._file,
                fieldnames=self._columns,
                extrasaction="ignore",
            )
            self._writer.writeheader()

        self._writer.writerow(row)
        self._row_count += 1

    def writerows(self, rows: list[dict]) -> None:
        for row in rows:
            self.writerow(row)

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None

    @property
    def has_data(self) -> bool:
        return self._row_count > 0

    @property
    def row_count(self) -> int:
        return self._row_count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
