# Using a Jenkins slave in your pipeline

**The challenge**: We want to run the tests within Jenkins, but Jenkins does
not have the packages and dependencies that your application needs.

In the previous article, we discovered how to run a shell command within the
running container, so we could execute some tests. In this article, we 
describe a different approach where the tests run within Jenkins instead.

## Sample code
First, we will write a unit test script using **Pytest**. Pytest is not
necessary for the application to run, so we won't add it to "requirements.txt".
This means that we can't "Exec" into the container to run the unit tests.

Add a file called "tests.py" to the repo. It should look like this:
```python
from wsgi import hello

def test_default_route_method_says_hello():
    assert hello() == "Hello World!"
```
The code above is a (very simplified) unit test that can be run with 
`pytest tests.py`. It imports the function 'hello' from wsgi.py and defines
a test which  contains an assert statement. Pytest looks for functions
starting "test_" so it will find this one function.


## Build a Jenkins slave with the correct dependencies
Jenkins allows you to run jobs on specified nodes, called slaves. 
Openshift provides slave node images for both Maven and NodeJS, in both
RHEL7 and CentOS flavours 
([more here](https://blog.openshift.com/openshift-3-3-pipelines-deep-dive/)).
For our purposes, we want a slave node with Python tooling (including Pytest),
so we will  have to build our own slave node.

We will accomplish this with an
[Openshift Template](https://docs.openshift.org/latest/dev_guide/templates.html).
The template defines a BuildConfig that constructs our new slave node as
a Docker image, from a base image and a Dockerfile. The template also needs to
specify the base image and the resultant image as "ImageStreams"

1. Create the template. See 
   [the template in this repo](python-jenkins-slave-node/oc_template.yaml)
   which explains what's going on.

1. Create a Dockerfile as below:
   ```yaml
    FROM registry.access.redhat.com/openshift3/jenkins-slave-base-rhel7:latest
    USER root
    RUN yum install -y python-devel gcc && \
        curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && \
        python get-pip.py && \
        pip install pytest && \
    USER 1001
    ```
    
    -(**Note**: The Dockerfile above will deploy the default, stable, Python
    which at the time of writing is Python 2.7 for RHEL 7. I would have 
    preferred to use Python 3, but that requires further community projects to
    be added to the "yum install" command, which is beyond the scope of this
    article.)

3. The template is then used to create the slave node via the `new app`
   command. **Only run this once**:
    ```bash
    oc new-app -f oc new-app -f python-jenkins-slave-node/oc_template.yaml
    ```

At this stage, we have a slave node, but Jenkins doesn't know about it.
**YOU NEED TO RUN A BUILD**
- see gareth's problems with Pip
  https://github.com/UKCloud/jenkins-openstack-slave-pipeline/commit/1f7bf8124537ac0b3637c78ade48f1dfd4f491b8
- see https://pip.pypa.io/en/stable/installing/  

5. We can now **use** the slave node as part of our CI process by referring to 
   it, e.g.
   ```yaml
   node('python-jenkins-slave') {
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
   
1. The template can be extended to add a pipeline that can update the
   image should the upstream (base) image change.
   
See https://github.com/UKCloud/jenkins-openstack-slave-pipeline

See also
    https://docs.openshift.org/latest/dev_guide/templates.html