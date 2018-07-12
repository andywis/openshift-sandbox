# Using a Jenkins slave in your pipeline

**The challenge**: Run the tests within Jenkins, but Jenkins does not have
the packages and dependencies that your application needs.


## Build a Jenkins slave with the correct dependencies
In the previous article, we discussed how to log into our running container
to execute a command, which gives us access to the Python modules needed for
our application. This article now discusses an alternative approach where
the code runs within Jenkins.

It will be necessary to install our dependencies (e.g. Python) on Jenkins
so that we can run our test code, for example.
Rather than changing the Jenkins Master, we can build a customised slave node
to do the work. If we were using Maven or NodeJS, there are already slave
images that contain the packages we need, but if we are working in a different
language, e.g. Python, we have to roll our own.





# Ideas...

1. create a new repo for our jenkins-slave.
2. In the repo, create a Dockerfile, like the one in 
   https://ukcloud.com/news-resources/news/blog/part-ii-openshift
   ```yaml
    FROM registry.access.redhat.com/openshift3/jenkins-slave-base-rhel7:latest
    USER root
    RUN yum install -y python-devel vim && \
        curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && \
        python get-pip.py && \
        pip install pytest && \
    USER 1001
    ```
3. create a build config in OpenShift which references the Dockerfile and tells
    it how to perform the build. The command is:
    ```bash
    oc new-app -f template_file.yaml \
      -p NAME=python-jenkins-slave
    # See https://github.com/UKCloud/jenkins-openstack-slave-pipeline/blob/master/setup-ci.sh
    ```
    For the template, see (**where??**.)
    The template lists multiple buildConfigs:
     * The imageStream for the base image for a Jenkins slave
     * The BuildConfig for creating the slave using the DockerStrategy
     * Hooks to rebuild when the parent image or the Github repo get updated.
     
    This template idea is based on
    https://github.com/UKCloud/jenkins-openstack-slave-pipeline/blob/master/openshift-yaml/template-openstackclient-jenkins-slave.yaml
    
    See also
    https://docs.openshift.org/latest/dev_guide/templates.html
    
    
4. Create a Pipeline to build the slave

5. We can now USE the slave node as part of our CI process by referring to 
   it, e.g.
   ```yaml
   node('my-python-jenkins-slave') {
        stage('do something') {
            ...
        }
   }
   ```
   
   
### Automatically rebuilding the slave
1. Within OpenShift we create two image streams. An image stream allows us to
   automatically perform actions such us building an image or undertaking a
   deployment when certain actions are triggered.

1. Our first image stream monitors the upstream Jenkins slave image from RedHat
   for any changes. Our second monitors for any changes to our own Jenkins
   slave image that we produce as an artifact to our build pipeline. 
   
1. The "Pipeline build config" is told to monitor the upstream image from 
  RedHat
  
1. Configure a Git Hook so that any changes you make to the custom slave 
   node will rebuild the slave node image.
   

## Write some sample test code
We also need a test script that we can run.
Add a file called "tests.py" to the repo. It should look like this:
```python
from wsgi import hello

def test_default_route_method_says_hello():
    assert hello() == "Hello World!"
```

The code above is a (very simplified) unit test that can be run with 
`pytest tests.py`. We will use this later.