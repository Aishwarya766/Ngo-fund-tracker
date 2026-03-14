from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import crud
from ..schemas import ProjectCreate, ProjectOut

router = APIRouter(tags=["projects"])


@router.post("/project", response_model=ProjectOut)
def add_project(payload: ProjectCreate) -> ProjectOut:
    try:
        project = crud.create_project(name=payload.name, description=payload.description, allocated_budget=payload.allocated_budget)
        project["total_spent"] = 0.0
        project["remaining_budget"] = float(project["allocated_budget"])
        return ProjectOut(**project)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects", response_model=list[ProjectOut])
def list_projects() -> list[ProjectOut]:
    return [ProjectOut(**p) for p in crud.list_projects()]

