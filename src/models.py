from typing import List, Dict, Any, Optional

from pydantic import BaseModel


class SolverStatus(BaseModel):
    active: int
    failed: int
    succeeded: int


class Solver(BaseModel):
    image: str
    cpu_request: str
    mem_request: str
    status: Optional[SolverStatus]


class ComputationRequest(BaseModel):
    model_url: str
    data_url: str
    solvers: List[Solver]


class ComputationStatus(BaseModel):
    computation_id: str
    solvers: List[Solver]


class ComputationResult(BaseModel):
    output: Optional[str]
