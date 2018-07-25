# A worked example
In this article, I'll work through the process of setting up a Pipeline
in a "dev" environment against a private Git repository protected by an
SSH key.

As described in [Part 3](Part03_JenkinsSlave.md), we need a Dockerfile so we
can create a customised Jenkins slave node, and it has to be pushed to your
Git repository before it can be used.

## Dockerfile
To start, the Dockerfile looks like this, which should be enough to allow us
to create a Python Virtual Environment. (we'll create a venv and install the
Python modules within it, in a later step.)

```text
FROM registry.access.redhat.com/openshift3/jenkins-slave-base-rhel7:latest
USER root
RUN yum install -y python-devel gcc python-virtualenv && \
     curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && \
     python get-pip.py

USER 1001
```

## Slave-Node build config.
We also need the BuildConfig which tells OpenShift how to build the Jenkins
slave node. Again, this is almost identical to 
[the template we saw before](python-jenkins-slave-node/oc_template.yaml),
but we need to configure the git secret. 

Below are two sections from the template; first part of the BuildConfig for 
building the slave node, and second, one of the parameters.
The Buildconfig defines a "sourceSecret" within the "source" block, which tells
OpenShift what the private key is to access the repository. The name of the
secret here is same as the name of the secret within the OpenShift Console UI.

