from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import crud
from ..schemas import ExpenseCreate, ExpenseOut

router = APIRouter(tags=["expenses"])


@router.post("/expense", response_model=ExpenseOut)
def add_expense(payload: ExpenseCreate) -> ExpenseOut:
    try:
        expense = crud.create_expense(
            project_id=payload.project_id,
            amount=payload.amount,
            description=payload.description,
            date=payload.date,
        )
        return ExpenseOut(**expense)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/expenses", response_model=list[ExpenseOut])
def list_expenses() -> list[ExpenseOut]:
    return [ExpenseOut(**e) for e in crud.list_expenses()]

