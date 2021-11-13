from typing import List, Dict, Any
import logging
from uuid import uuid4

from fastapi import FastAPI

from .job import Job
from .models import ComputationRequest, ComputationStatus, ComputationResult, Solver, SolverStatus


logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.get("/")
def read_root() -> Dict[str, Any]:
    jobs = Job.get_jobs()
    return {"jobs": [job.name for job in jobs]}


@app.post("/run", response_model=ComputationStatus)
def run(request: ComputationRequest) -> ComputationStatus:
    solver_stats: List[Solver] = []

    computation_id = str(uuid4())
    for image in request.solver_images:
        job = Job.from_defaults(image, labels={"computation_id": computation_id})
        solver_stats.append(Solver(image=image, status=job.run_job()))

    return ComputationStatus(computation_id=computation_id, solvers=solver_stats)


@app.get("/status/{computation_id}", response_model=ComputationStatus)
def get_status(computation_id: str) -> ComputationStatus:
    jobs = Job.get_jobs(labels={"computation_id": computation_id})
    solvers = [Solver(image=j.image, status=j.get_status()) for j in jobs]
    return ComputationStatus(computation_id=computation_id, solvers=solvers)


@app.get("/result/{computation_id}", response_model=ComputationResult)
def harvest_result(computation_id: str) -> ComputationResult:
    jobs = Job.get_jobs(labels={"computation_id": computation_id})
    succeeded = [job for job in jobs if job.get_status().succeeded]

    if not succeeded:
        result = ComputationResult()
    else:
        result = ComputationResult(output=succeeded[0].get_output())

    for job in jobs:
        job.delete_job()

    return result


@app.get("/delete/{name}")
def delete_job(name: str) -> Dict[str, Any]:
    jobs = Job.get_jobs()
    for job in jobs:
        if job.name == name:
            return {"status": job.delete_job()}

    return {"not": "found"}
