import pytest

from kubernetes import watch


# Returns a kubernetes pod object in given namespace. Object description at: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodList.md
def get_pod(api_instance, namespace, pod_name):
    try:
        return api_instance.read_namespaced_pod(pod_name, namespace)
    except Exception as e:
        pytest.fail("Error occured when retrieving pod information: " + str(e))


# Returns a list of kubernetes pod objects in a given namespace. Object description at: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodList.md
def get_pod_list(api_instance, namespace, label_selector=""):
    try:
        return api_instance.list_namespaced_pod(namespace, label_selector=label_selector)
    except Exception as e:
        pytest.fail("Error occurred when retrieving pod information: " + str(e))


# Function that watches events corresponding to pods in the given namespace and passes the events to a callback function
def watch_pod_status(api_instance, namespace=None, timeout=300, callback=None):
    if not callback:
        return
    try:
        w = watch.Watch()
        if not namespace:
            for event in w.stream(api_instance.list_pod_for_all_namespaces, timeout_seconds=timeout):
                if callback(event):
                    return
        else:
            for event in w.stream(api_instance.list_namespaced_pod, namespace, timeout_seconds=timeout):
                if callback(event):
                    return
    except Exception as e:
        pytest.fail("Error occurred when checking pod status: " + str(e))
    pytest.fail("The watch on the pods has timed out. Please see the pod logs for more info.")


# Function that returns the pod logs of a given container.
def get_pod_logs_since_seconds(api_instance, pod_namespace, pod_name, container_name, since_seconds):
    try:
        return api_instance.read_namespaced_pod_log(pod_name, pod_namespace, container=container_name, since_seconds=since_seconds)
    except Exception as e:
        pytest.fail("Error occurred when fetching pod logs: " + str(e))


def get_pod_logs(api_instance, pod_namespace, pod_name, container_name):
    try:
        return api_instance.read_namespaced_pod_log(pod_name, pod_namespace, container=container_name)
    except Exception as e:
        pytest.fail("Error occurred when fetching pod logs: " + str(e))
