# Microsoft.Flux Conformance Testing

## Development

1. Setup a virtual environment for Python

```bash
python -m venv env
source env/bin/activate
```

2. Create a `setup-test.sh` file in the format of `setup-test.template`

```bash
export TENANT_ID=<TENANT-ID>
export CLIENT_ID=<CLIENT-ID>
export OBJECT_ID=<OBJECT-ID>
export CLIENT_SECRET=<CLIENT-SECRET>
export SUBSCRIPTION_ID=<SUBSCRIPTION-ID>
export RESOURCE_GROUP=<RESOURCE-GROUP>
export CLUSTER_NAME=conformance-testing-arc
export LOCATION=eastus
export RESULTS_DIR=./results
export CUSTOM_KUBECONFIG=~/.kube/config
export NUM_TESTS=1
export CA_CERT_FILE=./src/file/https-ca.cer
```

3. Source the `setup-test.sh` file to override the values in the `Makefile`

```bash
source setup-test.sh
```

To be able to properly run the tests, you will need to create an SPN that has permission to operate over whichever resource group that you plan to create

4. Run the following command to setup the cluster and install the extension

```bash
make setup
```

You can take a look at the `Makefile` to see the exact configuration and the steps that are taken to configure the cluster

5. Run the `test` command to validate the `pytest` tests that you have created work

```bash
make test
```
