# Setting up
We'll start by creating a really simple web application in Python

1. Log in to the OpenShift Container Platform (OCP) CLI:
`oc login https://ocp.blah.blah.blah.com:8443`

1. Create a new OCP Project.
   - List the existing projects with `oc projects`  
   - Create a new one called "andy-test1" with  `oc new-project andy-test1`
   - alternatively, click the "New Project" button in the Web UI

1. Create a new Repository; it must be in a location that can be seen by
   OpenShift (e.g. on github)

1. Create the code for the new application
   - we'll start with something really simple, and build it up.
   - Copy the code from 
     [OpenShiftDemos on Github](https://github.com/OpenShiftDemos/os-sample-python)
     into your new repository. Tthe files you'll need are config.py,
     requirements.txt, wsgi.py and .s2i/environment

1. Create a new App within this project:
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

1. Now we have a very simple web application, we can develop it to add
   pipelines.