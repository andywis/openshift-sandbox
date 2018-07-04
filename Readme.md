# Setting up the Project and Application
We'll start by creating a really simple web application in Python

1. Log in to the OpenShift Container Platform (OCP) CLI:
`oc login https://ocp.blah.blah.blah.com:8443`

1. Create a new OCP Project.
   - List the existing projects with `oc projects`  
   - Create a new one called "andy-test1" with  `oc new-project andy-test1`
   - alternatively, create it in the Web UI by clicking the "New Project"
     button.

1. Create a new source code repository; it must be in a location that can be
   seen by OpenShift (e.g. on github)

1. Create the code for the new application
   - we'll start with something really simple, and build it up.
   - Copy the code from 
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

1. Now we have a very simple web application (called **openshift-sandbox** if 
   you used my demo), we can develop it to add pipelines.
   
-------

# Setting up the Pipeline

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

1. Create the pipeline by running "oc create" with the above file:
    ```bash
    oc create -f pipeline_file.yaml
    ```
    The "thing" created by oc create is completely described by the 
    file (in this case, the "thing" is a Pipeline, which is a BuildConfig)


## Things to notice:
   -  When we created the app earlier, the "oc new-app" command created a
      BuildConfig with the default "strategy", which is the 
      **sourceStrategy**. This pulls your code from source control, builds
      and immediately deploys it. A Pipeline is a different sort of
      Build Config that uses a 
      **jenkinsPipelineStrategy** instead
   -  If you want to place the Jenkinsfile in a separate file, rather than
      embedding it in the Yaml, you should use the **jenkinsfilePath**
      directive instead, e.g.
   
        ```yaml
        spec:
          strategy:
            jenkinsPipelineStrategy:
              jenkinsfilePath: some/path/to/your/jenkins/filename
        ```

  -  In the Jenkinsfile, "node" takes no arguments. If we specify an argument, 
     e.g. `node('maven') { ... }` the Jenkins job will create a slave node 
     based on the "Maven" node image. 
     ([more here](https://blog.openshift.com/openshift-3-3-pipelines-deep-dive/))
     Four slave node images are available: maven and nodejs, both in rhel7 and
     CentOS flavours. They all contain `oc` and `git` tooling.
     
     
  -  If the slave doesn't exist, you may see a message in the console log saying
     "Jenkins doesn’t have label maven" Jenkins will then create a slave node
     matching that label. It may take a while to start up.
   
   
# More questions
* How to run tests on the image?

another example...
```yaml
    jenkinsPipelineStrategy:
      jenkinsfile: |-
          node('maven') {
            stage('build') {
              openshiftBuild(buildConfig: 'openshift-sandbox', showBuildLogs: 'true')
            }
            /*stage('deploy') {
              openshiftDeploy(deploymentConfig: 'frontend')
            }*/
          }
```

# Further reading

https://docs.openshift.com/container-platform/3.7/dev_guide/dev_tutorials/openshift_pipeline.html#the-pipeline-build-config

https://ukcloud.com/news-resources/news/blog/part-openshift-deploying-openshift-openshift-pipelines
   
https://www.safaribooksonline.com/library/view/devops-with-openshift/9781491975954/ch04.html
   
https://blog.openshift.com/openshift-3-3-pipelines-deep-dive/
