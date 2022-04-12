from re import L
from common.results_utility import append_result_output
from msrestazure import azure_cloud
import pytest
import os
import pickle
from common.arm_rest_utility import fetch_aad_token_credentials
from common.kubernetes_configuration_utility import (
    delete_kubernetes_configuration,
    get_flux_configuration_client,
)

import constants as constants

from filelock import FileLock
from pathlib import Path
from kubernetes import client, config
from common.kubernetes_pod_utility import get_pod_list, get_pod_logs
from common.kubernetes_namespace_utility import list_namespace, delete_namespace

pytestmark = pytest.mark.microsoftfluxtest

# Fixture to collect all the environment variables, install the helm charts and check the status of azure arc pods. It will be run before the tests.
@pytest.fixture(scope="session", autouse=True)
def env_dict():
    results_dir = (
        os.getenv("RESULTS_DIR") if os.getenv("RESULTS_DIR") else "/tmp/results"
    )
    pod_log_dir = os.path.join(results_dir, "pods")
    conf_fixture_log = os.path.join(results_dir, "conf_fixture.log")

    my_file = Path("env.pkl")  # File to store the environment variables.
    with FileLock(
        str(my_file) + ".lock"
    ):  # Locking the file since each test will be run in parallel as separate subprocesses and may try to access the file simultaneously.
        env_dict = {}
        if not my_file.is_file():
            results_dir = os.getenv("RESULTS_DIR")
            if not results_dir:
                results_dir = "/tmp/results"
            ca_cert_file = os.getenv("CA_CERT_FILE")
            if not ca_cert_file:
                ca_cert_file = "/test/file/https-ca.cer"
            env_dict["RESULTS_DIR"] = results_dir
            env_dict["CA_CERT_FILE"] = ca_cert_file
            env_dict["CUSTOM_KUBECONFIG"] = os.getenv("CUSTOM_KUBECONFIG")
            env_dict["NUM_TESTS_COMPLETED"] = 0

            # Collecting environment variables
            env_dict["TENANT_ID"] = os.getenv("TENANT_ID")
            env_dict["SUBSCRIPTION_ID"] = os.getenv("SUBSCRIPTION_ID")
            env_dict["RESOURCE_GROUP"] = os.getenv("RESOURCE_GROUP")
            env_dict["CLUSTER_NAME"] = os.getenv("CLUSTER_NAME")
            env_dict["CLIENT_ID"] = os.getenv("CLIENT_ID")
            env_dict["CLIENT_SECRET"] = os.getenv("CLIENT_SECRET")

            env_dict["AZURE_RM_ENDPOINT"] = (
                os.getenv("AZURE_RM_ENDPOINT")
                if os.getenv("AZURE_RM_ENDPOINT")
                else constants.DEFAULT_AZURE_RMENDPOINT
            )

            env_dict["TIMEOUT"] = (
                int(os.getenv("TIMEOUT")) if os.getenv("TIMEOUT") else constants.TIMEOUT
            )

            with Path.open(my_file, "wb") as f:
                pickle.dump(env_dict, f, pickle.HIGHEST_PROTOCOL)
        else:
            with Path.open(my_file, "rb") as f:
                env_dict = pickle.load(f)

    yield env_dict

    my_file = Path("env.pkl")
    with FileLock(str(my_file) + ".lock"):
        with Path.open(my_file, "rb") as f:
            env_dict = pickle.load(f)

        env_dict["NUM_TESTS_COMPLETED"] = 1 + env_dict.get("NUM_TESTS_COMPLETED")
        if env_dict["NUM_TESTS_COMPLETED"] == int(os.getenv("NUM_TESTS")):
            # Checking if cleanup is required.
            if os.getenv("SKIP_CLEANUP"):
                return
            print("Starting cleanup...")
            append_result_output("Starting cleanup...\n", conf_fixture_log)

            load_kube_config()
            api_instance = client.CoreV1Api()

            # Before we cleanup everything, let's get a log dump from the pods
            log_dump_extension(pod_log_dir, api_instance)

            # Cleaning up resources created by default configurations
            append_result_output(
                "Cleaning up the namespaces created by the tests\n", conf_fixture_log
            )
            cleanup_namespace_list = constants.CLEANUP_NAMESPACE_LIST
            namespace_list = list_namespace(api_instance)
            for ns in namespace_list.items:
                namespace_name = ns.metadata.name
                if namespace_name in cleanup_namespace_list:
                    delete_namespace(api_instance, namespace_name)

            append_result_output(
                "Cleaning up the services created by the tests\n", conf_fixture_log
            )
            for (
                cleanup_service_ns,
                cleanup_service_name,
            ) in constants.CLEANUP_SERVICE_LIST:
                try:
                    api_instance.delete_namespaced_service(
                        cleanup_service_name, cleanup_service_ns
                    )
                except Exception:
                    pass

            append_result_output(
                "Cleaning up the deployments created by the tests\n", conf_fixture_log
            )
            api_instance = client.AppsV1Api()
            for (
                cleanup_deployment_ns,
                cleanup_deployment_name,
            ) in constants.CLEANUP_DEPLOYMENT_LIST:
                try:
                    api_instance.delete_namespaced_deployment(
                        cleanup_deployment_name, cleanup_deployment_ns
                    )
                except Exception:
                    pass

            try:
                force_delete_configurations(
                    env_dict["AZURE_RM_ENDPOINT"],
                    env_dict["SUBSCRIPTION_ID"],
                    env_dict["TENANT_ID"],
                    env_dict["CLIENT_ID"],
                    env_dict["CLIENT_SECRET"],
                    env_dict["RESOURCE_GROUP"],
                    env_dict["CLUSTER_NAME"],
                    [constants.DEFAULT_TEST_NAME, constants.CA_CERT_TEST_NAME],
                    conf_fixture_log,
                )
            except Exception as e:
                # We do our best to try to delete the configurations
                pass
            return

        with Path.open(my_file, "wb") as f:
            pickle.dump(env_dict, f, pickle.HIGHEST_PROTOCOL)


