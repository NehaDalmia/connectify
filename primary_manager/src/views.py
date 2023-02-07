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

@app.route(rule="/topics", methods=["POST"])
def topics():
    return "POST on /topics"

@app.route(rule="/producer/register", methods=["POST"])
def produce():
    return "POST on /producer/register"

@app.route(rule="/consumer/register", methods=["POST"])
def consume():
    return "POST on /consumer/register"

@app.route(rule="/producer/produce", methods=["POST"])
def size():
    return "POST on /producer/produce"

