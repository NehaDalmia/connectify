from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src.json_validator import expects_json
import config
import os

app = Flask(__name__)
app.config.from_object(config.DevConfig)

db = SQLAlchemy(app)
from db_models import *

from src.models import DataManager

data_manager = DataManager()

from src import views

with app.app_context():
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected \033[0m")
        db.drop_all()
        print("\033[94mAll tables dropped.\033[0m")
    
    print("\033[94mCreating all tables...\033[0m")
    db.create_all()
    print("\033[94mAll tables created.\033[0m")
    # db.session.add(BrokerDB(name = 'broker-1'))
    # db.session.add(BrokerDB(name = 'broker-2'))
    # db.session.add(BrokerDB(name = 'broker-3'))
    # db.session.commit()
    # print("\033[94mBrokers Added.\033[0m")
    print("\033[94mInitializing master queue from database...\033[0m")
    data_manager.init_from_db()
    print("\033[94mMaster queue initialized from database.\033[0m")

    # print the master queue for debugging purposes
    if app.config["FLASK_ENV"] == "development":
        print("Brokers in manager:")
        print(data_manager._brokers)