#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mainly used for generating unique ids for data and model paths since they must be short

# run with:
# sudo nohup /app/anaconda3/bin/python app.py > /dev/null 2>&1 &
from flask_cors import CORS
from typing import Union
from functools import wraps, partial
import os
import sys
import json
import secrets
import webbrowser
import time
import traceback
import pandas as pd
import threading
import hashlib
from queue import Queue
from waitress import serve  # necessary ?
from flask import Flask, url_for, redirect, jsonify, flash, send_from_directory
from flask import session, request, render_template
from flask import Response, stream_with_context, render_template_string
from satorilib.concepts.structs import StreamId, StreamOverviews
from satorilib.api.wallet.wallet import TransactionFailure
from satorilib.api.time import timeToSeconds
from satorilib.api.wallet import RavencoinWallet, EvrmoreWallet
from satorineuron import VERSION, MOTTO, config
from satorineuron import logging
from satorineuron.relay import acceptRelaySubmission, processRelayCsv, generateHookFromTarget, registerDataStream
from satorineuron.web import forms
from satorineuron.web.utils import deduceCadenceString, deduceOffsetString
from oracle import Oracle

logging.info(f'verison: {VERSION}', print=True)


###############################################################################
## Globals ####################################################################
###############################################################################

logging.logging.getLogger('werkzeug').setLevel(logging.logging.ERROR)

debug = True
darkmode = False
firstRun = True
badForm = {}
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
updateTime = 0
updateQueue = Queue()
ENV = config.get().get('env', os.environ.get(
    'ENV', os.environ.get('SATORI_RUN_MODE', 'dev')))
CORS(app, origins=[{
    'local': 'http://192.168.0.10:5002',
    'dev': 'http://localhost:5002',
    'test': 'https://test.satorinet.io',
    'prod': 'https://satorinet.io'}[ENV]])


###############################################################################
## Startup ####################################################################
###############################################################################
while True:
    try:
        oracle = Oracle()
        break
    except ConnectionError as e:
        # try again...
        traceback.print_exc()
        logging.error(f'ConnectionError in app startup: {e}', color='red')
        time.sleep(30)
    # except RemoteDisconnected as e:
    except Exception as e:
        # try again...
        traceback.print_exc()
        logging.error(f'Exception in app startup: {e}', color='red')
        time.sleep(30)

    while True:
        time.sleep(60)




def cryptoAuthRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('cryptoAuthenticated'):
            conf = config.get()
            if conf.get('oracle enabled', False):
                # Server generates a challenge and sends it to the client
                if 'challenge' not in session:
                    session['challenge'] = hashlib.md5(time.time())
                    return jsonify({'challenge': session['challenge']}), 401
                
                # Client submits the signed challenge
                challenge = session['challenge']
                signature = request.headers.get('X-Signature')
                address = request.headers.get('X-Address')  # Obtain client's public key from the headers
                
                if not signature or not start.wallet.verify(challenge, signature, address):
                    return jsonify({'message': 'Invalid signature'}), 403
                
                session['cryptoAuthenticated'] = True
                del session['challenge']  # Remove the challenge after successful authentication
            else:
                session['cryptoAuthenticated'] = False
                
        return f(*args, **kwargs)
    return decorated_function


###############################################################################
## Blockchain Endpoints #######################################################
###############################################################################

@app.route('/api/oracle/get_latest_block', methods=['GET'])
@cryptoAuthRequired
def get_latest_block():
    '''
    Get the latest block from the blockchain
    '''
    return jsonify(oracle.get_latest_block()), 200

@app.route('/api/oracle/get_streams', methods=['GET'])
@cryptoAuthRequired
def get_streams():
    return jsonify(oracle.get_streams()), 200


@app.route('/api/oracle/get_stream_data/<topic>}', methods=['GET'])
@cryptoAuthRequired
def get_stream_data(topic):
    '''
    Get the latest block from the blockchain
    '''
    return jsonify(oracle.get_stream_data(topic)), 200

@app.route('/api/oracle/submit_prediction', methods=['POST'])
@cryptoAuthRequired
def submit_prediction():
    '''
    Submit a prediction
    json format
    { 'topic': 'str',
      'prediction': 'str',
      'signture': 'str',
      'walleet_address': 'valid wallet address matching signature',
      'date': 'epoch timestamp'
      }
    
    '''
    data = request.json
    if data is None:
        return jsonify({'error': 'No data provided'}), 400
    elif 'topic' not in data:
        return jsonify({'error': 'Topic not provided'}), 400
    elif 'prediction' not in data:
        return jsonify({'error': 'Prediction not provided'}), 400
    elif 'signature' not in data:
        return jsonify({'error': 'Signature not provided'}), 400
    elif 'wallet_address' not in data:
        return jsonify({'error': 'Wallet address not provided'}), 400
    elif 'date' not in data:
        return jsonify({'error': 'Date not provided'}), 400
    elif 
    return jsonify(oracle.submit_prediction(data, request)), 200

@app.route('/api/oracle/submit_stream/<topic>', methods=['POST'])
@cryptoAuthRequired
def submit_prediction(topic):
    '''
    Submit a data stream
    '''
    data = request.json
    if data is None:
        return jsonify({'error': 'No data provided'}), 400
    elif 'topic' not in data:
        return jsonify({'error': 'Topic not provided'}), 400
    elif 'prediction' not in data:
        return jsonify({'error': 'Prediction not provided'}), 400
    elif 'signature' not in data:
        return jsonify({'error': 'Signature not provided'}), 400
    elif 'wallet_address' not in data:
        return jsonify({'error': 'Wallet address not provided'}), 400
    elif 'date' not in data:
        return jsonify({'error': 'Date not provided'}), 400
    
    return jsonify(oracle.submit_stream_data(topic, data, request)), 200

@app.route('/api/oracle/create_stream/<topic>', methods=['POST'])
@cryptoAuthRequired
def create_stream(topic):
    '''
    Submit a data stream
    '''
    data = request.json
    if data is None:
        return jsonify({'error': 'No data provided'}), 400
    elif 'stream_name' not in data:
        return jsonify({'error': 'Topic not provided'}), 400
    elif 'api_key' not in data:
        return jsonify({'error': 'Prediction not provided'}), 400
    elif 'api_url' not in data:
        return jsonify({'error': 'Signature not provided'}), 400
    elif 'api_header' not in data:
        return jsonify({'error': 'Wallet address not provided'}), 400
    elif 'date' not in data:
        return jsonify({'error': 'Date not provided'}), 400
    
    return jsonify(oracle.submit_stream_data(topic, data, request)), 200

@app.route('/api/oracle/helloWorld', methods=['GET'])
@cryptoAuthRequired
def helloWorld():
    return jsonify({"Hello": "World"}), 200


@app.route('/api/oracle/accept_stream/<port>', methods=["POST"])
def accept_stream(port):
    result = Oracle.accept_stream(port)
    return jsonify({"accepted": result}) , 200


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.flaskAPIPort(),
        threaded=True,
        debug=debug,
        use_reloader=False)