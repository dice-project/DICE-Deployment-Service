# Setting up continuous tests

Here are the instructions and notes on how to set up the Continuous Integration
and Continuous Deployment process for the DICE deployment service. The goal
of this exercise is to have a process for validating the changes and updates
to the DICE deployment service source code.

At the time of writing, we use Jeknis ver. 2.7 as the CI tool. Other
requirements include:

* Packages `gcc python-virtualenv python-dev`


## Unit tests

First, we set up a Jenkins job for unit tests. Let's name it
`Deployment-Service-01-unit-tests`. 

* Source Code Management: Git. Select `*/develop` as the branch.
* Build triggers: Poll SCM. E.g. every 10 minutes: `H/10 * * * *`
* Build: I like putting this in two parts. The first part sets up the virtual
  environment and updates any requirements. The second part runs the actual
  unit tests.

Execute shell:

```bash
PATH="$WORKSPACE/../venv/bin":/usr/local/bin:$PATH

if [ ! -d "../venv" ]
then
  virtualenv ../venv
fi

. "$WORKSPACE/../venv/bin/activate"

cd dice_deploy_django
pip install -U -r requirements.txt
```

Execute shell:

```bash
. "$WORKSPACE/../venv/bin/activate"

cd dice_deploy_django
echo "******* Running unit tests"
python manage.py test
```


## Integration tests

The integration tests require a wider context to be able to run. They need:

* A platform to run the deployment into. Supported platforms: `openstack`,
  `fco`.
* A Cloudify Manager version 3.4.

First, use the shell on the Jenkins to set up the virtual environment for the
Cloudify CLI, and provide the inputs.

```bash
$ sudo su jenkins
$ cd ~/jobs/Deployment-Service-01-unit-tests
$ virtualenv cfy-34
$ . cfy-34/bin/activate
$ pip install cloudify==3.4.0
```

Then provide the context information as a set of environment properties. Use
the Jenkins' Environment variables in the Global properties section of
`/jenkins/configure`. Note that all of the variables start with prefix `TEST_`
that should make it clear what process they control.

| Name                      | Example     | Description                       |
|---------------------------|-------------|-----------------------------------|
| TEST_AGENT_USER           | ubuntu      | SSH user for plain host           |
| TEST_CFY_MANAGER          | 10.10.43.48 | Address of manager                |
| TEST_CFY_MANAGER_USERNAME | admin       | Username for manager              |
| TEST_CFY_MANAGER_PASSWORD | 2Big1Secret | Password for manager              |
| TEST_SUPERUSER_USERNAME   | ds-user     | Admin user for deployment service |
| TEST_SUPERUSER_PASSWORD   | ds-pass     | Admin pass for deployment service |
| TEST_SUPERUSER_EMAIL      | t@x.com     | Admin email address               |

Variables in the table above are required regardless of the platform being
used. Each supported platform has some additional required variables that need
to be set. Consult tables below for more information.

| OpenStack var         | Example    | Description         |
|-----------------------|------------|---------------------|
| TEST_MEDIUM_IMAGE_ID  | ca123...0a | OpenStack image ID  |
| TEST_MEDIUM_FLAVOR_ID | d3046...fa | OpenStack flavor ID |

| FCO var                 | Example                         | Description     |
|-------------------------|---------------------------------|-----------------|
| TEST_SERVICE_URL        | https://cp.project.flexiant.net | API endpoint    |
| TEST_USERNAME           | fb3c9...12                      | FCO username ID |
| TEST_PASSWORD           | MyS3cr37Pa55                    | FCO password    |
| TEST_CUSTOMER           | ae568...cc                      | FCO customer ID |
| TEST_MEDIUM_IMAGE_ID    | 12345...bb                      | image uuid      |
| TEST_MEDIUM_SERVER_TYPE | 2 GB / 1 CPU                    | server type     |
| TEST_MEDIUM_DISK        | 30Gb Storage                    | disk type       |
| TEST_VDC                | abcde...98                      | VDC uuid        |
| TEST_NETWORK            | 1a2b3...9f                      | network uuid    |
| TEST_AGENT_KEY          | ab12c...f9                      | agent key uuid  |

There is one more variable that can be used to control test execution. Set
`TEST_WAIT_TIME` variable to time in minutes. This is used to terminate test
that run for too long. For example, setting this to 10 means that each test in
test suite can run for no more that 10 minutes. Default value used by test
harness is set to 30 minutes, which should be plenty for most of the cases.

Then create a Cloudify job, e.g., `Deployment-Service-02-integration-tests`. 
Click on **Advanced ...** and check **Use custom workspace**. In the Directory,
provide the path to the Unit tests workspace set up earlier:

    $HOME/jobs/Deployment-Service-01-unit-tests/workspace

Leave the **Display Name** field blank.

To the **Build** section add an **Execute shell** build step:

    PATH="$WORKSPACE/../cfy-34/bin":/usr/local/bin:$PATH
    . "$WORKSPACE/../cfy-34/bin/activate"
    if [ ! -e ".cloudify" ]
    then
      cfy init
    fi
    cd tests
    ./run-integration-tests.sh platform  # or fco

The job is now ready to run. As the last step, go back to the
`Deployment-Service-01-unit-tests`, go to the **Post-build Actions** section
and add **Build other projects**, specifying 
`Deployment-Service-02-integration-tests` project to build.


# Running integration tests against vagrant instance

Developers might find it beneficial to run integration tests against local
deployment service. To do this, a few steps need to be taken care of.

First, make sure deployment service settings have properly configured cloudify
manager endpoint (settings that need to be checked are `CFY_MANAGER_URL`,
`CFY_MANAGER_USERNAME` and `CFY_MANAGER_PASSWORD`). Second, export following
variables (change contents to fit your development environment, defaults
listed below should work for default vagrant setup):

    export TEST_DEPLOYMENT_SERVICE_ADDRESS="http://localhost:8080"
    export TEST_SUPERUSER_USERNAME=admin
    export TEST_SUPERUSER_PASSWORD=changeme

Now simply run `python -m unittest discover`.


# Running bootstrap and teardown tests from local machine

This is also quite simple to do. Simply export all variables that are
described in section about setting up integration tests. For convenience, two
shell scripts that can be edited and then sourced are provided:
`set-env-vars-PLATFORM.sh` will set required variables and `unset-env-vars.sh`
will clean them up.

After variables are properly set up, run `./run-integration-tests.sh platform`
script.  The script should start bootstraping the deployment service and
execute tests after bootstrap is done.
