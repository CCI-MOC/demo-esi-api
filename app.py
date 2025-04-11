from esi_api.connections import get_openstack_connection, get_esi_connection
from esi.lib import nodes
from flask import Flask, jsonify
from threading import Event
import json
import signal
import os
import sys
import traceback


app = Flask(__name__)

INTERRUPT_EVENT = Event()

cloud_name = os.environ.get('CLOUD_NAME') or "openstack"


@app.route('/api/v1/nodes/list', methods=['GET'])
def nodes_list():
    try:
        conn = get_esi_connection(cloud=cloud_name)
        node_networks = nodes.network_list(conn)
        items = []
        for node_network in node_networks:
            node = node_network['node']
            network_info_list = []
            lease_info_list = []

            for node_port in node_network['network_info']:
                if node_port["networks"]:
                    network = node_port['networks'].get('parent')
                    network_name = network.name if network else None
                    network_uuid = network.id if network else None
                # TODO: decide what is the necessary attributes of network_ports
                stripped_network_info = {
                    'baremetal_port': {
                        'mac_address': node_port["baremetal_port"].address,
                        'baremetal_port_uuid': node_port["baremetal_port"].id,
                    },
                    'network_ports': node_port["network_ports"],
                    'network': {
                        'name': network_name,
                        'network_uuid': network_uuid,
                    }
                }
                network_info_list.append(stripped_network_info)

            leases = conn.lease.leases(resource_uuid=node.id)
            for lease in leases:
                lease_info_list.append({
                    'lease_uuid': lease.id,
                    'start_time': lease.start_time,
                    'end_time': lease.end_time
                })
            items.append({'node': node.to_dict(),
                'lease_info': lease_info_list,
                'network_info': network_info_list
                })
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/v1/baremetal-request/fulfill', methods=['POST'])
def baremetal_order_request_fulfill():
    response = {
        'status': 'CREATED'
        , 'code': 201
    }
    return jsonify(response)

@app.route('/api/v1/networks/list', methods=['GET'])
def networks_list():
    try:
        conn = get_openstack_connection(cloud=cloud_name)
        response = conn.network.networks()
        networks = [r.to_dict() for r in response]
        return jsonify(networks)
    except Exception as e:
        return jsonify({"error": str(e)})

def start():
    flask_port = os.environ.get('FLASK_PORT') or 8081
    flask_port = int(flask_port)

    app.run(port=flask_port, host='0.0.0.0')

if __name__ == "__main__":
    start()
