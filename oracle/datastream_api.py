from oracle.serverside import *
from flask import jsonify, Flask, request
from oracle import oracle_errors
from satorilib.concepts.structs import Stream, StreamId
from oracle.datastream_for_api import Data_Stream
import secrets
import threading, time
from satorineuron import relay
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set the lowest level to log (DEBUG is the most detailed)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler()  # Log to the console
    ]
)

logging.debug("This is a DEBUG message")
logging.info("This is an INFO message")
logging.warning("This is a WARNING message")
logging.error("This is an ERROR message")
logging.critical("This is a critical message")

DEBUG = 1

def new_datastream(stream: Stream, port: int):
    print(f"started datastream {stream=}")
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

    ds = Data_Stream(stream, port)
    print(f"new datastream {ds=}")

    @app.route("/json")   
    def json():
        return ds.topic()

    @app.route("/topic")
    def topic():
        return ds.topic()

    @app.route("/get_current_data", methods=["GET"])
    def get_data():
        data = ds.get_data()
        return jsonify(data)

    @app.route("/rec_pred", methods=["POST"])
    def record_prediction():
        data = request.json
        wallet_address = data["wallet"]
        prediction = data["prediction"]


        try:
            if ds.record_prediction(wallet_address, prediction):
                return "Success", 200
            else:
                return "Error", 500

        except Exception as e:
            logging.critical(f"{type(e)}, {str(e)}")
            return "Error", 500

    @app.route("/submit_data/<data>", methods=["POST"])
    def record_submitted_data(data):
        try:
            #data = request.json()
            #logging.critical(f"{data=}")
            submitted = ds.record_submitted_data(data)
            logging.critical(f"{submitted}")
            if submitted:
                logging.critical(f"{submitted} {data}")
                return str(submitted), 200
            else:
                logging.critical(f"{submitted} {data}")
                return "Error", 500
        except Exception as e:
            logging.critical(f"{type(e)}, {str(e)}")
            return "Error", 500

    @app.route("/latest_data", methods=["GET"])  
    def latest():
        return ds.latest()

    @app.route("/buildBlock", methods=["GET"])    
    def buildBlock():
        try:
            block = ds.buildBlock()
            return jsonify(block), 200
        except:
            return "Error", 500
        
    app.run(host="127.0.0.1", port=port)

    while True:
        threading.Thread(target=relay.RawStreamRelayEngine.call, args=[ds.stream]).start()
        
        time.sleep(60)
    