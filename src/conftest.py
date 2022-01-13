import pytest
import os
import pickle

import common.constants as constants

from filelock import FileLock
from pathlib import Path
from kubernetes import client, config
from common.kubernetes_namespace_utility import list_namespace, delete_namespace
from common.kubernetes_deployment_utility import list_deployment, delete_deployment
from common.kubernetes_service_utility import list_service, delete_service

pytestmark = pytest.mark.microsoftfluxtest

# Fixture to collect all the environment variables, install the helm charts and check the status of azure arc pods. It will be run before the tests.
@pytest.fixture(scope='session', autouse=True)
def env_dict():
    my_file = Path("env.pkl")  # File to store the environment variables.
    with FileLock(str(my_file) + ".lock"):  # Locking the file since each test will be run in parallel as separate subprocesses and may try to access the file simultaneously.
        env_dict = {}
        if not my_file.is_file():
            results_dir = os.getenv('RESULTS_DIR')
            if not results_dir:
                results_dir = '/tmp/results'
            env_dict['RESULTS_DIR'] = results_dir
            env_dict['CUSTOM_KUBECONFIG'] = os.getenv('CUSTOM_KUBECONFIG')
            env_dict['NUM_TESTS_COMPLETED'] = 0

            # Collecting environment variables
            env_dict['TENANT_ID'] = os.getenv('TENANT_ID')
            env_dict['SUBSCRIPTION_ID'] = os.getenv('SUBSCRIPTION_ID')
            env_dict['RESOURCE_GROUP'] = os.getenv('RESOURCE_GROUP')
            env_dict['CLUSTER_NAME'] = os.getenv('CLUSTER_NAME')
            env_dict['CLIENT_ID'] = os.getenv('CLIENT_ID')
            env_dict['CLIENT_SECRET'] = os.getenv('CLIENT_SECRET')

            env_dict['AZURE_RM_ENDPOINT'] = os.getenv('AZURE_RM_ENDPOINT') if os.getenv('AZURE_RM_ENDPOINT') else constants.DEFAULT_AZURE_RMENDPOINT

            env_dict['TIMEOUT'] = int(os.getenv('TIMEOUT')) if os.getenv('TIMEOUT') else constants.TIMEOUT

            env_dict['CLUSTER_TYPE'] = os.getenv('CLUSTER_TYPE')
            env_dict['CLUSTER_RP'] = os.getenv('CLUSTER_RP')

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

        env_dict['NUM_TESTS_COMPLETED'] = 1 + env_dict.get('NUM_TESTS_COMPLETED')
        if env_dict['NUM_TESTS_COMPLETED'] == int(os.getenv('NUM_TESTS')):
            # Checking if cleanup is required.
            if os.getenv('SKIP_CLEANUP'):
                return
            print('Starting cleanup...')

            # Loading in-cluster kube config
            try:
                custom_kubeconfig = env_dict['CUSTOM_KUBECONFIG']
                if custom_kubeconfig:
                    config.load_kube_config(config_file=custom_kubeconfig)
                else:
                    config.load_incluster_config()
            except Exception as e:
                pytest.fail("Error loading the in-cluster config: " + str(e))
            api_instance = client.CoreV1Api()
            
            # Cleaning up resources created by default configurations
            print("Cleaning up the resources created by the flux operators")
            cleanup_namespace_list = constants.CLEANUP_NAMESPACE_LIST
            namespace_list = list_namespace(api_instance)
            for ns in namespace_list.items:
                namespace_name = ns.metadata.name
                if namespace_name in cleanup_namespace_list:
                    delete_namespace(api_instance, namespace_name)
            
            api_instance = client.AppsV1Api()
            cleanup_deployment_list = constants.CLEANUP_DEPLOYMENT_LIST
            deployment_list = list_deployment(api_instance, constants.FLUX_OPERATOR_RESOURCE_NAMESPACE)
            for deployment in deployment_list.items:
                deployment_name = deployment.metadata.name
                if deployment_name in cleanup_deployment_list:
                    delete_deployment(api_instance, constants.FLUX_OPERATOR_RESOURCE_NAMESPACE, deployment_name)

            api_instance = client.CoreV1Api()
            cleanup_service_list = constants.CLEANUP_SERVICE_LIST
            service_list = list_service(api_instance, constants.FLUX_OPERATOR_RESOURCE_NAMESPACE)
            for service in service_list.items:
                service_name = service.metadata.name
                if service_name in cleanup_service_list:
                    delete_service(api_instance, constants.FLUX_OPERATOR_RESOURCE_NAMESPACE, service_name)
            print("Cleanup Complete.")
            return

        with Path.open(my_file, "wb") as f:
            pickle.dump(env_dict, f, pickle.HIGHEST_PROTOCOL)