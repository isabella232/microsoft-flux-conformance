DEFAULT_AZURE_RMENDPOINT = "https://management.azure.com/"

HELM_RELEASE_NAME = 'azure-arc'
HELM_RELEASE_NAMESPACE = 'default'
TIMEOUT = 360
ARC_AGENT_CLEANUP_TIMEOUT = 900

AZURE_ARC_NAMESPACE = 'azure-arc'

CLUSTER_TYPE = 'connectedClusters'
CLUSTER_RP = 'Microsoft.Kubernetes'

DEFAULT_CASE_RESOURCES_POD_LABEL_LIST = ['arc-k8s-demo']
DEFAULT_CASE_RESOURCE_NAMESPACE = 'default'
DEFAULT_CASE_NAMESPACE_RESOURCE_LIST = ['team-a', 'team-b', 'itops']

CLEANUP_NAMESPACE_LIST = ['arc-k8s-demo', 'team-a', 'team-b', 'itops']
CLEANUP_DEPLOYMENT_LIST = ['arc-k8s-demo']
CLEANUP_SERVICE_LIST = ['arc-k8s-demo']
FLUX_OPERATOR_RESOURCE_NAMESPACE = 'default'
