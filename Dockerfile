FROM python:3.6

ADD ./requirements.txt /requirements.txt
RUN pip install --trusted-host pypi.org -r requirements.txt

RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

RUN az extension add -n connectedk8s --yes --debug
RUN az extension add -n k8s-extension --yes --debug
RUN az config set core.only_show_errors=true

RUN /usr/bin/curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl  \
    &&  mv ./kubectl /usr/local/bin/kubectl

RUN curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash \
    && helm version

# Grab sonobuoy and install it
ARG SONOBUOY_VERSION

RUN curl -L https://github.com/vmware-tanzu/sonobuoy/releases/download/v${SONOBUOY_VERSION}/sonobuoy_${SONOBUOY_VERSION}_linux_amd64.tar.gz --output /bin/sonobuoy.tar.gz
RUN tar -xzf /bin/sonobuoy.tar.gz -C /bin

RUN apt-get install jq --yes

COPY ./flux_conformance.sh /
COPY ./src/ /test/
COPY ./setup_failure_handler.py /

RUN ["chmod", "+x", "/flux_conformance.sh"]
ENTRYPOINT ["./flux_conformance.sh"]