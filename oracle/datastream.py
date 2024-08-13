from oracle.serverside import *
from flask import jsonify
import json
import requests, time
from oracle import oracle_errors
import socket
from satorilib.concepts.structs import Stream, StreamId


class Data_Stream():
    def __init__(self, stream: Stream, port: int):
        self.stream = stream
        self.port = port
        self.data = {}
        self.latest_data = []
        self.changed_data = []
        self.last_recorded = 0
        self.predictors = []

        self.actions = {
            "json": self.json,
            "topic": self.topic,
            "rec_pred": self.record_prediction,
            "rec_sub": self.record_submitted_data,
            "build": self.buildBlock,
            "latest": self.latest
        }
        try:
            Data_Stream.return_message(f"new_stream: {self.port}", 24621)
            print(f"started datastream {stream=}")
        except:
            print(f"Failed to notify oracle stream started on {self.port}")
            pass


    def __str__(self):
        return f"""Stream Name: {self.stream_name}, \
            API URL: {self.api_url}, \
            """
    
    def json(self):
        return self.stream.streamId.topic(authorAsPubkey=True)
    
    def topic(self):
        return self.stream.streamId.topic(authorAsPubkey=True)
    
    def get_data(self, local: str = True) -> bool:
        if local:
            try:
                data = requests.get(self.api_url, headers=self.api_header)
            except:
                raise oracle_errors.NotMessage(f"No data in stream {self.stream_name}")
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
    
    def record_prediction(self, wallet_address: str=None, prediction: str=None) -> bool:
        if wallet_address not in self.predictors:
            self.predictors.append(wallet_address)
        for wallet in range(self.predictors):
            if wallet_address == self.predictors[wallet]:
                self.latest_data[wallet] = prediction
                return True
        return False
    
    def record_submitted_data(self, data: str=None) -> bool:
        try:
            self.latest_data[0] = data
            self.changed_data[0] = True
            return True
        except:
            return False
        
    def latest(self):
        return self.latest_data
        
    def buildBlock(self) -> str:
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
        block_data += "#" # this is a separator between the sections of the dataBlock
        self.data = {}
        return block_data
    
    def handle_call(self, socket=None, return_address=""):
        try:
            message = socket.recv(1024).decode()
            func, args = message.split("|") if "|" in message else (message, "")
            print(func, args, self.actions[func])
            if "," in args:
                arg_dict = {key: value for key, value in [arg for arg in args.split(",")]}
                print(f"created {arg_dict=}")
            else:
                arg_dict = {}
                print(f"created empty {arg_dict=}")

            if len(arg_dict.items()) > 0:
                returnable = self.actions[func](arg_dict)
            else:
                returnable = self.actions[func]()
        except Exception as e:
            print(type(e), str(e))
            returnable = False    
            
        Data_Stream.return_message(returnable, socket)

    @staticmethod
    def return_message(data, socket):
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #     print(data, port)
        #     s.connect(port)
        #     s.sendall(f"{data}".encode())
        socket.connect()
        socket.sendall(f"{data}".encode())

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', self.port))
        server_socket.listen(5)
        while True:
            client_socket, address = server_socket.accept()
            self.handle_call(socket=client_socket, return_address=address)
            client_socket.close()


    