FROM python:3.9

RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pytest pytest-xdist filelock junit_xml kubernetes azure.identity msrestazure azure-mgmt-hybridkubernetes azure-mgmt-kubernetesconfiguration==1.0.0b1

RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

RUN az extension add -n connectedk8s --yes --debug
RUN az extension add -n k8s-extension --yes --debug

RUN /usr/bin/curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl  \
    &&  mv ./kubectl /usr/local/bin/kubectl

RUN curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash \
    && helm version

COPY ./flux_conformance.sh /
COPY ./src/ /test/

RUN ["chmod", "+x", "/flux_conformance.sh"]
ENTRYPOINT ["./flux_conformance.sh"]