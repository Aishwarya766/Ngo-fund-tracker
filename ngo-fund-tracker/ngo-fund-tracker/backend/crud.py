from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Optional

from .database import get_conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def create_donor(*, name: str, email: Optional[str], phone: Optional[str]) -> dict[str, Any]:
    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO donors(name, email, phone) VALUES(?,?,?)",
                (name.strip(), email, phone),
            )
            donor_id = int(cur.lastrowid)
        except sqlite3.IntegrityError:
         cur = conn.execute(
        "INSERT INTO donors(name, email, phone) VALUES(?,?,?)",
        (name.strip(), None, phone),
    )
        donor_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM donors WHERE id = ?", (donor_id,)).fetchone()
        if not row:
            raise RuntimeError("Failed to create donor")
        out = _row_to_dict(row)
        out["total_donations"] = float(
            conn.execute("SELECT COALESCE(SUM(amount),0) AS s FROM donations WHERE donor_id = ?", (donor_id,)).fetchone()[
                "s"
            ]
        )
        return out


def list_donors() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT d.*,
                   COALESCE(SUM(do.amount),0) AS total_donations
            FROM donors d
            LEFT JOIN donations do ON do.donor_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC, d.id DESC
            """
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def create_donation(
    *, donor_id: int, amount: float, donation_type: str, notes: Optional[str], date: Optional[datetime]
) -> dict[str, Any]:
    with get_conn() as conn:
        donor = conn.execute("SELECT id, name FROM donors WHERE id = ?", (donor_id,)).fetchone()
        if not donor:
            raise ValueError("donor_id not found")
        if date is None:
            cur = conn.execute(
                "INSERT INTO donations(donor_id, amount, donation_type, notes) VALUES(?,?,?,?)",
                (donor_id, amount, donation_type, notes),
            )
        else:
            cur = conn.execute(
                "INSERT INTO donations(donor_id, amount, donation_type, date, notes) VALUES(?,?,?,?,?)",
                (donor_id, amount, donation_type, date.isoformat(sep=" "), notes),
            )
        donation_id = int(cur.lastrowid)
        row = conn.execute(
            """
            SELECT do.id,
                   do.donor_id,
                   d.name AS donor_name,
                   do.amount,
                   do.donation_type,
                   do.date,
                   do.notes
            FROM donations do
            JOIN donors d ON d.id = do.donor_id
            WHERE do.id = ?
            """,
            (donation_id,),
        ).fetchone()
        if not row:
            raise RuntimeError("Failed to create donation")
        return _row_to_dict(row)


def list_donations() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT do.id,
                   do.donor_id,
                   d.name AS donor_name,
                   do.amount,
                   do.donation_type,
                   do.date,
                   do.notes
            FROM donations do
            JOIN donors d ON d.id = do.donor_id
            ORDER BY do.date DESC, do.id DESC
            """
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def create_project(*, name: str, description: Optional[str], allocated_budget: float) -> dict[str, Any]:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO projects(name, description, allocated_budget) VALUES(?,?,?)",
            (name.strip(), description, allocated_budget),
        )
        project_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise RuntimeError("Failed to create project")
        return _row_to_dict(row)


def list_projects() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.*,
                   COALESCE(SUM(e.amount),0) AS total_spent,
                   (p.allocated_budget - COALESCE(SUM(e.amount),0)) AS remaining_budget
            FROM projects p
            LEFT JOIN expenses e ON e.project_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC, p.id DESC
            """
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def create_expense(*, project_id: int, amount: float, description: str, date: Optional[datetime]) -> dict[str, Any]:
    with get_conn() as conn:
        project = conn.execute("SELECT id, name FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project:
            raise ValueError("project_id not found")
        if date is None:
            cur = conn.execute(
                "INSERT INTO expenses(project_id, amount, description) VALUES(?,?,?)",
                (project_id, amount, description),
            )
        else:
            cur = conn.execute(
                "INSERT INTO expenses(project_id, amount, description, date) VALUES(?,?,?,?)",
                (project_id, amount, description, date.isoformat(sep=" ")),
            )
        expense_id = int(cur.lastrowid)
        row = conn.execute(
            """
            SELECT e.id,
                   e.project_id,
                   p.name AS project_name,
                   e.amount,
                   e.description,
                   e.date
            FROM expenses e
            JOIN projects p ON p.id = e.project_id
            WHERE e.id = ?
            """,
            (expense_id,),
        ).fetchone()
        if not row:
            raise RuntimeError("Failed to create expense")
        return _row_to_dict(row)


def list_expenses() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT e.id,
                   e.project_id,
                   p.name AS project_name,
                   e.amount,
                   e.description,
                   e.date
            FROM expenses e
            JOIN projects p ON p.id = e.project_id
            ORDER BY e.date DESC, e.id DESC
            """
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def get_dashboard() -> dict[str, Any]:
    with get_conn() as conn:
        total_donations = float(conn.execute("SELECT COALESCE(SUM(amount),0) AS s FROM donations").fetchone()["s"])
        total_expenses = float(conn.execute("SELECT COALESCE(SUM(amount),0) AS s FROM expenses").fetchone()["s"])
        total_donors = int(conn.execute("SELECT COUNT(*) AS c FROM donors").fetchone()["c"])
        return {
            "total_donations": total_donations,
            "total_expenses": total_expenses,
            "remaining_balance": total_donations - total_expenses,
            "total_donors": total_donors,
        }

