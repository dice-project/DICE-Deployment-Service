import sys
import os

from cloudify_cli import utils

deployment_id = sys.argv[1]

management_ip = utils.get_management_server_ip()
client = utils.get_rest_client(management_ip)

dep = client.deployments.get(deployment_id, _include=['outputs'])
response = client.deployments.outputs.get(deployment_id)
outputs = response.outputs

print("""
	export DDS_DNS_SERVER={0}
	export DDS_HTTP_ENDPOINT={1}
""".format(outputs["dns_server"], outputs["http_endpoint"]))

