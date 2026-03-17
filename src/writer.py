import csv


class TableWriter:
    """CSV writer that buffers rows and writes on close with the full column schema."""

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._rows: list[dict] = []
        self._columns: list[str] = []
        self._column_set: set[str] = set()

    def writerow(self, row: dict) -> None:
        if not row:
            return
        for key in row:
            if key not in self._column_set:
                self._columns.append(key)
                self._column_set.add(key)
        self._rows.append(row)

    def writerows(self, rows: list[dict]) -> None:
        for row in rows:
            self.writerow(row)

    def close(self) -> None:
        if not self._rows:
            return
        with open(self._file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._columns, restval="")
            writer.writeheader()
            writer.writerows(self._rows)
        self._rows.clear()

    @property
    def has_data(self) -> bool:
        return len(self._rows) > 0

    @property
    def row_count(self) -> int:
        return len(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
