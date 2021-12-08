import os
import logging

from kubernetes import client, config, watch


namespace = "default"

logging.basicConfig(level=logging.INFO)


def notify_dispatcher():
    logging.info("Detected solver finish")


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
        notify_dispatcher()
        exit()

    w = watch.Watch()

    for event in w.stream(core_api.list_namespaced_pod, field_selector=field_selector, namespace=namespace, _continue=response.metadata._continue):
        pod = event["object"]
        if solver_terminated(pod):
            notify_dispatcher()
            w.stop()
            exit()


if __name__ == "__main__":
    main()
