from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import crud
from ..schemas import DonorCreate, DonorOut

router = APIRouter(tags=["donors"])


@router.post("/donor", response_model=DonorOut)
def add_donor(payload: DonorCreate) -> DonorOut:
    try:
        donor = crud.create_donor(name=payload.name, email=payload.email, phone=payload.phone)
        return DonorOut(**donor)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/donors", response_model=list[DonorOut])
def list_donors() -> list[DonorOut]:
    return [DonorOut(**d) for d in crud.list_donors()]
