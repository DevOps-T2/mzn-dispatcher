from __future__ import annotations  # https://stackoverflow.com/questions/41135033/type-hinting-within-a-class

import logging

from kubernetes import client

from .models import Solver, SolverStatus


class Job(object):

    """
    A wrapper around the API-servers' job object
    """

    _job: client.V1Job
    _batch_api: client.BatchV1Api

    def __init__(self, job: client.V1Job, batch_api: client.BatchV1Api) -> None:
        self._job: client.V1Job = job
        self._batch_api: client.BatchV1Api = batch_api

    @property
    def name(self) -> str:
        return self._job.metadata.name

    @property
    def image(self) -> str:
        return self._job.spec.template.spec.containers[0].image

    @property
    def active(self) -> int:
        return self._job.status.to_dict().get('active', 0) or 0

    @property
    def succeeded(self) -> int:
        return self._job.status.to_dict().get('succeeded', 0) or 0

    @property
    def failed(self) -> int:
        return self._job.status.to_dict().get('failed', 0) or 0

    def get_solver_representation(self) -> Solver:
        solver_status = SolverStatus(active=self.active,
                                     succeeded=self.succeeded,
                                     failed=self.failed)
        return Solver(image=self.image, status=solver_status)

    def update_status(self) -> None:
        api_response = self._batch_api.read_namespaced_job_status(
            name=self.name,
            namespace="default")

        logging.debug(api_response.status.to_dict())

        self._job = api_response

    def get_output(self) -> str:
        return "placeholder"

    def delete(self) -> str:
        api_response = self._batch_api.delete_namespaced_job(
            name=self.name,
            namespace="default",
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))
        return api_response.status
