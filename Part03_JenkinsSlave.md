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
        pip install Flask pytest
    USER 1001
    ```
    
    -(**Note**: The Dockerfile above will deploy the default, stable, Python
    which at the time of writing is Python 2.7 for RHEL 7. I would have 
    preferred to use Python 3, but that requires further community projects to
    be added to the "yum install" command, which is beyond the scope of this
    article.)
    
    **Note** also that we install just the Python modules necessary to run 
    the unit tests.

3. The template is then used to create the slave node via the `new app`
   command. **Only run this once**:
    ```bash
    oc new-app -f oc new-app -f python-jenkins-slave-node/oc_template.yaml
    ```

4. Build the slave node: At this stage, we have configured Openshift via the
   template to be able to build the slave node, but the Docker Image does
   not yet exist, so Jenkins doesn't know about it; The next step is to build
   it.
   - in the CLI `oc start-build python-jenkins-slave`
   - alternatively, in the UI, navigate to the "python-jenkins-slave" in the
     Builds page, and click the "Start Build" button.
 

5. We can now **use** the slave node as part of our CI process by referring to 
   it in the Jenkinsfile. For example, clone our repository and run the
   unit tests: Note you can have multiple `node` statements
   ```yaml
   node {                                        // Runs on the Jenkins master
       stage('build') {
           ...                         // The build stage described previously
       }
   }
   node('python-jenkins-slave') {                 // Runs on the jenkins slave
       stage('run tests') {
           sh('''(python --version; git --version) | true''')
           sh('''git clone https://github.com/andywis/openshift-sandbox.git''')
           sh('''cd openshift-sandbox && pytest tests.py''')
       }
    }
    ```
    In the above example, printing the Python version and Git version is
    helpful if you need to determine why a test failed. Note they are also
    wrapped in a `(cmd) | true` structure which forces this line to return an
    exit status of zero, so that Jenkins will carry on even if this line fails.
    
    

## Suggested improvements:
* Ensure Virtualenv is installed via the Dockerfile, then the "pip install"
  tasks can take place in the Jenkinsfile instead.
    
* Automatically rebuilding the slave - The template can be extended to add 
  a pipeline that can update the
   image should the upstream (base) image change. For more details, see:
   * https://github.com/UKCloud/jenkins-openstack-slave-pipeline
   * https://ukcloud.com/news-resources/news/blog/part-openshift-deploying-openshift-openshift-pipelines
   * https://docs.openshift.org/latest/dev_guide/templates.html
   
* There are recommended ways of integrating Pytest into Jenkins; see
  https://jenkins.io/solutions/python/