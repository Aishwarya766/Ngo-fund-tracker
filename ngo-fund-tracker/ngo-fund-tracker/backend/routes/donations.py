from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import crud
from ..schemas import DonationCreate, DonationOut

router = APIRouter(tags=["donations"])


@router.post("/donation", response_model=DonationOut)
def add_donation(payload: DonationCreate) -> DonationOut:
    try:
        donation = crud.create_donation(
            donor_id=payload.donor_id,
            amount=payload.amount,
            donation_type=payload.type,
            notes=payload.notes,
            date=payload.date,
        )
        return DonationOut(**donation)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/donations", response_model=list[DonationOut])
def list_donations() -> list[DonationOut]:
    return [DonationOut(**d) for d in crud.list_donations()]

