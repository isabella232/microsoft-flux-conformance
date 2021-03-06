#!/bin/bash
set -x

results_dir="${RESULTS_DIR:-/tmp/results}"

waitForResourcesReady() {
   ready=false
   max_retries=60
   sleep_seconds=10
   NAMESPACE=$1
   RESOURCETYPE=$2
   RESOURCE=$3
    # if resource not specified, set to --all
    if [ -z $RESOURCE ]; then
       RESOURCE="--all"
    fi
    for i in $(seq 1 $max_retries)
    do
    if [[ ! $(kubectl wait --for=condition=Ready ${RESOURCETYPE} ${RESOURCE} --namespace ${NAMESPACE}) ]]; then
        echo "waiting for the resource:${RESOURCE} of the type:${RESOURCETYPE} in namespace:${NAMESPACE} to be ready state, iteration:${i}"
        sleep ${sleep_seconds}
    else
        echo "resource:${RESOURCE} of the type:${RESOURCETYPE} in namespace:${NAMESPACE} in ready state"
        ready=true
        break
    fi
    done

    echo "waitForResourcesReady state: $ready"
}


waitForArcK8sClusterCreated() {
    connectivityState=false
    max_retries=60
    sleep_seconds=10
    for i in $(seq 1 $max_retries)
    do
      echo "iteration: ${i}, clustername: ${CLUSTER_NAME}, resourcegroup: ${RESOURCE_GROUP}"
      clusterState=$(az connectedk8s show --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --query connectivityStatus -o json)
      clusterState=$(echo $clusterState | tr -d '"' | tr -d '"\r\n')
      echo "cluster current state: ${clusterState}"
      if [ ! -z "$clusterState" ]; then
         if [[ ("${clusterState}" == "Connected") || ("${clusterState}" == "Connecting") ]]; then
            connectivityState=true
            break
         fi
      fi
      sleep ${sleep_seconds}
    done
    echo "Arc K8s cluster connectivityState: $connectivityState"
}

waitForCIExtensionInstalled() {
    installedState=false
    max_retries=40
    sleep_seconds=10
    for i in $(seq 1 $max_retries)
    do
      echo "iteration: ${i}, clustername: ${CLUSTER_NAME}, resourcegroup: ${RESOURCE_GROUP}"
      provisioningState=$(az k8s-extension show  --cluster-name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --cluster-type connectedClusters --name flux --query provisioningState -o json)
      provisioningState=$(echo $provisioningState | tr -d '"' | tr -d '"\r\n')
      echo "extension provisioning state: ${provisioningState}"
      if [ ! -z "$provisioningState" ]; then
         if [ "${provisioningState}" == "Succeeded" ]; then
            break
         fi
      fi
      sleep ${sleep_seconds}
    done
    echo "microsoft.flux extension installed"
}

validateCommonParameters() {
    if [ -z $TENANT_ID ]; then
	   echo "ERROR: parameter TENANT_ID is required." > ${results_dir}/error
	   python3 setup_failure_handler.py
	fi
	if [ -z $CLIENT_ID ]; then
	   echo "ERROR: parameter CLIENT_ID is required." > ${results_dir}/error
	   python3 setup_failure_handler.py
	fi

	if [ -z $CLIENT_SECRET ]; then
	   echo "ERROR: parameter CLIENT_SECRET is required." > ${results_dir}/error
	   python3 setup_failure_handler.py
	fi
}

validateArcConfTestParameters() {
	if [ -z $SUBSCRIPTION_ID ]; then
	   echo "ERROR: parameter SUBSCRIPTION_ID is required." > ${results_dir}/error
	   python3 setup_failure_handler.py
	fi

	if [ -z $RESOURCE_GROUP ]]; then
		echo "ERROR: parameter RESOURCE_GROUP is required." > ${results_dir}/error
		python3 setup_failure_handler.py
	fi

	if [ -z $CLUSTER_NAME ]; then
		echo "ERROR: parameter CLUSTER_NAME is required." > ${results_dir}/error
		python3 setup_failure_handler.py
	fi
}