def load_kube_config():
    # Loading the cluster kubeconfig
    try:
        custom_kubeconfig = os.getenv("CUSTOM_KUBECONFIG")
        if custom_kubeconfig:
            config.load_kube_config(config_file=custom_kubeconfig)
        else:
            config.load_incluster_config()
    except Exception as e:
        pytest.fail("Error loading the in-cluster config: \n" + str(e))


# Get a log dump from the extension before cleaning up everything
def log_dump_extension(pod_log_dir, api_instance):
    # Collecting all arc-agent pod logs
    print("Collecting flux-system extension pod logs.")
    pod_list = get_pod_list(api_instance, constants.FLUX_SYSTEM_NAMESPACE)
    for pod in pod_list.items:
      pod_name = pod.metadata.name
      for container in pod.spec.containers:
        container_name = container.name
        log_file = os.path.join(pod_log_dir, pod_name, "{}.log".format(container_name))
        log = get_pod_logs(api_instance, constants.FLUX_SYSTEM_NAMESPACE, pod_name, container_name)
        append_result_output("Logs for the pod {} and container {}:\n".format(pod_name, container_name), log_file)
        append_result_output("{}\n".format(log), log_file)


# Force delete the flux configurations from the cluster just in case there
# was an issue with the standard deletion in the tests.
def force_delete_configurations(
    azure_rmendpoint,
    subscription_id,
    tenant_id,
    client_id,
    client_secret,
    resource_group,
    cluster_name,
    configuration_names,
    log_file,
):
    # Fetch aad token credentials from spn
    cloud = azure_cloud.get_cloud_from_metadata_endpoint(azure_rmendpoint)
    credential = fetch_aad_token_credentials(
        tenant_id, client_id, client_secret, cloud.endpoints.active_directory
    )
    kc_client = get_flux_configuration_client(
        credential,
        subscription_id,
        base_url=cloud.endpoints.resource_manager,
        credential_scopes=[cloud.endpoints.resource_manager + "/.default"],
        api_version=constants.FLUX_API_VERSION,
    )

    for configuration_name in configuration_names:
        try:
            delete_kubernetes_configuration(
                kc_client,
                resource_group,
                constants.CLUSTER_RP,
                constants.CLUSTER_TYPE,
                cluster_name,
                configuration_name,
                force_delete=True,
            ).result()
        except Exception as e:
            append_result_output(
                "Error while deleting the configuration: \n" + str(e), log_file
            )
