FROM registry.access.redhat.com/openshift3/jenkins-slave-base-rhel7:latest
USER root

RUN yum install -y python-devel gcc && \
     curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && \
     python get-pip.py && \
     pip install Flask pytest && \
     pip install python-openstackclient
USER 1001