addArcConnectedK8sExtension() {
   echo "adding Arc K8s connectedk8s extension"
   az extension add --name connectedk8s 2> ${results_dir}/error || python3 setup_failure_handler.py
}

addArcK8sCLIExtension() {
   echo "adding Arc K8s k8s-extension extension"
   az extension add --name k8s-extension
}

waitForSonobuoy() {
   sonobuoy status --json | jq -r '.plugins[] | select (.plugin == "azure-arc-platform")'.status

   max_retries=60
   sleep_seconds=10
   for i in $(seq 1 $max_retries)
   do
      sonobuoyStatus=$(sonobuoy status --json | jq -r '.plugins[] | select (.plugin == "azure-arc-platform")'.status)
      echo "sonobuoy status: ${sonobuoyStatus}"
      if [ ! -z "$sonobuoyStatus" ]; then
         if [ "${sonobuoyStatus}" == "complete" ]; then
            break
         fi
      fi
      sleep ${sleep_seconds}
   done
   echo "azure-arc-platform plugin has finished"
}

createArcCIExtension() {
	echo "creating extension type: Microsoft.Flux"
  
  az k8s-extension create \
    --cluster-name $CLUSTER_NAME \
    --resource-group $RESOURCE_GROUP \
    --cluster-type connectedClusters \
    --extension-type Microsoft.Flux \
    --subscription $SUBSCRIPTION_ID \
    --scope cluster \
    --name flux \
    --config image-automation-controller.enabled=true \
    --config image-reflector-controller.enabled=true \
    --no-wait 2> ${results_dir}/error || python3 setup_failure_handler.py || exit 1
}

showArcCIExtension() {
  echo "arc ci extension status"
  az k8s-extension show  --cluster-name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --cluster-type connectedClusters --name flux
}

deleteArcCIExtension() {
    az k8s-extension delete --name flux \
    --cluster-type connectedClusters \
	  --cluster-name $CLUSTER_NAME \
	  --resource-group $RESOURCE_GROUP --yes
}

login_to_azure() {
	# Login with service principal
    echo "login to azure using the SP creds"
	az login --service-principal \
	-u ${CLIENT_ID} \
	-p ${CLIENT_SECRET} \
	--tenant ${TENANT_ID} 2> ${results_dir}/error || python3 setup_failure_handler.py || exit 1

	echo "setting subscription: ${SUBSCRIPTION_ID} as default subscription"
	az account set -s $SUBSCRIPTION_ID
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

# validate common params
validateCommonParameters

# validate params
validateArcConfTestParameters

# login to azure
login_to_azure

# add arc k8s connectedk8s extension
addArcConnectedK8sExtension

# wait for arc k8s pods to be ready state
waitForResourcesReady azure-arc pods

# wait for Arc K8s cluster to be created
waitForArcK8sClusterCreated

# wait for sonobuoy plugin to be finished
waitForSonobuoy

# add CLI extension
addArcK8sCLIExtension

# add ARC K8s container insights extension
createArcCIExtension

# show the ci extension status
showArcCIExtension

#wait for extension state to be installed
waitForCIExtensionInstalled

# The variable 'TEST_LIST' should be provided if we want to run specific tests. If not provided, all tests are run

NUM_PROCESS=$(pytest /test/ --collect-only  -k "$TEST_NAME_LIST" -m "$TEST_MARKER_LIST" | grep "<Function\|<Class" -c)

export NUM_TESTS="$NUM_PROCESS"

pytest /test/ --junitxml=/tmp/results/results.xml -d --tx "$NUM_PROCESS"*popen -k "$TEST_NAME_LIST" -m "$TEST_MARKER_LIST"

# cleanup extension resource
deleteArcCIExtension