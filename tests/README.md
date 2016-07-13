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
* A Cloudify Manager version 3.4 (for OpenStack) or 3.3.1 or newer (for FCO).

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
either the Jenkins' Environment variables in the Global properties section of
`/jenkins/configure`. 

  Name                | Example value
  ----                | -------------
  `TARGET_PLATFORM`   | `openstack`  
  `CLOUDIFY_ADDRESS`  | `10.10.43.48`
  `CLOUDIFY_USERNAME` | `admin`      
  `CLOUDIFY_PASSWORD` | `2Big1Secret`


Prepare the inputs that will be valid for your environment. Make sure to
name the inputs file as `inputs-$TARGET_PLATFORM.yaml`. Put it into
`$HOME/jobs/Deployment-Service-01-unit-tests/`.

Then create a Cloudify job, e.g., `Deployment-Service-02-integration-tests`. 
Click on **Advanced ...** and check **Use custom workspace**. In the Directory,
provide the path to the Unit tests workspace set up earlier:

`$HOME/jobs/Deployment-Service-01-unit-tests/workspace`

Leave the **Display Name** field blank.

To the **Build** section add an **Execute shell** build step:

```bash
cp ../inputs-$TARGET_PLATFORM.yaml .

PATH="$WORKSPACE/../cfy-34/bin":/usr/local/bin:$PATH

. "$WORKSPACE/../cfy-34/bin/activate"

if [ ! -e ".cloudify" ]
then
  cfy init
fi

cfy use -t $CLOUDIFY_ADDRESS

cd tests
python -m unittest test_integration.BootstrapTests.test_bootstrap
```

The job is now ready to run. As the last step, go back to the
`Deployment-Service-01-unit-tests`, go to the **Post-build Actions** section
and add **Build other projects**, specifying 
`Deployment-Service-02-integration-tests` project to build.
