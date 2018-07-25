# Promoting a build to a higher environment

So far, we've looked at:
- [setting up a pipeline](Readme.md), 
- [executing code within the running container](Part02_UnitTests1.md) and
- [running unit tests on a Jenkins node](Part03_JenkinsSlave.md)

Now we can look at the next step of Continuous integration: Promoting the 
app to the next environment.

Let's imagine we have designed a set of CI environments as follows:
```text
             devel   ->   integ   ->   preprod   ->   production
```
In this article, we will concentrate on the first 2 environments, but the same
idea applies for promoting the image to the higher environments.

# How to represent environments in OpenShift
Each environment is represented as a project within Openshift.

Let's set up a pair of projects we can use to the experiment with...

`oc login https://ocp.blah.blah.blah.com:8443`

`oc new-project demo-devel`

`oc new-project demo-integ`

Now switch to the "demo-devel project" and build the demo Python app based 
on the code in this repo (from Part 1)... 

```oc project demo-devel```

```oc new-app https://github.com/andywis/openshift-sandbox.git```

and build a pipeline (also as Part 1, using the file
[part_01_pipeline_build_config.yaml](part_01_pipeline_build_config.yaml)).

```oc create -f part_01_pipeline_build_config.yaml```

This should kick off a build of a "jenkins-ephemeral" app, and prepare us for
testing the app promotion. At the moment, the pipeline only performs a build.

In the next section, we'll extend the pipeline to promote the build from
"demo-devel" to "demo-integ".

# Promote the build
The first step is to tag the successful build.

```text
node {
  def APPNAME = "openshift-sandbox"
  stage('build') {
    openshiftBuild(buildConfig: 'openshift-sandbox', showBuildLogs: 'true')
  }
  stage('test') {
    sh('''do_tests.sh''')
  }
  stage('promote') {
    openshift.withCluster() {
      openshift.withProject() {
        openshift.tag("${APPNAME}:latest", "${APPNAME}-staging:latest") 
      }
    }
  }
}
```
In the above Jenkinsfile, we add a Docker tag to the image after it has been
successfully built. Note this is a tagged image in the "demo-devel" project, 
but it could then be detected by a  task in "demo-integ".

If we want to add the image to the "demo-integ" namespace, we need to
allow the service accounts for Jenkins in each project to see eachother, 
as described 
[here](https://docs.openshift.com/container-platform/3.9/using_images/other_images/jenkins.html#jenkins-cross-project-access).

Then the pipeline can be modifed to look like this:
```text
node {
  ...
  stage('promote') {
    openshift.withCluster() {
      openshift.withProject() {
        openshift.tag("${APPNAME}:latest", "demo-integ/${APPNAME}-staging:latest") 
      }
     }
  }
}
```


