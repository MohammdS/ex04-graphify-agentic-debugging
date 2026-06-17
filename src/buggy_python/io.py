"""Loan file loading and aggregate calculations."""

from __future__ import annotations

from importlib.resources import files
from json import load
from pathlib import Path
from typing import Any


def read_file(path: str | Path | None = None) -> dict[str, Any]:
    """Read loan data from a JSON file.

    When no path is provided, the bundled fixture from the extracted repository
    is used.
    """

    loan_path = Path(path) if path is not None else files(__package__) / "loans.json"
    with loan_path.open("r", encoding="utf-8") as json_file:
        return load(json_file)


def _amounts_by_status(data: dict[str, Any], status: str) -> list[float]:
    return [
        float(loan["amount"])
        for loan in data["loans"]
        if loan["status"] == status
    ]


def calculate_unpaid_loans(data: dict[str, Any]) -> int:
    return int(sum(_amounts_by_status(data, "unpaid")))


def calculate_paid_loans(data: dict[str, Any]) -> float:
    return sum(_amounts_by_status(data, "paid"))


def average_paid_loans(data: dict[str, Any]) -> float:
    paid_loans = _amounts_by_status(data, "paid")
    return sum(paid_loans) / len(paid_loans)

