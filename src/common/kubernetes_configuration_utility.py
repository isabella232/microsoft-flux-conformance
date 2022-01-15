import pytest

from azure.mgmt.kubernetesconfiguration import SourceControlConfigurationClient
from azure.mgmt.kubernetesconfiguration.v2022_01_01_preview.models import (
    FluxConfiguration,
    GitRepositoryDefinition,
    RepositoryRefDefinition,
    KustomizationDefinition,
    DependsOnDefinition,
)


# This function returns the python client to interact with resources under the namespace 'Microsoft.KubernetesConfiguration'
def get_kubernetes_configuration_client(
    credential, subscription_id, base_url=None, credential_scopes=None, api_version=None
):
    return SourceControlConfigurationClient(
        credential,
        subscription_id,
        base_url=base_url,
        credential_scopes=credential_scopes,
        api_version=api_version,
    )


# This function returns the python client to interact with the connected cluster resource
def get_flux_configuration_client(
    credential, subscription_id, base_url=None, credential_scopes=None, api_version=None
):
    try:
        return get_kubernetes_configuration_client(
            credential,
            subscription_id,
            base_url=base_url,
            credential_scopes=credential_scopes,
            api_version=api_version,
        ).flux_configurations
    except Exception as e:
        pytest.fail(
            "Error occured while creating source control configuration client: "
            + str(e)
        )


# This function creates a new kubernetes configuration on a given cluster
def create_flux_configuration(
    kc_client,
    resource_group_name,
    cluster_rp,
    cluster_type,
    cluster_name,
    configuration_name,
    repository_url,
    kustomizations,
    namespace="default",
    branch="main",
    scope="cluster",
    https_ca_cert=None,
):

    repository_ref = RepositoryRefDefinition(branch=branch)
    git_repository = GitRepositoryDefinition(
        url=repository_url, repository_ref=repository_ref, https_ca_cert=https_ca_cert
    )
    flux_configuration = FluxConfiguration(
        source_kind="GitRepository",
        namespace=namespace,
        scope=scope,
        git_repository=git_repository,
        kustomizations=kustomizations,
    )
    try:
        return kc_client.begin_create_or_update(
            resource_group_name,
            cluster_rp,
            cluster_type,
            cluster_name,
            configuration_name,
            flux_configuration,
            polling=False,
        ).result()
    except Exception as e:
        pytest.fail(
            "Error occurred while creating the kubernetes configuration resource: "
            + str(e)
        )


def create_flux_configuration_kustomization(path, deps):
    return KustomizationDefinition(
        path=path,
        depends_on=[DependsOnDefinition(kustomization_name=dep) for dep in deps],
    )


def delete_kubernetes_configuration(
    kc_client,
    resource_group_name,
    cluster_rp,
    cluster_type,
    cluster_name,
    configuration_name,
    force_delete=False,
):
    return kc_client.begin_delete(
        resource_group_name,
        cluster_rp,
        cluster_type,
        cluster_name,
        configuration_name,
        polling=False,
        force_delete=force_delete,
    )


# This function gets a kubernetes configuration resource
def show_kubernetes_configuration(
    kc_client,
    resource_group_name,
    cluster_rp,
    cluster_type,
    cluster_name,
    configuration_name,
):
    try:
        return kc_client.get(
            resource_group_name,
            cluster_rp,
            cluster_type,
            cluster_name,
            configuration_name,
        )
    except Exception as e:
        pytest.fail(
            "Error occurred while fetching the kubernetes configuration resource: "
            + str(e)
        )
