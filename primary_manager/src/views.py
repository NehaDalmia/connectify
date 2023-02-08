from flask import make_response, request, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError

from src import app, expects_json, data_manager
import requests

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

@app.route(rule="/topics", methods=["GET", "POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"name": {"type": "string"},"number_of_partitions":{"type":"number"}},
        "required": ["name"],
    },
    ignore_for=["GET"],
)
def topics():
    """Return all the topics or add a topic."""

    # If method is POST add a topic
    if request.method == "POST":
        topic_name = request.get_json()["name"]
        try:
            broker_hosts = []
            # add default none arg to data manager funcs
            if "number_of_partitions" in request.get_json():
                broker_hosts = data_manager.check_and_get_chosen_brokers(topic_name,request.get_json()["number_of_partitions"])
            else : 
                broker_hosts = data_manager.check_and_get_chosen_brokers(topic_name)
            for broker_host in broker_hosts: # can async this
                response = requests.post("http://"+broker_host+":5000/topics",json = {"name":topic_name})
            if "number_of_partitions" in request.get_json():
                data_manager.add_topic(topic_name,broker_hosts,request.get_json()["number_of_partitions"])
            else : 
                data_manager.add_topic(topic_name,broker_hosts)
            
            
            return make_response(
                jsonify(
                    {
                        "status": "success",
                        "message": f"Topic '{topic_name}' created successfully.",
                    }
                ),
                200,
            )
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )

@app.route(rule="/producer/register", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"topic": {"type": "string"}},
        "required": ["topic"],
    }
)
def register_producer():
    """Register a producer for a topic."""
    topic_name = request.get_json()["topic"]
    try:
        producer_id,partition_count = data_manager.add_producer(topic_name)
        return make_response(
            jsonify({"status": "success", "producer_id": producer_id, "partition_count":partition_count}),
            200,
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
@app.route(rule="/consumer/register", methods=["POST"])
def consume():
    return "POST on /consumer/register"

@app.route(rule="/producer/produce", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "producer_id": {"type": "string"},
            "message": {"type": "string"},
            "partition_number": {"type":"number"},
        },
        "required": ["topic", "producer_id", "message"],
    }
)
def produce():
    """Add a log to a topic."""
    topic_name = request.get_json()["topic"]
    producer_id = request.get_json()["producer_id"]
    message = request.get_json()["message"]
    try:
        partition_number = None
        if "partition_number" in request.get_json():
            partition_number = request.get_json()["partition_number"]
        
        broker_host = data_manager.get_broker_host(topic_name, producer_id, partition_number)
        response =  requests.post("http://"+broker_host+":5000/producer/produce",json = {"topic":topic_name, "producer_id":producer_id,"message":message})
        return make_response(
            jsonify({"status": "success"}),
            200,
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )

