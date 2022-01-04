DEFAULT_AZURE_RMENDPOINT = "https://management.azure.com/"

HELM_RELEASE_NAME = 'azure-arc'
HELM_RELEASE_NAMESPACE = 'default'
TIMEOUT = 360
ARC_AGENT_CLEANUP_TIMEOUT = 900

AZURE_ARC_NAMESPACE = 'azure-arc'

METRICS_AGENT_LOG_LIST = ["Successfully connected to outputs.http_mdm", "Wrote batch of"]
METRICS_AGENT_ERROR_LOG_LIST = ["Could not resolve", "Could not parse"]
FLUENT_BIT_LOG_LIST = ["[engine] started (pid=1)", "[sp] stream processor started", "[http_mdm] Flush called for id: http_mdm_plugin"]
FLUENT_BIT_ERROR_LOG_LIST = ["[error] [in_tail] read error, check permissions"]
METRICS_AGENT_CONTAINER_NAME = 'metrics-agent'
FLUENT_BIT_CONTAINER_NAME = 'fluent-bit'

CLUSTER_TYPE = 'connectedClusters'
CLUSTER_RP = 'Microsoft.Kubernetes'

DEFAULT_CASE_RESOURCES_POD_LABEL_LIST = ['arc-k8s-demo']
DEFAULT_CASE_RESOURCE_NAMESPACE = 'default'
DEFAULT_CASE_NAMESPACE_RESOURCE_LIST = ['team-a', 'team-b', 'itops']

CLEANUP_NAMESPACE_LIST = ['arc-k8s-demo', 'team-a', 'team-b', 'itops']
CLEANUP_DEPLOYMENT_LIST = ['arc-k8s-demo']
CLEANUP_SERVICE_LIST = ['arc-k8s-demo']
