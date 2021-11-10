from typing import List, Dict, Any
import logging

from fastapi import FastAPI

from job import Job


logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.get("/")
def read_root() -> Dict[str, Any]:
    jobs = Job.get_jobs()
    return {"jobs": [job.name for job in jobs]}


@app.get("/start")
def schedule_job() -> Dict[str, Any]:
    job = Job.from_defaults("minizinc/mznc2020", ["minizinc", "test.mzn", "2.dzn"])
    status = job.run_job()
    return {"name": job.name, "status": status}


@app.get("/status/{name}")
def get_job_status(name: str) -> Dict[str, Any]:
    jobs = Job.get_jobs()
    return {"status": job.get_job_status() for job in jobs if job.name == name}


@app.get("/delete/{name}")
def delete_job(name: str) -> Dict[str, Any]:
    jobs = Job.get_jobs()
    for job in jobs:
        if job.name == name:
            return {"status": job.delete_job()}

    return {"not": "found"}
