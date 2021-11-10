from __future__ import annotations  # https://stackoverflow.com/questions/41135033/type-hinting-within-a-class

import logging
from typing import List, Dict, Any
from os import environ
from uuid import uuid4

from kubernetes import client, config
from kubernetes.client.api import BatchV1Api


config.load_incluster_config()
job_prefix = environ["JOB_PREFIX"]

batch_api = client.BatchV1Api()


class Job(object):

    """
    A wrapper around the API-servers' job object
    """

    _job: client.V1Job

    def __init__(self, job: client.V1Job) -> None:
        self._job = job

    @property
    def name(self) -> str:
        return self._job.metadata.name

    @staticmethod
    def from_defaults(image: str, command: List[str] = None) -> Job:
        name = job_prefix + "-" + str(uuid4())
        # Configureate Pod template container
        container = client.V1Container(
            name=name,
            image=image,
            command=command)
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": name}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container]))
        # Create the specification of deployment
        spec = client.V1JobSpec(
            template=template,
            backoff_limit=4)
        # Instantiate the job object
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=name, labels={"app": job_prefix}),
            spec=spec)
        return Job(job)

    @staticmethod
    def get_jobs() -> List[Job]:
        v1jobs = batch_api.list_namespaced_job(namespace="default", label_selector="app={}".format(job_prefix))
        return [Job(j) for j in v1jobs.items]

    def run_job(self) -> Dict[Any, Any]:
        api_response = batch_api.create_namespaced_job(
            body=self._job,
            namespace="default")
        logging.info("Job created. status='%s'" % str(api_response.status))
        return self.get_job_status()

    def get_job_status(self) -> Dict[Any, Any]:
        api_response = batch_api.read_namespaced_job_status(
            name=self.name,
            namespace="default")

        return api_response.status.to_dict()

    def delete_job(self) -> str:
        api_response = batch_api.delete_namespaced_job(
            name=self.name,
            namespace="default",
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))
        return api_response.status
