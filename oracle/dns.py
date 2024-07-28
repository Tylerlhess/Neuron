from serverside import *
from datastream import Data_Stream
import json
import squawker_errors


class DNS():
    def __init__(self, block_hash: str=None):
        self.block_hash = block_hash
        if block_hash:
            try:
                self.raw_dns = self.get_raw_dns()
                self.ip_address = self.raw_dns["ip_address"]
                self.ports = {portname: portnumber for portname, portnumber in self.raw_dns["ports"]}
                self.data_streams = [Data_Stream(stream) for stream in self.raw_dns["data_streams"]]
            except:
                raise squawker_errors.NotMessage(f"No dns in ipfs hash {block_hash}")
        else: 
            self.raw_dns = None
            self.ip_address = None
            self.ports = {}
            self.data_streams = []

    def __str__(self):
        return f"""IP_ADDRESS: {self.ip_address}, \
            Ports: {', '.join({key: value for key, value in self.ports})}, \
            Data Streams: {', '.join({str(stream) for stream in self.data_streams})}, \
            """

    def get_raw_dns(self):
        try:
            ipfs_hash = self.block_hash
            raw_dns = json.loads(ipfs.cat(ipfs_hash))
        except squawker_errors.NotMessage as e:
            raise squawker_errors.NotMessage(str(e))
        except Exception as e:
            pass
        return raw_dns

    @property
    def ip_address(self):
        return self.ip_address

    @property
    def ports(self):
        return self.ports
    
    @property
    def data_streams(self):
        return self.data_streams
    
    @property
    def ipfs_hash(self):
        return self.block_hash
    
    @ip_address.setter
    def ip_address(self, ip_address):
        self.ip_address = ip_address

    def add_port(self, port):
        port_name, port_number = port
        self.ports[port_name] = port_number

    def add_data_stream(self, data_stream):
        self.data_streams.append(data_stream)

    def publish_dns(self):
        self.raw_dns = {
            "data_streams": sorted([stream.json() for stream in self.data_streams]),
            "ip_address": self.ip_address,
            "ports": {port_name: port_number for port_name, port_number in self.ports.items()},
        }
        ipfs_hash = ipfs.add_json(self.raw_dns)
        return ipfs_hash