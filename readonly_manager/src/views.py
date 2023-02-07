from flask import make_response, request, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError

from src import app, expects_json


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
    return "GET on /topics"

@app.route(rule="/producer/produce", methods=["GET"])
def produce():
    return "GET on /producer/produce"

@app.route(rule="/consumer/consume", methods=["GET"])
def consume():
    return "GET on /consumer/consume"

@app.route(rule="/size", methods=["GET"])
def size():
    return "GET on /size"