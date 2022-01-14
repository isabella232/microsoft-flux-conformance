import pytest
import os
import base64
from common.kubernetes_configuration_utility import (
    create_flux_configuration,
    create_flux_configuration_kustomization,
    delete_kubernetes_configuration,
    get_flux_configuration_client,
)
import constants as constants

from kubernetes import config
from msrestazure import azure_cloud

from common.arm_rest_utility import fetch_aad_token_credentials
from common.results_utility import append_result_output
from helper import (
    check_kubernetes_configuration_delete_state,
    check_kubernetes_pods_status,
    check_kubernetes_configuration_state,
    check_kubernetes_secret,
    check_namespace_status,
)

pytestmark = pytest.mark.microsoftfluxtest


# validate all the critical resources such as ds, rs, ds pods and rs pod etc. are up and running
def test_create_flux_config_https_ca(env_dict):
    tenant_id = env_dict.get("TENANT_ID")
    if not tenant_id:
        pytest.fail("ERROR: variable TENANT_ID is required.")

    subscription_id = env_dict.get("SUBSCRIPTION_ID")
    if not subscription_id:
        pytest.fail("ERROR: variable SUBSCRIPTION_ID is required.")

    resource_group = env_dict.get("RESOURCE_GROUP")
    if not resource_group:
        pytest.fail("ERROR: variable RESOURCE_GROUP is required.")

    cluster_name = env_dict.get("CLUSTER_NAME")
    if not cluster_name:
        pytest.fail("ERROR: variable CLUSTER_NAME is required.")

    client_id = env_dict.get("CLIENT_ID")
    if not client_id:
        pytest.fail("ERROR: variable CLIENT_ID is required.")

    client_secret = env_dict.get("CLIENT_SECRET")
    if not client_secret:
        pytest.fail("ERROR: variable CLIENT_SECRET is required.")

    azure_rmendpoint = env_dict.get("AZURE_RM_ENDPOINT")
    log_file = "https_ca_cert.log"

    cluster_rp = constants.CLUSTER_RP
    cluster_type = constants.CLUSTER_TYPE
    repository_url = constants.CA_CERT_TEST_REPOSITORY_URL
    namespace = constants.CA_CERT_TEST_NAMESPACE
    branch = constants.CA_CERT_TEST_BRANCH
    configuration_name = constants.CA_CERT_TEST_NAME
    scope = constants.CA_CERT_TEST_SCOPE

    kustomizations = {
        "infra": create_flux_configuration_kustomization("./infrastructure", []),
        "apps": create_flux_configuration_kustomization("./apps/staging", ["infra"]),
    }

    # Base64 encode a ca cert from a file
    encoded_ca_cert = None
    with open(env_dict.get("CA_CERT_FILE"), "r") as f:
        ca_cert = f.read()
        encoded_ca_cert = base64.b64encode(ca_cert.encode("utf-8")).decode("utf-8")

    # Fetch aad token credentials from spn
    cloud = azure_cloud.get_cloud_from_metadata_endpoint(azure_rmendpoint)
    credential = fetch_aad_token_credentials(
        tenant_id, client_id, client_secret, cloud.endpoints.active_directory
    )
    print("Successfully fetched credentials object.")

    kc_client = get_flux_configuration_client(
        credential,
        subscription_id,
        base_url=cloud.endpoints.resource_manager,
        credential_scopes=[cloud.endpoints.resource_manager + "/.default"],
        api_version=constants.FLUX_API_VERSION,
    )
    put_kc_response = create_flux_configuration(
        kc_client,
        resource_group,
        cluster_rp,
        cluster_type,
        cluster_name,
        configuration_name,
        repository_url,
        kustomizations,
        namespace,
        branch,
        scope,
        encoded_ca_cert,
    )
    append_result_output(
        "Create config response: {}\n".format(put_kc_response),
        os.path.join(env_dict["RESULTS_DIR"], log_file),
    )
    print("Successfully requested the creation of kubernetes configuration resource.")

    # Checking the compliance of kubernetes configuration resource
    timeout_seconds = env_dict.get("TIMEOUT")
    check_kubernetes_configuration_state(
        kc_client,
        resource_group,
        cluster_rp,
        cluster_type,
        cluster_name,
        configuration_name,
        os.path.join(env_dict["RESULTS_DIR"], log_file),
        timeout_seconds,
    )
    print("The kubernetes configuration resource was created successfully.")

    # Loading in-cluster kube-config
    try:
        custom_kubeconfig = env_dict["CUSTOM_KUBECONFIG"]
        if custom_kubeconfig:
            config.load_kube_config(config_file=custom_kubeconfig)
        else:
            config.load_incluster_config()
    except Exception as e:
        pytest.fail("Error loading the in-cluster config: " + str(e))

    check_kubernetes_secret(
        namespace, f"{configuration_name}-auth", timeout=timeout_seconds
    )

    # Checking the status of namespaces created by the flux operator
    check_namespace_status(
        os.path.join(env_dict["RESULTS_DIR"], log_file),
        constants.CA_CERT_CASE_NAMESPACE_RESOURCE_LIST,
        timeout_seconds,
    )

    # Checking the status of pods created by the flux operator
    # for the HTTPS CA Cert case
    check_kubernetes_pods_status(
        None,
        os.path.join(env_dict["RESULTS_DIR"], log_file),
        ["nginx-ingress-controller", "redis", "podinfo"],
        timeout_seconds,
    )
    print(
        "Successfully checked pod status of the flux operator and resources created by it."
    )

    # Cleanup the flux configuration from the cluster
    delete_kc_response = delete_kubernetes_configuration(
        kc_client,
        resource_group,
        cluster_rp,
        cluster_type,
        cluster_name,
        configuration_name,
    )
    append_result_output(
        "Delete config response: {}\n".format(delete_kc_response),
        os.path.join(env_dict["RESULTS_DIR"], log_file),
    )

    # Check that the flux configuration was actually removed from the cluster
    check_kubernetes_configuration_delete_state(
        kc_client,
        resource_group,
        cluster_rp,
        cluster_type,
        cluster_name,
        configuration_name,
        os.path.join(env_dict["RESULTS_DIR"], log_file),
        timeout_seconds,
    )
