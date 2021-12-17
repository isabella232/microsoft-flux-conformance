FROM golang:1.17.3

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get -f -y install dialog apt-utils curl apt-transport-https lsb-release gnupg python3-pip && \
    apt-get install -y git && \
    apt-get install zip -y  && \
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash

RUN az version && \
    az config set extension.use_dynamic_install=yes_without_prompt && \
    az extension add --upgrade --yes --name connectedk8s && \
    az extension add --upgrade --yes --name k8s-extension && \
    az extension add --upgrade --yes --name customlocation && \
    az extension add --upgrade --yes --name appservice-kube

RUN /usr/bin/curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl  \
    &&  mv ./kubectl /usr/local/bin/kubectl

RUN curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash \
    && helm version

RUN python3 -m pip install junit_xml

COPY setup_failure_handler.py /
COPY flux_conformance.sh /

RUN ["chmod", "+x", "/flux_conformance.sh"]
ENTRYPOINT [ "/flux_conformance.sh" ]