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
    partition_number = request.get_json()["partition_number"]

    try:
        broker_host = ro_manager.assign_consume_request(topic_name, consumer_id, partition_number)
        # Forward this request to a broker, wait for a response
        response = requests.post(
            url = "http://"+broker_host+":5000/consumer/consume",
            json = request.get_json()
        )
        # Reply to consumer
        return response
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
        },
        "required": ["topic", "consumer_id"],
    }
)
def size():
    """Sanity check and assign size request to a broker."""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    try:
        broker_host = ro_manager.assign_size_request(topic_name, consumer_id)
        # Forward this request to a broker, wait for a response
        response = requests.post(
            url = "http://"+broker_host+":5000/size",
            json = request.get_json()
        )
        # Reply to consumer
        return response
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )