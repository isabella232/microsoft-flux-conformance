import pytest
import os
from common.kubernetes_configuration_utility import create_flux_configuration, get_flux_configuration_client
import common.constants as constants

from kubernetes import config
from msrestazure import azure_cloud

from common.arm_rest_utility import fetch_aad_token_credentials
from common.results_utility import append_result_output
from helper import check_kubernetes_pods_status, check_kubernetes_configuration_state, check_namespace_status

pytestmark = pytest.mark.microsoftfluxtest


# validate all the critical resources such as ds, rs, ds pods and rs pod etc. are up and running
def test_create_flux_config_default(env_dict):
    tenant_id = env_dict.get('TENANT_ID')
    if not tenant_id:
        pytest.fail('ERROR: variable TENANT_ID is required.')

    subscription_id = env_dict.get('SUBSCRIPTION_ID')
    if not subscription_id:
        pytest.fail('ERROR: variable SUBSCRIPTION_ID is required.')

    resource_group = env_dict.get('RESOURCE_GROUP')
    if not resource_group:
        pytest.fail('ERROR: variable RESOURCE_GROUP is required.')

    cluster_name = env_dict.get('CLUSTER_NAME')
    if not cluster_name:
        pytest.fail('ERROR: variable CLUSTER_NAME is required.')

    client_id = env_dict.get('CLIENT_ID')
    if not client_id:
        pytest.fail('ERROR: variable CLIENT_ID is required.')

    client_secret = env_dict.get('CLIENT_SECRET')
    if not client_secret:
        pytest.fail('ERROR: variable CLIENT_SECRET is required.')
    
    azure_rmendpoint = env_dict.get('AZURE_RM_ENDPOINT')

    cluster_rp = constants.CLUSTER_RP
    cluster_type = constants.CLUSTER_TYPE
    repository_url = "https://github.com/Azure/arc-k8s-demo"
    namespace = "default"
    branch = "main"
    paths = [""]
    configuration_name = "default"
    scope = "cluster"
    
    # Fetch aad token credentials from spn
    cloud = azure_cloud.get_cloud_from_metadata_endpoint(azure_rmendpoint)
    credential = fetch_aad_token_credentials(tenant_id, client_id, client_secret, cloud.endpoints.active_directory)
    print("Successfully fetched credentials object.")

    # flux_config_creation_args
    # stdout, stderr = subprocess.Popen(['az','k8s-configuration','flux','create','-g',resource_group,'-t',cluster_type,'-c',cluster_name,'-n',configuration_name,'-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    # if len(stderr) > 0:

    kc_client = get_flux_configuration_client(credential, subscription_id, base_url=cloud.endpoints.resource_manager, credential_scopes=[cloud.endpoints.resource_manager + "/.default"], api_version='2022-01-01-preview')
    put_kc_response = create_flux_configuration(kc_client, resource_group, cluster_rp, cluster_type, cluster_name, configuration_name, repository_url, paths, namespace, branch, scope)
    append_result_output("Create config response: {}\n".format(put_kc_response), os.path.join(env_dict['RESULTS_DIR'], 'default.log'))
    print("Successfully requested the creation of kubernetes configuration resource.")

    # Checking the compliance of kubernetes configuration resource
    timeout_seconds = env_dict.get('TIMEOUT')
    check_kubernetes_configuration_state(kc_client, resource_group, cluster_rp, cluster_type, cluster_name, configuration_name, os.path.join(env_dict['RESULTS_DIR'], 'default.log'), timeout_seconds)
    print("The kubernetes configuration resource was created successfully.")

    # Loading in-cluster kube-config
    try:
        custom_kubeconfig = env_dict['CUSTOM_KUBECONFIG']
        if custom_kubeconfig:
            config.load_kube_config(config_file=custom_kubeconfig)
        else:
            config.load_incluster_config()
    except Exception as e:
        pytest.fail("Error loading the in-cluster config: " + str(e))

    # Checking the status of namespaces created by the flux operator
    check_namespace_status(os.path.join(env_dict['RESULTS_DIR'], 'default.log'), constants.DEFAULT_CASE_NAMESPACE_RESOURCE_LIST, timeout_seconds)

    # Checking the status of pods created by the flux operator
    check_kubernetes_pods_status(constants.FLUX_OPERATOR_RESOURCE_NAMESPACE, os.path.join(env_dict['RESULTS_DIR'], 'default.log'), constants.DEFAULT_CASE_RESOURCES_POD_LABEL_LIST, timeout_seconds)
    print("Successfully checked pod status of the flux operator and resources created by it.")

    