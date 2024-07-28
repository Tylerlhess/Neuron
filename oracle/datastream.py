from serverside import *
from datastream import Data_Stream
from flask import jsonify
import json
import squawker_errors
import requests


class Data_Stream():
    def __init__(self, file_handle: str=None, stream_name: str=None, api_key: str=None, api_url: str=None, api_header: str=None):
        try:
            with open(file_handle) as f:
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
    
    def get_data(self):
        try:
            data = requests.get(self.api_url, headers=self.api_header)
        except:
            raise squawker_errors.NotMessage(f"No data in stream {self.stream_name}")
        return data
    
    