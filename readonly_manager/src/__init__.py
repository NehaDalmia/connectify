from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src.json_validator import expects_json
from readonly_manager.src.models import readonly_manager
import config
import os
import requests

app = Flask(__name__)
app.config.from_object(config.ProdConfig)
db = SQLAlchemy(app)
from db_models import *

from src.models import ReadonlyManager

ro_manager = ReadonlyManager()


from src import views

with app.app_context():
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected. Dropping all tables...\033[0m")
        db.drop_all()
        print("\033[94mAll tables dropped.\033[0m")
    
    print("\033[94mCreating all tables...\033[0m")
    db.create_all()
    print("\033[94mAll tables created.\033[0m")

    print("\033[94mInitializing readonly manager from database...\033[0m")
    ro_manager.init_from_db()
    print("\033[94mReadonly manager initialized from database.\033[0m")

    # print the master queue for debugging purposes
    if app.config["FLASK_ENV"] == "development":
        pass