The parameter shown here has a default value showing the correct format for a
Git URL.
```text
    ...
      source:
        contextDir: ${path_to_dockerfile}
        git:
          ref: ${repo_branch_name}
          uri: ${repo_url}
        type: Git
        sourceSecret:                  # 
          name: my_github_secret       # <-- Git secret
      strategy:
        dockerStrategy:
          from:
            kind: ImageStreamTag
            name: jenkins-slave-base-rhel7:latest
        type: Docker
        
    ...
    
- description: The URL of the repository with your application source code.
  displayName: Git Repository URL
  name: repo_url
  required: true
  value: git@github.com:andywis/my-private-repo.git           # <-- must be an SSH URL
  
```
**Note** that the Git URL must be an SSH-style URL as shown above, and not an
HTTPS URL. (HTTPS URLs don't work with a "dockerStrategy")

# Build the slave node
With the two files above, we can build the infrastructure needed for our
pipeline. Let's assume you've already got the beginnings of your application, 
and want to build the pipeline so you can test it...

* Log in `oc login https://blah.blah...`

* Create a project in OpenShift that represents your "dev" environment, 
e.g. `oc new-project myproject-dev`

* Create the app within the project (this assumes you've started writing the app)
`oc new-app https://github.com/andywis/my-private-repo.git`

* Spin up an Ephemeral Jenkins container in this project: 
`oc new-app jenkins-ephemeral`

* Build a Jenkins slave node for use in our pipeline.  There are 2 steps:
  - First, configure the imagestreams and the build config for the slave: the
  file "pipeline-template.yaml" is the template file discussed above.
  `oc new-app -f oc new-app -f pipeline-template.yaml`
  - Second, build the slave:
  `oc start-build python-jenkins-slave`
  
We should now be in a position to build the pipeline itself.

# The Pipeline
The Jenkins Pipeline definition can be defined within the BuildConfig. Again, 
we can base it on the [previous example](part_01_pipeline_build_config.yaml).

An advantage of embedding the Jenkinsfile definition in the build config is
that we can continue to develop it without having to go round the 
`git add, git commit, git push ` loop.

Here is an example pipeline that you might have embedded in your pipeline build
config.
```text
        /* Build the app; this can run on any node. */
        node {
          stage('build') {
            openshiftBuild(buildConfig: 'my-app-name', showBuildLogs: 'true')
          }
        }
        
        /* Run the tests; these have to run on the Jenkins slave node
           we built in the previous step, because they rely on certain
           packages that we installed via the Dockerfile (namely 'virtualenv')
        */
        node('python-jenkins-slave') {
          stage('run tests') {
            /* Print out the versions of Python and Git, so we know they are
               installed, and so we know what versions the tests were run
               against.
            */
            sh('''
              python --version
              git --version
            ''')

            /* Extract Github key and configure SSH so we can git clone.
               This is the same secret we used in the buildconfig above;
               this time, it allows us to "git clone" the repo into the slave
               node.
               
               Note that we have to Base64-decode the secret.
            */
            sh('''
              oc get secrets my_github_secret --template='{{index .data "ssh-privatekey" }}' | base64 --decode  > /tmp/pipeline_private_key
              chmod 0600 /tmp/pipeline_private_key
              mkdir -p ~/.ssh && chmod 700 ~/.ssh
              ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
              ''')

            /* We can now clone the repo. Use ssh-add to add the private key
               to our shell session, and clone the repo.
               
               The branch name is specified here (as I was using a different
               branch)
            */
            sh('''
              eval $(ssh-agent -s)
              ssh-add /tmp/pipeline_private_key
              git clone git@github.com:andywis/my-private-repo.git -b master
              
            ''')

            /* Finally, we can create a virtual python environment with
               virtualenv, install the dependencies as listed in the source
               code, and run the tests.
               
               In this example, the "pytest" program is listed in 
               "test_requirements.txt" (the list of requirements for testing)
            */
            sh('''
              cd my-private-repo
              virtualenv _venv
              source _venv/bin/activate
              pip install -r requirements.txt
              pip install -r test_requirements.txt
              pytest tests.py
            ''')
          }
}
```

# Python3 in RHEL 7
As a final step, I wanted to use Python3, rather than the default Python 2.7 that
comes with RHEL7. I tried using the
[IUS Release of Python3](https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-centos-7)
and the
[EPEL approach](https://stackoverflow.com/questions/8087184/installing-python-3-on-rhel)
but neither of these worked. Eventually, I discovered the
[EPEL-from-Fedora](https://www.badllama.com/content/installing-python-3x-rhel-7-centos-7)
approach did work.

This requird some fidding around with the image to get the "yum install" 
commands right. I found the easiest thing was to pull the image into a local
Docker environment 

```text
docker pull registry.access.redhat.com/openshift3/jenkins-slave-base-rhel7:latest
```

and run bash in the container with:

```text
docker run -it --entrypoint /bin/bash registry.access.redhat.com/openshift3/jenkins-slave-base-rhel7
```
I could then run "yum" commands to test the lines in the Dockerfile. Using this
approach, I was able to determine the installation script for Python 3.

(I tried using `oc run temp --image=<ImageName> -it --restart=Never -- /bin/bash` but
this gives me a regular user, not the root user, so is less useful for playing
with "yum install")
 
The installation script for Python3 turns out to be as follows:

```text
RUN rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
     yum install -y python36 python34-virtualenv && \
     python3 -m ensurepip && \
     ln -s /usr/bin/virtualenv-3 /usr/bin/virtualenv && \
     ln -s /usr/bin/pip3 /usr/bin/pip
```

We now have `python` pointing to Python2, as required by the OS, and `python3`
being the one we want to use for our tests. The symbolic links for `virtualenv`
and `pip` mean we have less to alter in our pipeline code. Note that we can 
safely mix Python36 and python34-virtualenv in the Dockerfile. This is because
virtualenv doesn't exist for 36 yet in the EPEL repositories.

Regrettably, we'll need to keep an eye on this in case the EPEL is updated.
We also need to know the naming convention used by EPEL to refer to different
versions of Python (e.g. python36 vs python3.6)

The final stage of the Jenkinsfile can now be modified to use python3:

```text
            sh('''
              cd my-private-repo
              virtualenv -p python3.6 _venv
              source _venv/bin/activate
              python --version
              pip install -r requirements.txt
              pip install -r test_requirements.txt
              pytest tests.py
            ''')
```
