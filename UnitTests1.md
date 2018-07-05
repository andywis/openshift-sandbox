# Running unit tests in a Pipeline

This article describes the first option for running unit tests,
i.e. running them via the Openshift equivalent of `docker exec`
in the application container itself.

## Basics

Let's start with the skeleton of the Jenkinsfile; this does nothing more
than build the app.

```yaml
node {
  def APPNAME = "demo-app"
  
  stage('build') {
     openshiftBuild(buildConfig: APPNAME, showBuildLogs: 'true')
  }
  
  stage('test') {
    echo "we need to add some Groovy here"
  }
  
  stage('promote') {
    echo "we need to add some Groovy here"
  }
}
```

**Note** that `node` takes no parameter here, on the first line. A parameter
would be used to specify the type of Jenkins node to run on. At this point, 
we just want things to run on the Jenkins-Master.

The 2nd and 3rd stages do nothing at the moment. We'll add code to these later.

## Running a command in the container
In the `stage('test') {}` stage, we would like to exec a command, which we
will do with the **openshiftExec** command.

**openshiftExec** takes a pod name and an array of shell
commands as its arguments.

The following code works out the name of the pod and calls **openshiftExec**.
For the purposes of the demo, we will "curl" the homepage of our app (which
is not strictly a unit test, but demonstrates the Jenkinsfile syntax)

Here's the definition for this stage. See notes below.

```yaml

  stage('tests') {
    openshift.withCluster() {
      openshift.withProject() {
      
          /* Get the Deployment Config Object */
          def dcObj = openshift.selector('dc', APPNAME).object()
          def podSelector = openshift.selector('pod', [deployment: "${APPNAME}-${dcObj.status.latestVersion}"])
          
          podSelector.withEach {
              // obtain the pod name and remove "pods/" from the front.
              def podName = it.name()  // probabbly pods/abcd1234
              podName = podName.replaceFirst("pods/", "")
              echo "Running unit tests against ${podName}"

              // Run a command on the container
              def resp = openshiftExec(pod: podName, command: ["/usr/bin/curl", "http://127.0.0.1:8080/"])
              
              // TODO: interrogate these outputs and work out how to
              // abort or continue.
              echo resp.error
              echo resp.failure
              println('Stdout: '+resp.stdout.trim())
              println('Stderr: '+resp.stderr.trim())
          }
      }
    }
  }
```
**Notes**
* withCluster and withProject allow you to specify which cluster and which
  project.
* You can print out all the details of the podSelector object with 
  `podSelector.describe()`
* The project name is available via `openshift.project()`
* We have to iterate over the podSelector object with `withEach`. Within the
  loop, the current item is `it`
* The pod name appears as "pods/abcd1234", but we need to remove the first 5
  letters from the front. This is done using Groovy's `String.replaceFirst()`
* The `command` parameter to `openshiftExec` must be an array. The short form
  described in 
  [the documentation](https://github.com/openshift/jenkins-plugin#run-openshift-exec)
  (i.e. `command: "curl http://127.0.0.1:8080"`)
  does not work because it does not perform shell interpolation. As in most
  other languages, you should use `command: [cmd, arg1, arg2, arg3]`


