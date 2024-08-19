from oracle.dns import DNS
from oracle.datastream import Data_Stream
import os
import json
import time
import requests
import hashlib
import yaml
from oracle.serverside import signmessage, verifymessage, ipfs
from satorineuron import config
from satorineuron import logging
import socket


class Oracle:
    '''
    an oracle is a service that provides a prediction
    '''

    def __init__(self):
        try:
            self.streams_file = config.get().get('streams_file', None)
            if self.streams_file:
                self.build_streams()
        except Exception as e:
            logging.info(f"Issue importing streams {type(e)} {str(e)}")
            self.streams_file = None
            self.streams = {}
        self.lastblock = None
        self.walletPath = config.get().get().walletPath()
        with open(self.walletPath + '/wallet.yaml', 'r') as f:
            self.walletDetails = yaml.safe_load(f)
            self.wallet_address = self.walletDetails["evr"]["address"]
            self.privkey = self.walletDetails["privateKey"]
        try:
            self.dns = DNS(config.get().get('dns_ipfs_hash', {}), self)
        except:
            self.dns = DNS(block_hash=None, oracle=self)
        self.sessions = {}
        self.headers = {}


    # def build_streams(self):
    #     '''
    #     build a list of streams from the streams_dir
    #     '''
    #     self.streams = {}
    #     with open(self.streams_file, 'r') as f:
    #         next_stream = ""
    #         for line in f.readlines():
    #             if line[0] == "?" and len(next_stream) > 1:
    #                 self.streams.append((Oracle.parse_stream(next_stream), True,))
    #             else:
    #                 next_stream += line
    
    def get_streams(self):
        '''
        get a stream by id
        '''
        if len(self.streams) > 0:
            return [stream[0].topic() for stream in self.streams]
        else:
            return []
        
    def get_latest_block(self):
        '''
        get the latest block from the streams
        '''
        
        return self.lastblock
    
    def get_stream_data(self, topic):
        '''
        get the data from a stream
        '''
        if self.streams[topic]:
            Oracle.call_stream("latest", self.streams[topic])
        return None
    
    def collect_streams(self):
        for stream in range(len(self.streams)):
            self.streams[stream][0].get_data(self.streams[stream][1])

    def buildBlock(self):
        dataBlock = str(self.dns.block_hash) + "#"
        for stream in self.streams:
            dataBlock += str(stream.buildBlock())
        dataBlock += str(self.knots.buildBlock())
        return self.signBlock(dataBlock)

    def signBlock(self, dataBlock: str=None) -> dict:
        signedBlock = {}
        signedBlock["address"] = self.wallet_address
        signedBlock["dataBlock"] = dataBlock
        signedBlock["dataSha256"] = hashlib.sha256(dataBlock.encode()).hexdigest()
        signedBlock["dataSignature"] = signmessage(self.privkey, signedBlock["dataSha256"])
        return signedBlock
    
    @staticmethod
    def verifyBlock(block: dict=None) -> bool:
        return verifymessage(address=block["address"], signature=block["dataSignature"], message=block["dataSha256"])
    
    @staticmethod
    def read_dns(block:str=None):
        if Oracle.verifyBlock(block):
            try:
                dnsIPFS = block["dataBlock"].split("#")[0]
                dnsJson = json.loads(ipfs.cat(dnsIPFS))
                return dnsJson, True
            except Exception as e:
                logging.info(f"Exception thrown from read_dns after verified block {type(e)}: {str(e)}")
                return {}, True 

        else:
            try:
                dnsIPFS = block["dataBlock"].split("#")[0]
                dnsJson = json.loads(ipfs.cat(dnsIPFS))
                return dnsJson, False
            except Exception as e:
                logging.info(f"Exception thrown from read_dns after verification failed {type(e)}: {str(e)}")
                return {}, False

    @staticmethod
    def call_stream(data, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', port))
            s.sendall(f"{data}".encode())


    def connectToOracleFromBlock(self, block:dict=None, URI: str=None):
        dns, verified = Oracle.read_dns(block=block)
        ip_address, port = dns["IP_ADDRESS"], dns["Ports"]["oracle"]
        if ip_address not in self.sessions:
            self.sessions[ip_address] = requests.Session()
        session = self.sessions[ip_address]
        if ip_address in self.headers:
            session.headers.update(self.headers[ip_address])
        result = session.get(f"http://{ip_address}:{port}{URI}")
        if result.status_code == 401:
            challenge = result.json["challenge"]
            logging.info(f"challenge has been set to {challenge}")
            signature = signmessage(challenge)
            self.headers[ip_address]["X-Signature"] = signature
            self.headers[ip_address]["X-Address"] = self.wallet_address
            session.headers.update(self.headers[ip_address])
            result = session.get(f"http://{ip_address}:{port}{URI}")
        return session, result
    
    def connectToOracleFromIP(self, ip_address, port, URI):
        if ip_address not in self.sessions:
            self.sessions[ip_address] = requests.Session()
        session = self.sessions[ip_address]
        if ip_address in self.headers:
            session.headers.update(self.headers[ip_address])
        result = session.get(f"http://{ip_address}:{port}{URI}")
        if result.status_code == 401:
            challenge = result.json["challenge"]
            logging.info(f"challenge has been set to {challenge}")
            signature = signmessage(challenge)
            self.headers[ip_address]["X-Signature"] = signature
            self.headers[ip_address]["X-Address"] = self.wallet_address
            session.headers.update(self.headers[ip_address])
            result = session.get(f"http://{ip_address}:{port}{URI}")
        return session, result

    def submit_stream_data(self, topic, data):
        port = self.streams[topic]
        Oracle.call_stream(f"rec_sub: {data}", 24621)

    # def create_submitted_stream(self, json_stream: str = "{}"):
    #     try:
    #         raw_data = json_stream
    #         stream_name = raw_data["stream_name"]
    #         api_key = raw_data["api_key"]
    #         api_url = raw_data["api_url"]
    #         api_header = raw_data["api_header"]
    #         self.streams[stream_name] = (Data_Stream(file_path=None, 
    #                                                 stream_name=stream_name,
    #                                                 api_key=api_key,
    #                                                 api_url=api_url,
    #                                                 api_header=api_header), False)
    #     except:
    #         return False
        
    def handle_call(self, message: str="", return_port: int=None):
        try:
            func, args = message.split("|")
            arg_dict = {key: value for key, value in [arg for arg in args.split(",")]}
            if len(arg_dict.items) > 0:
                returnable = self.actions[func](arg_dict)
            else:
                returnable = self.actions[func]()
        except:
            returnable = False    
            
        Data_Stream.return_message(returnable, return_port)

    @staticmethod
    def return_message(data, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', port))
            s.sendall(f"{data}".encode())
    
    def run(self, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', 24621))
        server_socket.listen(25)
        while True:
            message, client_socket = server_socket.accept()
            self.handle_call(message=message, return_port=client_socket)
            client_socket.close()
            

