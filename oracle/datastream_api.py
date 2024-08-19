from oracle.serverside import *
from flask import jsonify, Flask, request
from oracle import oracle_errors
from satorilib.concepts.structs import Stream, StreamId
from oracle.datastream_for_api import Data_Stream
import secrets
import threading, time

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


    # def get_data():
    #     if local:
    #         try:
    #             data = Stream.call(self.stream)
    #             print(f"{data=}")
    #         except:
    #             raise oracle_errors.NotMessage(f"No data in stream {self.stream_name}")
    #     #this needs to fileter to just the value
    #         self.latest_data[0] = data.json()
    #         self.changed_data[0] = True
    #     record_data = ""
    #     for index in range(self.changed_data):
    #         if self.changed_data[index]:
    #             self.changed_data[index] = False
    #             record_data += str(self.latest_data[index])
    #         record_data += "|"
    #     self.last_recorded = int(time.time())
    #     # Record it for minutes after the hour
    #     self.data[(self.last_recorded%3600)//60] = record_data
    #     return True

    @app.route("/rec_pred", methods=["POST"])
    def record_prediction():
        data = request.json()
        wallet_address = data["wallet"]
        prediction = data["prediction"]


        try:
            if ds.record_prediction(wallet_address, prediction):
                return "Success", 200
            else:
                return "Error", 500

        except:
            return "Error", 500

    @app.route("/submit_data", methods=["POST"])
    def record_submitted_data():
        try:
            data = request.json()
            if ds.record_submitted_data(data):
                return "Success", 200
            else:
                return "Error", 500
        except:
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
        threading.Thread(target=ds.get_data, args=[]).start()
        time.sleep(60)
    