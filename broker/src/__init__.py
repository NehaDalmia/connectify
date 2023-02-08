from flask import Flask

from src.json_validator import expects_json
from flask_sqlalchemy import SQLAlchemy
import config
import os

app = Flask(__name__)
app.config.from_object(config.ProdConfig)
db = SQLAlchemy(app)


with app.app_context():
    db.drop_all()

from src import views