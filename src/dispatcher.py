from os import environ
from uuid import uuid4
from typing import Dict, List

from kubernetes import client

from .job import Job


class Dispatcher:
    batch_api: client.BatchV1Api

    def __init__(self, batch_api: client.BatchV1Api):
        self.batch_api = batch_api
        self.job_prefix = environ["JOB_PREFIX"]

    def start_job(self, image: str, model_url: str, data_url: str, labels: Dict[str, str] = {}) -> Job:
        labels["app"] = self.job_prefix
        name = self.job_prefix + "-" + str(uuid4())

        # Configure Pod template
        volume = client.V1Volume(
                name="src-dir",
                empty_dir=client.V1EmptyDirVolumeSource()
                )

        command = ["minizinc", "/src/model.mzn", "/src/data.dzn"]
        container = client.V1Container(
                name=name,
                image=image,
                command=command,
                volume_mounts=[client.V1VolumeMount(name="src-dir",
                                                    mount_path="/src")])

        wget = "wget -O /src/model.mzn {model_url} && wget -O /src/data.dzn {data_url}".format(model_url=model_url,
                                                                                               data_url=data_url)
        initContainer = client.V1Container(
                name="init-"+name,
                image="busybox",
                command=["sh", "-c", wget],
                volume_mounts=[client.V1VolumeMount(name="src-dir",
                                                    mount_path="/src")])

        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": name}),
            spec=client.V1PodSpec(restart_policy="Never",
                                  containers=[container],
                                  init_containers=[initContainer],
                                  volumes=[volume]))

        # Create the specification of deployment
        spec = client.V1JobSpec(
            template=template,
            backoff_limit=4)

        # Instantiate the job object
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=name, labels=labels),
            spec=spec)

        started_job = self.batch_api.create_namespaced_job(
            body=job,
            namespace="default")
        return Job(started_job, self.batch_api)

    def get_jobs(self, labels: Dict[str, str] = {}) -> List[Job]:
        labels["app"] = self.job_prefix
        label_selector = Dispatcher._labels_to_string(labels)

        v1jobs = self.batch_api.list_namespaced_job(namespace="default", label_selector=label_selector)
        return [Job(j, self.batch_api) for j in v1jobs.items]

    @staticmethod
    def _labels_to_string(labels: Dict[str, str]) -> str:
        return ",".join([label+"="+value for label, value in labels.items()])
