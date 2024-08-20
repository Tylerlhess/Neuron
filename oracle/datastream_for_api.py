from oracle.serverside import *
from flask import jsonify
import json
import requests, time
from oracle import oracle_errors
import socket
from satorilib.concepts.structs import Stream
from satorineuron import relay

DEBUG = 1
class Data_Stream():
    def __init__(self, stream: Stream, port: int):
        self.stream = stream
        self.data = {}
        self.latest_data = ["",]
        self.changed_data = [False,]
        self.last_recorded = 0
        self.predictors = ["stream",]

        try:
            Data_Stream.return_message(f"new_stream: {port}", 24621)
            print(f"started datastream {stream=}")
        except:
            print(f"Failed to notify oracle stream started on {port}")
            pass


    def __str__(self):
        return f"""Stream Name: {self.stream_name}, \
            API URL: {self.api_url}, \
            """
    
    def json(self):
        return self.stream.streamId.topic(authorAsPubkey=True)
    
    def topic(self):
        return self.stream.streamId.topic(authorAsPubkey=True)
    
    def get_data(self, local: bool = True):
        if local:
            try:
                data = relay.RawStreamRelayEngine.call(self.stream)
                clean_data = relay.RawStreamRelayEngine.callHook(self.stream, data)
                print(f"{clean_data=}")

            except:
                print(f"No data in stream {self.stream_name}")
                raise oracle_errors.NotMessage(f"No data in stream {self.stream_name}")
        #this needs to fileter to just the value
            self.latest_data[0] = clean_data
            self.changed_data[0] = True
        record_data = ""
        for index in range(0, len(self.changed_data)):
            if self.changed_data[index]:
                self.changed_data[index] = False
                record_data += str(self.latest_data[index])
            record_data += "|"
        self.last_recorded = int(time.time())
        # Record it for minutes after the hour
        self.data[(self.last_recorded%3600)//60] = record_data
        return record_data
    
    def record_prediction(self, wallet_address: str, prediction: str) -> bool:
        if DEBUG: print(f"<DEBUG> Made it to record_predictions with {wallet_address=} {prediction=}")
        if wallet_address not in self.predictors:
            self.predictors.append(wallet_address)
            self.changed_data.append(True)
            self.latest_data.append("")
            if DEBUG: print(self.predictors, self.changed_data)
        for wallet in range(0, len(self.predictors)):
            if DEBUG: print(wallet, self.predictors[wallet], wallet_address)
            if wallet_address == self.predictors[wallet]:
                if DEBUG: print(self.latest_data)
                self.latest_data[wallet] = prediction
                return True
        return False
    
    def record_submitted_data(self, data) -> bool:
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


    @staticmethod
    def return_message(data, socket):
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #     print(data, port)
        #     s.connect(port)
        #     s.sendall(f"{data}".encode())
        socket.sendall(f"{data}".encode())

    


    