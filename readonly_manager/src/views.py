from flask import make_response, request, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError

from src import app, ro_manager, requests, expects_json


@app.errorhandler(400)
def bad_request(error):
    """Bad request handler for ill formated JSONs"""
    if isinstance(error.description, ValidationError):
        return make_response(
            jsonify(
                {"status": "failure", "message": error.description.message}
            ),
            400,
        )
    # handle other bad request errors
    return error

@app.route(rule="/topics", methods=["GET"])
def topics():
    """Return all the topics or add a topic."""
    try:
        topics = ro_manager.get_topics()
        return make_response(
            jsonify({"status": "success", "topics": topics}), 200
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )

@app.route(rule="/consumer/consume", methods=["GET"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "partition_number": {"type": "number"},
            "consumer_id": {"type": "string"},
        },
        "required": ["topic", "consumer_id"],
    }
)
def consume():
    """Sanity check and assign consume request to a broker"""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_number: int = None
    read_from_given_partition = False

    try:
        partition_number = int(request.get_json()["partition_number"])
        try:
            ro_manager.is_request_valid(topic_name, consumer_id, partition_number)
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )
        read_from_given_partition = True
    except Exception as e:
        try:
            ro_manager.is_request_valid(topic_name, consumer_id)
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )
        partition_number = ro_manager.find_best_partition(topic_name, consumer_id)

    try:
        num_tries = 0
        response = None
        num_partitions = ro_manager.get_partition_count(topic_name)
        # Try all brokers once, and infer no logs to read only if all brokers say so
        while num_tries < num_partitions:
            broker_host = ro_manager.get_broker_host(topic_name, partition_number)
            # Add partition_number to the request data
            json_data = request.get_json()
            json_data["partition_number"] = partition_number
            # Forward this request to a broker, wait for a response
            response = requests.get(
                url = "http://"+broker_host+":5000/consumer/consume",
                json = json_data
            )
            # Check response received from broker, if success, then exit loop
            if(response.json()["status"] == "success"):
                break
            num_tries += 1
            partition_number = (partition_number + 1) % num_partitions
            # If consumer wanted to read from given partition only, then exit loop
            if read_from_given_partition == True and num_tries == 1:
                break
        # Reply to consumer
        return make_response(
            jsonify({"status": response.json()["status"], "message": response.json()["message"]}), 200
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )

@app.route(rule="/size", methods=["GET"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "consumer_id": {"type": "string"},
            "partition_number": {"type": "number"}
        },
        "required": ["topic", "consumer_id", "partition_number"]
    }
)
def size():
    """Sanity check and assign size request to a broker."""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_number = int(request.get_json()["partition_number"])
    # ADDDDDDDDD SANITY CHECK
    try:
        broker_host = ro_manager.get_broker_host(topic_name, partition_number)
        # Forward this request to a broker, wait for a response
        response = requests.get(
            url = "http://"+broker_host+":5000/size",
            json = request.get_json()
        )
        # Reply to consumer
        return make_response(
            jsonify({"status": response.json()["status"], "size": response.json()["size"]}), 200
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )