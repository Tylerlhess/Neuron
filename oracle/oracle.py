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
import threading
from oracle import datastream_api
from satorilib.concepts.structs import Stream, StreamId



class Oracle:
    '''
    an oracle is a service that provides a prediction
    '''

    def __init__(self):
        # try:
        #     self.streams_file = config.get().get('streams_file', None)
        #     if self.streams_file:
        #         self.build_streams()
        # except Exception as e:
        #     logging.info(f"Issue importing streams {type(e)} {str(e)}")
        #     self.streams_file = None
        self.streams = {}
        self.lastblock = None
        self.walletPath = "/Satori/Neuron/wallet" # config.get().walletPath()
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

    #        s.sendall(f"{data}".encode())


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
        Oracle.call_stream(f"{data}", port)

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


    def call_stream(data, port):
        print(data)
        pass

    def handle_call(self, message: str="", return_port: int=None):
        """ received message: {"topic": "{\"source\": \"satori\", \"author\": \"03ecc3fc46ce11cdda6deace2a52f1c700920c304377900dc6643b6aa2ada03ee4\", \"stream\": \"GLPG.USD.10mins\", \"target\": \"results.p\"}", "data": "29.275", "time": "2024-10-14 18:50:01.026029", "hash": "f2028c7376694599"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"03764db13d11dca864ef3e83e7b0257c3b6840f2bcf1fb80ad00e486032edca05d\", \"stream\": \"IMNN.USD.10mins\", \"target\": \"results.p\"}", "data": "1.04", "time": "2024-10-14 18:50:01.402422", "hash": "51f08d5078703654"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"03c062977efa58418f56cec6012ab47931dd0bd5b50a1969822f84316c4c944fcc\", \"stream\": \"HBB.USD.10mins\", \"target\": \"results.p\"}", "data": "29.98", "time": "2024-10-14 18:50:02.912412", "hash": "bf0242cff36e1838"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"0367a0c88402e602e11c412234ed25bfc5bbaa42b4463d155cf43f6d9e7962a7aa\", \"stream\": \"EOG.USD.10mins\", \"target\": \"results.p\"}", "data": "131.5431", "time": "2024-10-14 18:50:01.765019", "hash": "496583ac59266935"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"03b29caade8f73dc2460bb2dc3a32051bd277c5a48418a26f13a6de059dc91e76f\", \"stream\": \"GWAV.USD.10mins\", \"target\": \"results.p\"}", "data": "0.3986", "time": "2024-10-14 18:50:02.723712", "hash": "7a3e41363e7e1cd1"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"02bcbbb7a3a01335d9d97a39a99e611b1d255112eb6da80f990ca3a404a063cd86\", \"stream\": \"IBAC.USD.10mins\", \"target\": \"results.p\"}", "data": "10.02", "time": "2024-10-14 18:50:03.987507", "hash": "6ba151e3d0702d09"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"03507737a5b6c9eb2721e43d7bab15372e426ad8a76eb2988781fbe8547beccbe0\", \"stream\": \"GIB.USD.10mins\", \"target\": \"results.p\"}", "data": "115.3896", "time": "2024-10-14 18:50:09.544528", "hash": "5888b77feb99c7a9"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"022a410d73325a37cb10a17816423df2da140563502b8b37e304f55f4a2ca968b3\", \"stream\": \"CLPT.USD.10mins\", \"target\": \"results.p\"}", "data": "12.33", "time": "2024-10-14 18:50:08.077777", "hash": "2ae88a6411b2290d"}
            received message: {"topic": "{\"source\": \"satori\", \"author\": \"033744da39677b98f4de7d846d2677cd07b1b9933f00e221c1dc628d1b54c0ee94\", \"stream\": \"AISP.USD.10mins\", \"target\": \"results.p\"}", "data": "2.26", "time": "2024-10-14 18:50:01.704882", "hash": "fbc47780bf98d70c"}
        """
        try:
            data = json.loads(message)
            try:
                topic = data["topic"]
                if return_port is None:
                    stream_port = max((self.streams[port] for port in self.streams))
                    stream_port += 1
                    stream = Stream(StreamId(topic["source"], topic["author"], topic["stream"], topic["target"]))
                    print(f"attempting to start recording a datastream {topic} on port {stream_port}")
                    threading.Thread(target=datastream_api.new_datastream, args=(stream, stream_port)).start()
                    return_port = stream_port
                    self.streams[stream_port] = topic
                Oracle.submit_stream_data(data, return_port)

                returnable = True
                

                    
            except:
                pass
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
        server_socket.bind(('localhost', port))
        server_socket.listen(25)
        while True:
            message, client_socket = server_socket.accept()
            self.handle_call(message=message, return_port=client_socket)
            client_socket.close()
            
    def accept_stream(self, port):
        self.streams[str(port)] = requests.get(f"http://127.0.0.1:{port}/topic")
        return True


if __name__ == "__main__":
    while True:
        try:
            oracle = Oracle()
            threading.Thread(target=Oracle.run, args=(24621)).start()
                    
            break
        except ConnectionError as e:
            # try again...
            logging.error(f'ConnectionError in app startup: {e}', color='red')
            time.sleep(30)
        # except RemoteDisconnected as e:
        except Exception as e:
            # try again...
            logging.error(f'Exception in app startup: {e}', color='red')
            time.sleep(30)


