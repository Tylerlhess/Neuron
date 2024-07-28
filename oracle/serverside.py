import ipfshttpclient
import subprocess

# TODO: need to implement with a remote server
ipfs = ipfshttpclient.connect()
ASSETNAME = "SATORI"
IPFSDIRPATH = "/opt/oracle/ipfs"

def signmessage(privkey: str=None, message: str=None) -> str:
    return subprocess.run(f"evrmore-cli signmessagewithprivkey {privkey} {message}", capture_output=True, text=True)

def verifymessage(address: str=None, signature: str=None, message: str=None):
    return subprocess.run(f"evrmore-cli verifymessage {address} {signature} {message}", capture_output=True, text=True)


