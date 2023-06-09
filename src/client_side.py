from flask import Blueprint, request, jsonify

import globals
from globals import storage
from clocks import *
from broadcast import broadcast
import time

client_side = Blueprint("client_side", import_name=__name__, url_prefix="/shard/data")

@client_side.before_request
def check_request():
    """Check that the json data is correct, and get the request clock info"""
    json = request.get_json()
    #ensure there is json data
    if json is None:
        return jsonify({"error": "bad request"}), 400
    #get the causal-metadata and update our clocks
    clocks = json.get('causal-metadata')
    if clocks:
        globals.update_known_clocks(clocks)
    
    #Ensure PUT requests have a value to save that isn't too large
    if request.method == "PUT":
        val = json.get('val')
        if val is None:
            return jsonify({"error": "bad request"}), 400

@client_side.route('/<key>', methods=['GET'])
# TODO: this function will have to determine which nodes contain the data and make appropriate requests
def get_data(key):
    """Get the value from local data, unless our info is after the request metadata"""
    json = request.get_json()
    clocks = json.get('causal-metadata', {})
    data = storage.get(key)
    #if the key doesn't exist locally, or in request metadata it doesn't exist in causal history
    if clocks.get(key) is None and data is None:
        return jsonify({"causal-metadata":globals.known_clocks}), 404

    #while our local clock is behind the request clock, read from other replicas until we get the updated value
    needs_persistence = False
    while compare_clocks(storage.data_clocks.get(key), clocks.get(key, [0])) <= 0:
        responses = broadcast(f"replication/{key}", "GET", {}, globals.view)
        for resp in responses:
            resp_json = resp.get_json()
            if compare_clocks(storage.data_clocks.get(key, [0]), resp_json.get('clock')) > 0:
                needs_persistence = True
                storage.put(key, resp_json.get('data'), resp_json.get('clock'),resp_json.get('last_writer'), persist=False)
    # Perist the last updated value
    if needs_persistence:
        storage._persist_data(key)

    #Now we know the local data/clock is at least up to date or in the future of the request clock
    return jsonify({"causal-metadata":globals.known_clocks, "val":storage.data.get(key)})

@client_side.route('/<key>', methods=['PUT'])
def put_data(key):
    # Cache causal metadata
    local_clock, *_ = storage.cache_causal_metadata(key)
    json = request.get_json()
    if local_clock == None:
        status_code = 201
        local_clock = new_clock(1)
    else: status_code = 200
    increment(local_clock, globals.id)
    globals.update_known_clocks({key: local_clock})
    data = {
            "clock":local_clock, 
            "id": globals.id, 
            "val": json.get('val')
            }
    broadcast(f"replication/{key}", "PUT", data, globals.view) 
    return jsonify({"causal-metadata":globals.known_clocks}), status_code

@client_side.route("/<key>", methods=['DELETE'])
def delete_data(key):
    if key not in globals.data.keys():
        return jsonify({"causal-metadata":globals.known_clocks}), 404
    increment(globals.data_clocks[key], globals.id)
    data = {
            "clock":globals.data_clocks.get(key, [0]), 
            "id": globals.id, 
            }
    broadcast(f"replication/{key}", "DELETE", data, globals.view) 
    return jsonify({"causal-metadata":globals.known_clocks}), 200

@client_side.route('/kvs', methods=['GET'])
def all_keys():
    return {"causal-metadata":globals.known_clocks, "count":len(storage.data), "keys": storage.data.keys()}, 200
