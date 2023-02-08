from flask import Flask

from src.json_validator import expects_json
import config
import os

app = Flask(__name__)
app.config.from_object(config.ProdConfig)

from src import views