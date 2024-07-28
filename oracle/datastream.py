from serverside import *
from flask import jsonify
import json
import squawker_errors
import requests, time


class Data_Stream():
    def __init__(self, file_path: str=None, stream_name: str=None, api_key: str=None, api_url: str=None, api_header: str=None):
        try:
            with open(file_path) as f:
                raw_data = json.load(f)
                self.stream_name = raw_data["stream_name"]
                self.api_key = raw_data["api_key"]
                self.api_url = raw_data["api_url"]
                self.api_header = raw_data["api_header"]
        except:
            self.stream_name = stream_name
            self.api_key = api_key
            self.api_url = api_url
            self.api_header = api_header
        self.data = {}
        self.latest_data = []
        self.changed_data = []
        self.last_recorded = 0
        self.predictors = []

    def __str__(self):
        return f"""Stream Name: {self.stream_name}, \
            API URL: {self.api_url}, \
            """
    
    def json(self):
        return jsonify({
            "stream_name": self.stream_name,
            "api_key": self.api_key,
            "api_url": self.api_url,
            "api_header": self.api_header
        })
    
    def topic(self):
        return self.stream_name
    
    def get_data(self) -> bool:
        try:
            data = requests.get(self.api_url, headers=self.api_header)
        except:
            raise squawker_errors.NotMessage(f"No data in stream {self.stream_name}")
        #this needs to fileter to just the value
        self.latest_data[0] = data.json()
        self.changed_data[0] = True
        record_data = ""
        for index in range(self.changed_data):
            if self.changed_data[index]:
                self.changed_data[index] = False
                record_data += str(self.latest_data[index])
            record_data += "|"
        self.last_recorded = int(time.time())
        # Record it for minutes after the hour
        self.data[(self.last_recorded%3600)//60] = record_data
        return True
    
    def record_prediction(self, wallet_address: str, prediction: str) -> bool:
        if wallet_address not in self.predictors:
            self.predictors.append(wallet_address)
        for wallet in range(self.predictors):
            if wallet_address == self.predictors[wallet]:
                self.latest_data[wallet] = prediction
                return True
        return False
    
    def generate_block_data(self) -> str:
        block_data = "|".join(self.predictors)
        wallet_pos = 0
        disconnected_wallets = []
        for wallet in self.predictors:
            for minute in self.data:
                if len(self.data[minute].split("|")[wallet_pos]) == 0:
                    disconnected_wallets.append(wallet)
            wallet_pos += 1
        for minute in self.data:
            block_data += "@" + self.data[minute]
        for wallet in disconnected_wallets:
                self.predictors.remove(wallet)
        self.data = {}
        return block_data
    