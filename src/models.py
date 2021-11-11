from typing import List, Dict, Any, Optional

from pydantic import BaseModel


class SolverStatus(BaseModel):
    active: int
    failed: int
    succeeded: int


class Solver(BaseModel):
    image: str
    status: SolverStatus


class ComputationRequest(BaseModel):
    solver_images: List[str]


class ComputationStatus(BaseModel):
    computation_id: str
    solvers: List[Solver]


class ComputationResult(BaseModel):
    output: Optional[str]
