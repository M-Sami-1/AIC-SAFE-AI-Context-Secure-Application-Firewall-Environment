from __future__ import annotations

import csv
import io

from .database_tool import read_business_data


def export_data(sanitized: bool = True) -> str:
    rows = read_business_data(sanitized=sanitized)
    output = io.StringIO()
    if sanitized:
        writer = csv.DictWriter(output, fieldnames=["id", "name", "department"])
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
    return str(rows)
