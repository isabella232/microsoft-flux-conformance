DEFAULT_AZURE_RMENDPOINT = "https://management.azure.com/"

HELM_RELEASE_NAME = "azure-arc"
HELM_RELEASE_NAMESPACE = "default"
TIMEOUT = 360
ARC_PLATFORM_PLUGIN_POLL_TIMEOUT = 900

FLUX_API_VERSION = "2022-01-01-preview"

AZURE_ARC_NAMESPACE = "azure-arc"

CLUSTER_TYPE = "connectedClusters"
CLUSTER_RP = "Microsoft.Kubernetes"

DEFAULT_TEST_REPOSITORY_URL = "https://github.com/Azure/arc-k8s-demo"
DEFAULT_TEST_NAMESPACE = "default"
DEFAULT_TEST_BRANCH = "main"
DEFAULT_TEST_NAME = "default"
DEFAULT_TEST_SCOPE = "cluster"

CA_CERT_TEST_REPOSITORY_URL = "https://gitops-bitbucket-test-server.eastus.cloudapp.azure.com/scm/git/flux2-kustomize-helm-example.git"
CA_CERT_TEST_NAMESPACE = "https-ca"
CA_CERT_TEST_BRANCH = "main"
CA_CERT_TEST_NAME = "https-ca"
CA_CERT_TEST_SCOPE = "cluster"

DEFAULT_CASE_NAMESPACE_RESOURCE_LIST = ["team-a", "team-b", "itops"]
CA_CERT_CASE_NAMESPACE_RESOURCE_LIST = ["nginx", "redis", "podinfo"]

CLEANUP_NAMESPACE_LIST = [
    "arc-k8s-demo",
    "team-a",
    "team-b",
    "itops",
    "nginx",
    "redis",
    "podinfo",
    "https-ca-file",
]

CLEANUP_DEPLOYMENT_LIST = [("default", "arc-k8s-demo")]
CLEANUP_SERVICE_LIST = [("default", "arc-k8s-demo")]
