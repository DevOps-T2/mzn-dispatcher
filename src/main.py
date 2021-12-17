from typing import List, Dict, Any
import logging
from uuid import uuid4

from fastapi import FastAPI
from kubernetes_asyncio import client, config

from .dispatcher import Dispatcher
from .job import Job
from .models import ComputationRequest, ComputationStatus, ComputationResult, Solver, SolverStatus


logging.basicConfig(level=logging.INFO)

app = FastAPI()

dispatcher: Dispatcher


@app.on_event("startup")
def init() -> None:
    global dispatcher

    logging.info("Initializing k8-API...")
    config.load_incluster_config()

    dispatcher = Dispatcher(client.BatchV1Api())


@app.get("/")
async def read_root() -> Dict[str, Any]:
    jobs = await dispatcher.get_jobs()
    return {"jobs": [job.name for job in jobs]}


@app.post("/run", response_model=ComputationStatus)
async def run(request: ComputationRequest) -> ComputationStatus:
    computation_id = str(uuid4())

    solvers: List[Solver] = []
    for solver in request.solvers:
        job = await dispatcher.start_job(solver.image,
                                         model_url=request.model_url,
                                         cpu_request=solver.cpu_request,
                                         mem_request=solver.mem_request,
                                         data_url=request.data_url,
                                         labels={"computation_id": computation_id})

        solvers.append(job.get_solver_representation())

    return ComputationStatus(computation_id=computation_id, solvers=solvers)


@app.get("/status/{computation_id}", response_model=ComputationStatus)
async def get_status(computation_id: str) -> ComputationStatus:
    jobs = await dispatcher.get_jobs(labels={"computation_id": computation_id})
    solvers = [j.get_solver_representation() for j in jobs]
    return ComputationStatus(computation_id=computation_id, solvers=solvers)


@app.get("/result/{computation_id}", response_model=ComputationResult)
async def harvest_result(computation_id: str) -> ComputationResult:
    jobs = await dispatcher.get_jobs(labels={"computation_id": computation_id})
    succeeded = [job for job in jobs if job.succeeded]

    if not succeeded:
        result = ComputationResult()
    else:
        result = ComputationResult(output=succeeded[0].get_output())

    for job in jobs:
        await job.delete()

    return result


@app.get("/delete/{name}")
async def delete_job(name: str) -> Dict[str, Any]:
    jobs = Job.get_jobs()
    for job in jobs:
        if job.name == name:
            return {"status": await job.delete_job()}

    return {"not": "found"}
