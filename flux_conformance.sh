#!/bin/bash

set -x
set -e

results_dir="${RESULTS_DIR:-/tmp/results}"

function waitForResources {
    available=false
    max_retries=60
    sleep_seconds=10
    RESOURCE=$1
    NAMESPACE=$2
    for i in $(seq 1 $max_retries)
    do
    if [[ ! $(kubectl wait --for=condition=available ${RESOURCE} --all --namespace ${NAMESPACE}) ]]; then
        sleep ${sleep_seconds}
    else
        available=true
        break
    fi
    done
    
    echo "$available"
}

# saveResults prepares the results for handoff to the Sonobuoy worker.
# See: https://github.com/vmware-tanzu/sonobuoy/blob/master/docs/plugins.md
saveResults() {
  cd ${results_dir}

    # Sonobuoy worker expects a tar file.
	tar czf results.tar.gz *

	# Signal to the worker that we are done and where to find the results.
	printf ${results_dir}/results.tar.gz > ${results_dir}/done
}

# Ensure that we tell the Sonobuoy worker we are done regardless of results.
trap saveResults EXIT

if [[ -z "${TENANT_ID}" ]]; then
  echo "ERROR: parameter TENANT_ID is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${SUBSCRIPTION_ID}" ]]; then
  echo "ERROR: parameter SUBSCRIPTION_ID is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${RESOURCE_GROUP}" ]]; then
  echo "ERROR: parameter RESOURCE_GROUP is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${CLUSTER_NAME}" ]]; then
  echo "ERROR: parameter CLUSTER_NAME is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${CLIENT_ID}" ]]; then
  echo "ERROR: parameter CLIENT_ID is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${CLIENT_SECRET}" ]]; then
  echo "ERROR: parameter CLIENT_SECRET is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${FLUX_RELEASE_TRAIN}" ]]; then
  echo "ERROR: parameter FLUX_RELEASE_TRAIN is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${FLUX_RELEASE_NAMESPACE}" ]]; then
  echo "ERROR: parameter FLUX_RELEASE_NAMESPACE is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

if [[ -z "${FLUX_VERSION}" ]]; then
  echo "ERROR: parameter FLUX_VERSION is required." > ${results_dir}/error
  python3 setup_failure_handler.py
fi

# Login with service principal
az login --service-principal \
  -u ${CLIENT_ID} \
  -p ${CLIENT_SECRET} \
  --tenant ${TENANT_ID} 2> ${results_dir}/error || python3 setup_failure_handler.py

# Wait for resources in ARC ns
waitSuccessArc="$(waitForResources deployment azure-arc)"
if [ "${waitSuccessArc}" == false ]; then
    echo "deployment is not avilable in namespace - azure-arc"
    exit 1
fi

az extension add --name k8s-extension 2> ${results_dir}/error || python3 setup_failure_handler.py

az k8s-extension create \
    --cluster-name $CLUSTER_NAME \
    --resource-group $RESOURCE_GROUP \
    --cluster-type connectedClusters \
    --extension-type Microsoft.Flux \
    --subscription $SUBSCRIPTION_ID \
    --scope cluster \
    --release-train $FLUX_RELEASE_TRAIN \
    --name flux \
    --release-namespace $FLUX_RELEASE_NAMESPACE \
    --config image-automation-controller.enabled=true \
    --config image-reflector-controller.enabled=true \
    --version $FLUX_VERSION 2> ${results_dir}/error || python3 setup_failure_handler.py 

# Wait for resources in osm-arc release ns
waitSuccessArc="$(waitForResources deployment $FLUX_RELEASE_NAMESPACE)"
if [ "${waitSuccessArc}" == false ]; then
    echo "deployment is not avilable in namespace - $FLUX_RELEASE_NAMESPACE"
    exit 1
fi

sleep 60

kubectl delete ns $FLUX_RELEASE_NAMESPACE