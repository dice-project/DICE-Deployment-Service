#!/bin/bash

set -e

port=$(ctx node properties port)

ctx logger info 'Creating the startup script'
echo "#!/bin/bash

cd /home/ubuntu
. venv/bin/activate
cd dice_deploy_django

bash up.sh $port
" > /home/ubuntu/start.sh

chmod u+x /home/ubuntu/start.sh
ctx logger info 'Done'
