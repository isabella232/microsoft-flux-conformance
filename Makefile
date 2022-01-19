ACR ?= joinnisacr.azurecr.io
IMAGE ?= microsoft-flux-conformance
TAG ?= 0.0.11
SONOBUOY_VERSION ?= 0.55.1

RESOURCE_GROUP ?= joinnis-test
CLUSTER_NAME ?= sonobuoy-test
CLUSTER_TYPE ?= connectedClusters
EXTENSION_NAME ?= flux
SUBSCRIPTION_ID ?= 37524548-5887-4df0-a359-38a687fdb3bc

all: deploy-extension test cleanup-extension

get-dependencies:
	pip install -r requirements.txt

setup: get-dependencies create-cluster create-extension
	mkdir results

create-cluster:
	az connectedk8s connect -g $(RESOURCE_GROUP) -n $(CLUSTER_NAME)

create-extension:
	az k8s-extension create -g $(RESOURCE_GROUP) -c $(CLUSTER_NAME) -n $(EXTENSION_NAME) -t $(CLUSTER_TYPE) --extension-type microsoft.flux

clean:
	rm results/*
	rm *.pkl*

clean-cluster:
	az connectedk8s delete -g $(RESOURCE_GROUP) -n $(CLUSTER_NAME)

login:
	az login
	az acr login --name $(ACR)

docker-build:
	docker build . -t $(ACR)/$(IMAGE):$(TAG) --build-arg SONOBUOY_VERSION=$(SONOBUOY_VERSION)

docker-push:
	docker push $(ACR)/$(IMAGE):$(TAG)

docker-all: docker-build docker-push

test:
	pytest ./src/

cleanup-extension:
	az k8s-extension delete --subscription $(SUBSCRIPTION_ID) -g $(RESOURCE_GROUP) -c $(CLUSTER_NAME) -t $(CLUSTER_TYPE) -n $(EXTENSION_NAME) --yes