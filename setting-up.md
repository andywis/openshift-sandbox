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
     into your new repository (the files you'll need are config.py,
     requirements.txt, wsgi.py and .s2i/environment)

1. Create a new App within this project.