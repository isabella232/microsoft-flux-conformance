ACR ?= joinnisacr.azurecr.io
IMAGE ?= microsoft-flux-conformance
TAG ?= 0.0.6

RESOURCE_GROUP ?= joinnis-test
CLUSTER_NAME ?= sonobuoy-test
CLUSTER_TYPE ?= connectedClusters
EXTENSION_NAME ?= flux
SUBSCRIPTION_ID ?= 37524548-5887-4df0-a359-38a687fdb3bc

all: deploy-extension test cleanup-extension

setup-venv:
	python3 -m venv env

activate:
	source ./env/bin/activate

get-dependencies:
	pip install -r requirements.txt

setup: get-dependencies
	mkdir results

clean:
	rm results/*
	rm *.pkl*

login:
	az login
	az acr login --name $(ACR)

build:
	docker build . -t $(ACR)/$(IMAGE):$(TAG)
	docker push $(ACR)/$(IMAGE):$(TAG)

test:
	source ./setup-test.sh
	pytest ./src/

deploy-extension:
	az k8s-extension create --subscription $(SUBSCRIPTION_ID) -g $(RESOURCE_GROUP) -c $(CLUSTER_NAME) -t $(CLUSTER_TYPE) -n $(EXTENSION_NAME) --extension-type microsoft.flux

cleanup-extension:
	az k8s-extension delete --subscription $(SUBSCRIPTION_ID) -g $(RESOURCE_GROUP) -c $(CLUSTER_NAME) -t $(CLUSTER_TYPE) -n $(EXTENSION_NAME) --yes