# Continuous Integration on OpenShift
In this series, we discuss a number of techniques for configuring CI within
your OpenShift environment.

We will create a simple application in Python and set up a Jenkins Pipeline
where we demonstrate different techniques for running tests, and promoting 
the app to a higher environment.

In CI, an **environment** is a setup that mimics 


## Setting up the Project and Application
We'll start by creating a really simple web application in Python

1. Log in to the OpenShift Container Platform (OCP) CLI:
`oc login https://ocp.blah.blah.blah.com:8443`

1. Create a new OCP Project.
   - List the existing projects with `oc projects`  
   - Create a new one called "andy-test1" with  `oc new-project andy-test1`
   - alternatively, create it in the Web UI by clicking the "New Project"
     button.
     
   If the project already exists, switch to it with e.g. `oc project andy-test1`

1. Create a new source code repository; it must be in a location that can be
   seen by OpenShift (e.g. on github)

1. Create the code for the new application
   - we'll start with something really simple, and gradually add to it as we 
     go.
   - You can clone this repo, or copy the code from 
     [OpenShiftDemos on Github](https://github.com/OpenShiftDemos/os-sample-python)
     into your new repository. The 4 files you'll need are config.py,
     requirements.txt, wsgi.py and .s2i/environment

1. Create a new App within this project, e.g. : 
    `oc new-app https://github.com/myGitHubUser/myProjectName.git`
    Obviously replacing the example github URL shown above with your own,
    which you can obtain from the green "Clone or download" button on the
    Github page for your project. **Make sure you use the HTTPS clone URL**
    as the "ssh" clone URL won't work.
    - OpenShift will inspect the code and decide this is Python based on
      the file "requirements.txt"
    - The app will be deployed automatically. You can watch it being
      deployed on the overview page.
    - We can test the app is working by creating a "Route" and navigating to
      the homepage, via the OpenShift web interface.
    - As we will continue development, destroy the "Route" after testing that
      the app is working.
    - For example, if you want to copy this demo app 'verbatim', you could
      create the app with `oc new-app https://github.com/andywis/openshift-sandbox.git`
      Note the app will be called "openshift-sandbox".

1. Now we have a very simple web application (called **openshift-sandbox** if 
   you used my demo), we can develop it to add pipelines.
   
-------

## Setting up the Pipeline

1. Create the Jenkins container within your project. OpenShift will 
   recognise the name and create everything you need. To create the Jenkins
   container, run: `oc new-app jenkins-ephemeral` (see 
   [the OpenShift documentation](https://docs.openshift.com/container-platform/3.7/dev_guide/dev_tutorials/openshift_pipeline.html#creating-the-jenkins-master)
   for more information)
   
1. Once the Jenkins app has started, click the Route to the Jenkins
   instance, and log in. You then need to authorise Jenkins to access the 
   OpenShift account (just click the 'allow' button)
   
1. Next, create the pipeline by constructing a new "BuildConfig" file. The
   code block below shows an example. It does the following:
   - creates a BuildConfig (line 1) called "sample-pipeline" (line 4).
   - The BuildConfig is a Jenkins Pipeline (line 7 and the last line)
   - The Jenkinsfile for the pipeline is embedded in the BuildConfig within
     the block starting on line 8. (the `|-` characters mark the start of a 
     multi-line block in Yaml)
   - The name of the "Build" is contained in the **openshiftbuild(...)*** line.
     In this example, the build is 'openshift-sandbox', which is the name
     of the app, and the name of the build created above by "oc new-app"
    ```yaml
    kind: "BuildConfig"
    apiVersion: "v1"
    metadata:
      name: "sample-pipeline"
    spec:
      strategy:
        jenkinsPipelineStrategy:
          jenkinsfile: |-
            node {
              stage('build') {
                openshiftBuild(buildConfig: 'openshift-sandbox', showBuildLogs: 'true')
              }
              stage('test') {
                sh('''hostname; pwd; ls -l;''')
              }
            }
        type: JenkinsPipeline
    ```
    (see the file [part_01_pipeline_build_config.yaml](part_01_pipeline_build_config.yaml))

1. Create the pipeline by running "oc create" with the above file:
    ```bash
    oc create -f pipeline_file.yaml
    ```
    The "thing" created by oc create is completely described by the 
    file (in this case, the "thing" is a Pipeline, which is a BuildConfig)


### Things to notice:
   -  When we created the app earlier, the "oc new-app" command created a
      BuildConfig with the default "strategy", which is the 
      **sourceStrategy**. This pulls your code from source control, builds
      and immediately deploys it. A Pipeline is a different sort of
      Build Config that uses a 
      **jenkinsPipelineStrategy** instead
   -  If you want to place the Jenkinsfile in a separate file, rather than
      embedding it in the Yaml, you will need to use the **jenkinsfilePath**
      directive instead; note you also need to specify a GIT URI which
      states where the jenkinsfile comes from, and the file must exist in
      the repository. e.g.
   
        ```yaml
        spec:
          strategy:
            jenkinsPipelineStrategy:
              jenkinsfilePath: path/to/your/jenkinsfile
          source:
            git:
              uri: https://github.com/andywis/openshift-sandbox
        ```

  -  In the Jenkinsfile, "node" takes no arguments. If we specify an argument, 
     e.g. `node('maven') { ... }` the Jenkins job will create a slave node 
     based on the "Maven" node image. 
     ([more here](https://blog.openshift.com/openshift-3-3-pipelines-deep-dive/))
     Four slave node images are available: maven and nodejs, both in rhel7 and
     CentOS flavours. They all contain `oc` and `git` tooling.
     
     In a later article, we will discuss how to create our own slave image
     
     
  -  If the slave doesn't exist, you may see a message in the console log 
     saying "Jenkins doesn’t have label maven" Jenkins will then create a
     slave node matching that label. It may take a while to start up.


## How to arrange your deployment environments

Now we have a very basic pipeline. Let's turn it into something useful.

The Jenkinsfile above calls `openshiftBuild` which builds the app and 
deploys it to the current project. The first thing to understand is that
we can't build without deploying, and we have to deploy the app *somewhere*
before we can test it.

Which begs the question **How do you test something before you deploy it?**

The answer is to create a *set* of OpenShift projects, and code the pipeline
so that it promotes the build from one project to another. For example, we
could have a "dev"(elopment) project and a "prod"(uction) project. Our 
pipeline should live in the "dev" project and do the following:
* build the app and deploy locally (i.e. to "dev")
* Run the tests against the build we've just deployed
* If the tests pass, promote the build to a different project, by deploying
  it to a different project with something like the following:
  ```yaml
    stage('deploy') {  // TODO: confirm if this is valid
        openshiftDeploy(deploymentConfig: 'my-prod-project')
    }
  ```
  
This means that our OpenShift projects can map almost exactly to the way we have
designed our DevOps environments; we can have projects with names like "dev",
"test", "integ", "preprod" and "prod", or whatever. A pipeline could exist
in each environment which deploys the image to the next environment if the
tests have passed.

We will develop this idea in a future article.

## Running unit tests
The first step is to ensure the unit tests are passing. We want to deploy the
app to "dev", run the unit tests, and detect whether the tests pass or fail.

We could run the unit tests in two ways:
1. Deploy the container, "docker exec" into it and run the unit tests there
2. Build and deploy a separate container that contains the code and the
   dependencies, and run the unit tests there.
   
We will cover both here...

See [part 2](Part02_UnitTests1.md) where we discuss the "docker exec" option.

# TODO
* The correct way to pause a pipeline, e.g. to wait until manual testing has 
  completed.
* Update UnitTests1.md with the correct way to detect a broken exec.
* Improve the initial documentation so it starts by talking about CI

## Further reading

https://docs.openshift.com/container-platform/3.7/dev_guide/dev_tutorials/openshift_pipeline.html#the-pipeline-build-config

https://ukcloud.com/news-resources/news/blog/part-openshift-deploying-openshift-openshift-pipelines
   
https://www.safaribooksonline.com/library/view/devops-with-openshift/9781491975954/ch04.html
  * Perhaps out of date, but contains lots of useful `oc` commands. 
  * Suggests using multiple projects to separate "dev" and "prod" 
    deployments of your code.
  * use `openshiftBuild(namespace: 'other_project_name', ...)` to run a build
    in a different project.
   
https://blog.openshift.com/openshift-3-3-pipelines-deep-dive/

https://jenkins.io/doc/book/pipeline/jenkinsfile/

https://github.com/toschneck/openshift-example-bakery-ci-pipeline

To exec a process on a container: 
https://github.com/openshift/jenkins-plugin#run-openshift-exec

https://docs.openshift.org/latest/install_config/configuring_pipeline_execution.html
Most of the documentation for Jenkins Pipeline jobs is here, 
according to
[this trello](https://trello.com/c/rBojNLGj/1121-5-better-devguide-pipeline-docs-techdebt)

N.B. The above is a **scripted** pipeline