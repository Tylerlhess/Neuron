import squawker_errors
import json
from utils import tx_to_self
from serverside import *
from satorilib.api.wallet import Wallet

debug = 0


def find_latest_messages(asset=ASSETNAME, count=50, wallet: Wallet=None):
    latest = []
    messages = dict()
    messages["addresses"] = list(wallet.send.listaddressesbyasset(asset, False)["result"])
    messages["assetName"] = asset
    deltas = rvn.getaddressdeltas(messages)["result"]
    for tx in deltas:
        if tx["satoshis"] == 100000000 and tx_to_self(tx):
            transaction = wallet.send.decoderawtransaction(wallet.send.getrawtransaction(tx["txid"])["result"])["result"]
            for vout in transaction["vout"]:
                vout = vout["scriptPubKey"]
                if vout["type"] == "transfer_asset" and vout["asset"]["name"] == asset and vout["asset"]["amount"] == 1.0:
                    kaw = {"address": vout["addresses"], "message": vout["asset"]["message"], "block": transaction["locktime"]}
                    latest.append(kaw)
    return sorted(latest[:count], key=lambda message: message["block"], reverse=True)