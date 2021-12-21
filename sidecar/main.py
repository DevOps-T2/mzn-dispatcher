import os
import logging

import requests
from pydantic import BaseModel
from kubernetes import client, config, watch


namespace = "default"
solution_file = "/src/solution.txt"

solution_service = "solution-serice"

computation_id = os.environ["COMPUTATION_ID"]
user_id = os.environ["USER_ID"]

logging.basicConfig(level=logging.INFO)


class SolutionRequest(BaseModel):
    user_id: str
    computation_id: str
    body: str


def save_solution():
    logging.info("Detected solver finish")
    if os.path.exists(solution_file):
        with open(solution_file, "r") as fd:
            data = SolutionRequest(user_id=user_id, computation_id=computation_id, body=fd.read()).dict()

        headers = {'UserId': 'system', 'Role': 'admin'}
        response = requests.post('http://'+solution_service+'/api/solutions/upload', json=data, headers=headers)
        if response.status_code != 200:
            logging.error("solution-service replied {}".format(response.text) +
                          "On request {}".format(data))


def solver_terminated(pod: client.V1Pod):
    return pod.status.container_statuses[0].state.terminated


def main():
    config.load_incluster_config()
    core_api = client.CoreV1Api()

    pod_name = os.environ["HOSTNAME"]
    field_selector = "metadata.name={}".format(pod_name)
    response = core_api.list_namespaced_pod(namespace, field_selector=field_selector)
    pod = response.items[0]

    if solver_terminated(pod):
        save_solution()
        exit()

    w = watch.Watch()

    for event in w.stream(core_api.list_namespaced_pod, field_selector=field_selector, namespace=namespace, _continue=response.metadata._continue):
        pod = event["object"]
        if solver_terminated(pod):
            save_solution()
            w.stop()
            exit()


if __name__ == "__main__":
    main()
