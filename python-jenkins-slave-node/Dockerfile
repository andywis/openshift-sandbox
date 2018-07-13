FROM registry.access.redhat.com/openshift3/jenkins-slave-base-rhel7:latest
USER root

# First, install the IUS project to give us access to Python3
# Then install Python, Pip and Pytest
RUN yum install -y epel-release && \
     yum install -y python36 python36-pip vim gcc yum-utils && \
     pip install pytest && \
     pip install python-openstackclient
USER 1001
