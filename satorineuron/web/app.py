import sys
import time
import subprocess


def startSatori():
    return subprocess.Popen([sys.executable, 'satori.py'])


def monitorAndRestartSatori():
    while True:
        print("Starting Satori...")
        process = startSatori()

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
        start = StartupDag(
            env=ENV,
            urlServer={
                'local': 'http://192.168.0.10:5002',
                'dev': 'http://localhost:5002',
                'test': 'https://test.satorinet.io',
                'prod': 'https://stage.satorinet.io'}[ENV],
            urlMundo={
                'local': 'http://192.168.0.10:5002',
                'dev': 'http://localhost:5002',
                'test': 'https://test.satorinet.io',
                'prod': 'https://mundo.satorinet.io'}[ENV],
            urlPubsubs={
                'local': ['ws://192.168.0.10:24603'],
                'dev': ['ws://localhost:24603'],
                'test': ['ws://test.satorinet.io:24603'],
                'prod': ['ws://pubsub2.satorinet.io:24603', 'ws://pubsub3.satorinet.io:24603', 'ws://d2ruaphb4v7v3i.cloudfront.net/']}[ENV],
            # 'prod': ['ws://pubsub2.satorinet.io:24603', 'ws://pubsub3.satorinet.io:24603', 'ws://pubsub4.satorinet.io:24603']}[ENV],
            urlSynergy={
                'local': 'https://192.168.0.10:24602',
                'dev': 'https://localhost:24602',
                'test': 'https://test.satorinet.io:24602',
                'prod': 'https://synergy.satorinet.io:24602'}[ENV],
            isDebug=sys.argv[1] if len(sys.argv) > 1 else False)
        print('building engine')
        # start.buildEngine()
        # threading.Thread(target=start.start, daemon=True).start()
        logging.info(f'environment: {ENV}', print=True)
        logging.info('Satori Neuron is starting...', color='green')
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

###############################################################################
## Functions ##################################################################
###############################################################################


def returnNone():
    r = Response()
    # r.set_cookie("My important cookie", value=some_cool_value)
    return r, 204


def hashSaltIt(string: str) -> str:
    import hashlib
    # return hashlib.sha256(rowStr.encode()).hexdigest()
    # return hashlib.md5(rowStr.encode()).hexdigest()
    return hashlib.blake2s(
        (string+string).encode(),
        digest_size=8).hexdigest()


def isActuallyLockable():
    conf = config.get()
    return conf.get('neuron lock enabled') is not None and (
        conf.get('neuron lock hash') is not None or
        conf.get('neuron lock password') is not None)


def isActuallyLocked():
    conf = config.get()
    return conf.get('neuron lock enabled') == True and (
        conf.get('neuron lock hash') is not None or
        conf.get('neuron lock password') is not None)


def get_user_id():
    return session.get('user_id', '0')


def getFile(ext: str = '.csv') -> tuple[str, int, Union[None, 'FileStorage']]:
    if 'file' not in request.files:
        return 'No file uploaded', 400, None
    f = request.files['file']
    if f.filename == '':
        return 'No selected file', 400, None
    if f:
        if ext is None:
            return 'success', 200, f
        elif isinstance(ext, str) and f.filename.endswith(ext):
            return 'success', 200, f
        else:
            return 'Invalid file format. Only CSV files are allowed', 400, None
    return 'unknown error getting file', 500, None


def getResp(resp: Union[dict, None] = None) -> dict:
    return {
        'version': VERSION,
        'lockEnabled': isActuallyLocked(),
        'lockable': isActuallyLockable(),
        'moto': MOTO,
        'env': ENV,
        'paused': start.paused,
        'darkmode': darkmode,
        'title': 'Satori',
        **(resp or {})}


def closeVault(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start.closeVault()
        return f(*args, **kwargs)
    return decorated_function


def authRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            # conf = config.get()
            # if not conf.get('neuron lock enabled', False) or (
            #    not conf.get('neuron lock password') and
            #    not conf.get('neuron lock hash')
            # ):
            if isActuallyLocked():
                return redirect(url_for('passphrase', next=request.url))
            else:
                session['authenticated'] = True
        return f(*args, **kwargs)
    return decorated_function


passphrase_html = '''
    <!doctype html>
    <title>Satori</title>
    <h1>Unlock the Satori Neuron</h1>
    <form method="post">
      <p><input type="password" name="passphrase">
      <input type="hidden" name="next" value="{{ next }}">
      <p><input type="submit" name="unlock" value="Submit">
    </form>
'''


@app.route('/unlock', methods=['GET', 'POST'])
def passphrase():

    def tryToInterpretAsInteger(password: str, exectedPassword: Union[str, int]) -> bool:
        if isinstance(exectedPassword, int):
            try:
                return int(password) == expectedPassword
            except Exception as _:
                pass
        return False

    if request.method == 'POST':
        target = request.form.get('next') or 'dashboard'
        conf = config.get()
        expectedPassword = conf.get('neuron lock password')
        expectedPassword = expectedPassword or conf.get('neuron lock hash', '')
        if (request.form['passphrase'] == expectedPassword or
                    hashSaltIt(request.form['passphrase']) == expectedPassword or
                    tryToInterpretAsInteger(
                    request.form['passphrase'], expectedPassword)
                ):
            session['authenticated'] = True
            return redirect(target)
        else:
            return "Wrong passphrase, try again.\n\nIf you're unable to unlock your Neuron remove the setting in the config file."
    next_url = request.args.get('next')
    return render_template_string(passphrase_html, next=next_url)


@app.route('/lock/enable', methods=['GET', 'POST'])
def lockEnable():
    # vaultPath = config.walletPath('vault.yaml')
    # if os.path.exists(vaultPath) or create:
    if isActuallyLockable():
        config.add(data={'neuron lock enabled': True})
    return redirect(url_for('dashboard'))


@app.route('/lock/relock', methods=['GET', 'POST'])
@authRequired
def lockRelock():
    ''' no ability to disable, this gives the user peace of mind '''
    session['authenticated'] = False
    return redirect(url_for('dashboard'))

###############################################################################
## Errors #####################################################################
###############################################################################


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

###############################################################################
## Routes - static ############################################################
###############################################################################


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static/img/favicon'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


@app.route('/static/<path:path>')
@authRequired
def sendStatic(path):
    return send_from_directory('static', path)


@app.route('/upload_history_csv', methods=['POST'])
@authRequired
def uploadHistoryCsv():
    msg, status, f = getFile('.csv')
    if f is not None:
        f.save('/Satori/Neuron/uploaded/history.csv')
        return 'Successful upload.', 200
    else:
        flash(msg, 'success' if status == 200 else 'error')
    return redirect(url_for('dashboard'))


@app.route('/upload_datastream_csv', methods=['POST'])
@authRequired
def uploadDatastreamCsv():
    msg, status, f = getFile('.csv')
    if f is not None:
        df = pd.read_csv(f)
        processRelayCsv(start, df)
        logging.info('Successful upload', 200, print=True)
    else:
        logging.error(msg, status, print=True)
        flash(msg, 'success' if status == 200 else 'error')
    return redirect(url_for('dashboard'))


# @app.route('/test')
# def test():
#    logging.info(request.MOBILE)
#    return render_template('test.html')


# @app.route('/kwargs')
# def kwargs():
#    ''' ...com/kwargs?0-name=widget_name0&0-value=widget_value0&0-type=widget_type0&1-name=widget_name1&1-value=widget_value1&1-#type=widget_type1 '''
#    kwargs = {}
#    for i in range(25):
#        if request.args.get(f'{i}-name') and request.args.get(f'{i}-value'):
#            kwargs[request.args.get(f'{i}-name')
#                   ] = request.args.get(f'{i}-value')
#            kwargs[request.args.get(f'{i}-name') +
#                   '-type'] = request.args.get(f'{i}-type')
#    return jsonify(kwargs)


@app.route('/ping', methods=['GET'])
def ping():
    from datetime import datetime
    return jsonify({'now': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


@app.route('/pause/<timeout>', methods=['GET'])
@authRequired
def pause(timeout):
    try:
        timeout = int(timeout)
        if timeout < 12:
            start.pause(timeout*60*60)
    except Exception as _:
        flash('invalid pause timeout', 'error')
    return redirect(url_for('dashboard'))


@app.route('/unpause', methods=['GET'])
@authRequired
def unpause():
    start.unpause()
    return redirect(url_for('dashboard'))


@app.route('/backup/<target>', methods=['GET'])
@authRequired
def backup(target: str = 'satori'):
    outputPath = '/Satori/Neuron/satorineuron/web/static/download'
    if target == 'satori':
        from satorilib.api.disk.zip.zip import zipSelected
        zipSelected(
            folderPath=f'/Satori/Neuron/{target}',
            outputPath=f'{outputPath}/{target}.zip',
            selectedFiles=['config', 'data', 'models', 'wallet', 'uploaded'])
    else:
        from satorilib.api.disk.zip.zip import zipFolder
        zipFolder(
            folderPath=f'/Satori/Neuron/{target}',
            outputPath=f'{outputPath}/{target}')
    return redirect(url_for('sendStatic', path=f'download/{target}.zip'))


@app.route('/restart', methods=['GET'])
def restart():
    start.udpQueue.put(Envelope(ip='', vesicle=Signal(restart=True)))
    html = (
        '<!DOCTYPE html>'
        '<html>'
        '<head>'
        '    <title>Restarting Satori Neuron</title>'
        '    <script type="text/javascript">'
        '        setTimeout(function(){'
        '            window.location.href = window.location.protocol + "//" + window.location.host;'
        '        }, 1000 * 60 * 10); // 600,000 milliseconds'
        '    </script>'
        '</head>'
        '<body>'
        '    <p>Satori Neuron is attempting to restart. <b>Please wait,</b> the restart process can take several minutes as it downloads updates.</p>'
        '    <p>If after 10 minutes this page has not refreshed, <a href="javascript:void(0);" onclick="window.location.href = window.location.protocol + "//" + window.location.host;">click here to refresh the Satori Neuron UI</a>.</p>'
        '    <p>Thank you.</p>'
        '</body>'
        '</html>'
    )
    return html, 200


@app.route('/shutdown', methods=['GET'])
@authRequired
def shutdown():
    start.udpQueue.put(Envelope(ip='', vesicle=Signal(shutdown=True)))
    html = (
        '<!DOCTYPE html>'
        '<html>'
        '<head>'
        '    <title>Shutting Down Satori Neuron</title>'
        '</head>'
        '<body>'
        '    <p>Satori Neuron is attempting to shut down. To verify it has shut down you can make sure the container is not running under the Container tab in Docker, and you can close the terminal window which shows the logs of the Satori Neuron.</p>'
        '</body>'
        '</html>'
    )
    return html, 200


@app.route('/mode/light', methods=['GET'])
@authRequired
def modeLight():
    global darkmode
    darkmode = False
    return redirect(url_for('dashboard'))


@app.route('/mode/dark', methods=['GET'])
@authRequired
def modeDark():
    global darkmode
    darkmode = True
    return redirect(url_for('dashboard'))

###############################################################################
## Routes - forms #############################################################
###############################################################################


@app.route('/configuration', methods=['GET', 'POST'])
@authRequired
@closeVault
def editConfiguration():
    import importlib
    global forms
    forms = importlib.reload(forms)

    def present_form(edit_configuration):
        edit_configuration.flaskPort.data = config.flaskPort()
        edit_configuration.nodejsPort.data = config.nodejsPort()
        edit_configuration.dataPath.data = config.dataPath()
        edit_configuration.modelPath.data = config.modelPath()
        edit_configuration.walletPath.data = config.walletPath()
        edit_configuration.defaultSource.data = config.defaultSource()
        edit_configuration.electrumxServers.data = config.electrumxServers()
        return render_template('forms/config.html', **getResp({
            'title': 'Configuration',
            'edit_configuration': edit_configuration}))

    def accept_submittion(edit_configuration):
        data = {}
        if edit_configuration.flaskPort.data not in ['', None, config.flaskPort()]:
            data = {
                **data, **{config.verbose('flaskPort'): edit_configuration.flaskPort.data}}
        if edit_configuration.nodejsPort.data not in ['', None, config.nodejsPort()]:
            data = {
                **data, **{config.verbose('nodejsPort'): edit_configuration.nodejsPort.data}}
        if edit_configuration.dataPath.data not in ['', None, config.dataPath()]:
            data = {
                **data, **{config.verbose('dataPath'): edit_configuration.dataPath.data}}
        if edit_configuration.modelPath.data not in ['', None, config.modelPath()]:
            data = {
                **data, **{config.verbose('modelPath'): edit_configuration.modelPath.data}}
        if edit_configuration.walletPath.data not in ['', None, config.walletPath()]:
            data = {
                **data, **{config.verbose('walletPath'): edit_configuration.walletPath.data}}
        if edit_configuration.defaultSource.data not in ['', None, config.defaultSource()]:
            data = {
                **data, **{config.verbose('defaultSource'): edit_configuration.defaultSource.data}}
        if edit_configuration.electrumxServers.data not in ['', None, config.electrumxServers()]:
            data = {**data, **{config.verbose('electrumxServers'): [
                edit_configuration.electrumxServers.data]}}
        config.modify(data=data)
        return redirect('/dashboard')

    edit_configuration = forms.EditConfigurationForm(formdata=request.form)
    if request.method == 'POST':
        return accept_submittion(edit_configuration)
    return present_form(edit_configuration)


@app.route('/hook/<target>', methods=['GET'])
@authRequired
def hook(target: str = 'Close'):
    ''' generates a hook for the given target '''
    return generateHookFromTarget(target)


@app.route('/hook/', methods=['GET'])
@authRequired
def hookEmptyTarget():
    ''' generates a hook for the given target '''
    # in the case target is empty string
    return generateHookFromTarget('Close')


@app.route('/relay', methods=['POST'])
@authRequired
def relay():
    '''
    format for json post (as python dict):{
        "source": "satori",
        "name": "nameOfSomeAPI",
        "target": "optional",
        "data": 420,
    }
    '''

    # def accept_submittion(data: dict):
    #    if not start.relayValidation.validRelay(data):
    #        return 'Invalid payload. here is an example: {"source": "satori", "name": "nameOfSomeAPI", "target": "optional", "data": 420}', 400
    #    if not start.relayValidation.streamClaimed(
    #        name=data.get('name'),
    #        target=data.get('target')
    #    ):
    #        save = start.relayValidation.registerStream(
    #            data=data)
    #        if save == False:
    #            return 'Unable to register stream with server', 500
    #        # get pubkey, recreate connection...
    #        start.checkin()
    #        start.pubsConnect()
    #    # ...pass data onto pubsub
    #    start.publish(
    #        topic=StreamId(
    #            source=data.get('source', 'satori'),
    #            author=start.wallet.publicKey,
    #            stream=data.get('name'),
    #            target=data.get('target')).topic(),
    #        data=data.get('data'))
    #    return 'Success: ', 200
    return acceptRelaySubmission(start, json.loads(request.get_json()))


@app.route('/send_satori_transaction_from_wallet/<network>', methods=['POST'])
@authRequired
def sendSatoriTransactionFromWallet(network: str = 'main'):
    # return sendSatoriTransactionUsing(start.getWallet(network=network), network, 'wallet')
    return sendSatoriTransactionUsing(start.getWallet(network=network), network, 'wallet')


@app.route('/send_satori_transaction_from_vault/<network>', methods=['POST'])
@authRequired
def sendSatoriTransactionFromVault(network: str = 'main'):
    return sendSatoriTransactionUsing(start.vault, network, 'vault')


def sendSatoriTransactionUsing(myWallet: Union[RavencoinWallet, EvrmoreWallet], network: str, loc: str):
    if myWallet is None:
        flash(f'Send Failed: {e}')
        return redirect(f'/wallet/{network}')

    import importlib
    global forms
    global badForm
    forms = importlib.reload(forms)

    def accept_submittion(sendSatoriForm):
        def refreshWallet():
            time.sleep(4)
            # doesn't respect the cooldown
            myWallet.get(allWalletInfo=False)

        # doesn't respect the cooldown
        myWallet.getUnspentSignatures()
        if sendSatoriForm.address.data == start.getWallet(network=network).address:
            # if we're sending to wallet we don't want it to auto send back to vault
            disableAutosecure(network)
        try:
            # logging.debug('sweep', sendSatoriForm.sweep.data, color='magenta')
            result = myWallet.typicalNeuronTransaction(
                sweep=sendSatoriForm.sweep.data,
                amount=sendSatoriForm.amount.data or 0,
                address=sendSatoriForm.address.data or '')
            if result.msg == 'creating partial, need feeSatsReserved.':
                responseJson = start.server.requestSimplePartial(
                    network=network)
                result = myWallet.typicalNeuronTransaction(
                    sweep=sendSatoriForm.sweep.data,
                    amount=sendSatoriForm.amount.data or 0,
                    address=sendSatoriForm.address.data or '',
                    completerAddress=responseJson.get('completerAddress'),
                    feeSatsReserved=responseJson.get('feeSatsReserved'),
                    changeAddress=responseJson.get('changeAddress'),
                )
            if result is None:
                flash('Send Failed: wait 10 minutes, refresh, and try again.')
            elif result.success:
                if (  # checking any on of these should suffice in theory...
                    result.tx is not None and
                    result.reportedFeeSats is not None and
                    result.reportedFeeSats > 0 and
                    result.msg == 'send transaction requires fee.'
                ):
                    r = start.server.broadcastSimplePartial(
                        tx=result.tx,
                        reportedFeeSats=result.reportedFeeSats,
                        feeSatsReserved=responseJson.get('feeSatsReserved'),
                        walletId=responseJson.get('partialId'),
                        network=(
                            'ravencoin' if start.networkIsTest(network)
                            else 'evrmore'))
                    if r.text != '':
                        flash(r.text)
                    else:
                        flash(
                            'Send Failed: wait 10 minutes, refresh, and try again.')
                else:
                    flash(str(result.result))
            else:
                flash(f'Send Failed: {result.msg}')
        except TransactionFailure as e:
            flash(f'Send Failed: {e}')
        refreshWallet()
        return redirect(f'/{loc}/{network}')

    sendSatoriForm = forms.SendSatoriTransaction(formdata=request.form)
    return accept_submittion(sendSatoriForm)


@app.route('/register_stream', methods=['POST'])
@authRequired
def registerStream():
    import importlib
    global forms
    global badForm
    forms = importlib.reload(forms)

    def accept_submittion(newRelayStream):
        # done: we should register this stream and
        # todo: save the uri, headers, payload, and hook to a config manifest file.
        global badForm
        data = {
            # **({'source': newRelayStream.source.data} if newRelayStream.source.data not in ['', None] else {}), # in the future we will allow users to specify a source like streamr or satori
            **({'topic': newRelayStream.topic.data} if newRelayStream.topic.data not in ['', None] else {}),
            **({'name': newRelayStream.name.data} if newRelayStream.name.data not in ['', None] else {}),
            **({'target': newRelayStream.target.data} if newRelayStream.target.data not in ['', None] else {}),
            **({'cadence': newRelayStream.cadence.data} if newRelayStream.cadence.data not in ['', None] else {}),
            **({'offset': newRelayStream.offset.data} if newRelayStream.offset.data not in ['', None] else {}),
            **({'datatype': newRelayStream.datatype.data} if newRelayStream.datatype.data not in ['', None] else {}),
            **({'description': newRelayStream.description.data} if newRelayStream.description.data not in ['', None] else {}),
            **({'tags': newRelayStream.tags.data} if newRelayStream.tags.data not in ['', None] else {}),
            **({'url': newRelayStream.url.data} if newRelayStream.url.data not in ['', None] else {}),
            **({'uri': newRelayStream.uri.data} if newRelayStream.uri.data not in ['', None] else {}),
            **({'headers': newRelayStream.headers.data} if newRelayStream.headers.data not in ['', None] else {}),
            **({'payload': newRelayStream.payload.data} if newRelayStream.payload.data not in ['', None] else {}),
            **({'hook': newRelayStream.hook.data} if newRelayStream.hook.data not in ['', None] else {}),
            **({'history': newRelayStream.history.data} if newRelayStream.history.data not in ['', None] else {}),
        }
        if data.get('hook') in ['', None, {}]:
            hook, status = generateHookFromTarget(data.get('target', ''))
            if status == 200:
                data['hook'] = hook
        msgs, status = registerDataStream(start, data)
        if status == 400:
            badForm = data
        elif status == 200:
            badForm = {}
        for msg in msgs:
            flash(msg)
        return redirect('/dashboard')

    newRelayStream = forms.RelayStreamForm(formdata=request.form)
    return accept_submittion(newRelayStream)


@app.route('/edit_stream/<topic>', methods=['GET'])
@authRequired
def editStream(topic=None):
    # name,target,cadence,offset,datatype,description,tags,url,uri,headers,payload,hook
    import importlib
    global forms
    global badForm
    forms = importlib.reload(forms)
    try:
        badForm = [
            s for s in start.relay.streams
            if s.streamId.topic() == topic][0].asMap(noneToBlank=True)
    except IndexError:
        # on rare occasions
        # IndexError: list index out of range
        # cannot reproduce, maybe it's in the middle of reconnecting?
        pass
    # return redirect('/dashboard#:~:text=Create%20Data%20Stream')
    return redirect('/dashboard#CreateDataStream')


# @app.route('/remove_stream/<source>/<stream>/<target>/', methods=['GET'])
# def removeStream(source=None, stream=None, target=None):
@app.route('/remove_stream/<topic>', methods=['GET'])
@authRequired
def removeStream(topic=None):
    # removeRelayStream = {
    #    'source': source or 'satori',
    #    'name': stream,
    #    'target': target}
    removeRelayStream = StreamId.fromTopic(topic)
    return removeStreamLogic(removeRelayStream)


def removeStreamLogic(removeRelayStream: StreamId, doRedirect=True):
    def accept_submittion(removeRelayStream: StreamId, doRedirect=True):
        r = start.server.removeStream(payload=json.dumps({
            'source': removeRelayStream.source,
            # should match removeRelayStream.author
            'pubkey': start.wallet.publicKey,
            'stream': removeRelayStream.stream,
            'target': removeRelayStream.target,
        }))
        if (r.status_code == 200):
            msg = 'Stream deleted.'
            # get pubkey, recreate connection, restart relay engine
            try:
                start.relayValidation.claimed.remove(removeRelayStream)
            except Exception as e:
                logging.error('remove stream logic err', e)
            start.checkin()
            start.pubsConnect()
            start.startRelay()
        else:
            msg = 'Unable to delete stream.'
        if doRedirect:
            flash(msg)
            return redirect('/dashboard')

    return accept_submittion(removeRelayStream, doRedirect)


@app.route('/remove_stream_by_post', methods=['POST'])
@authRequired
def removeStreamByPost():

    def accept_submittion(removeRelayStream):
        r = start.server.removeStream(payload=json.dumps({
            'source': removeRelayStream.get('source', 'satori'),
            'pubkey': start.wallet.publicKey,
            'stream': removeRelayStream.get('name'),
            'target': removeRelayStream.get('target'),
        }))
        if (r.status_code == 200):
            msg = 'Stream deleted.'
            # get pubkey, recreate connection, restart relay engine
            try:
                start.relayValidation.claimed.remove(removeRelayStream)
            except Exception as e:
                logging.error('remove strem by post err', e)
            start.checkin()
            start.pubsConnect()
            start.startRelay()
        else:
            msg = 'Unable to delete stream.'
        flash(msg)
        return redirect('/dashboard')

    removeRelayStream = json.loads(request.get_json())
    return accept_submittion(removeRelayStream)


###############################################################################
## Routes - dashboard #########################################################
###############################################################################


@app.route('/')
@app.route('/home', methods=['GET'])
@app.route('/index', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
@closeVault
@authRequired
def dashboard():
    '''
    UI
    - send to setup process if first time running the app...
    - show earnings
    - access to wallet
    - access metrics for published streams
        (which streams do I have?)
        (how often am I publishing to my streams?)
    - access to data management (monitor storage resources)
    - access to model metrics
        (show accuracy over time)
        (model inputs and relative strengths)
        (access to all predictions and the truth)
    '''
    import importlib
    global forms
    global badForm
    forms = importlib.reload(forms)

    def present_stream_form():
        '''
        this function could be used to fill a form with the current
        configuration for a stream in order to edit it.
        '''
        if isinstance(badForm.get('streamId'), StreamId):
            name = badForm.get('streamId').stream
            target = badForm.get('streamId').target
        elif isinstance(badForm.get('streamId'), dict):
            name = badForm.get('streamId', {}).get('stream', '')
            target = badForm.get('streamId', {}).get('target', '')
        else:
            name = ''
            target = ''
        newRelayStream = forms.RelayStreamForm(formdata=request.form)
        newRelayStream.topic.data = badForm.get(
            'topic', badForm.get('kwargs', {}).get('topic', ''))
        newRelayStream.name.data = badForm.get('name', None) or name
        newRelayStream.target.data = badForm.get('target', None) or target
        newRelayStream.cadence.data = badForm.get('cadence', None)
        newRelayStream.offset.data = badForm.get('offset', None)
        newRelayStream.datatype.data = badForm.get('datatype', '')
        newRelayStream.description.data = badForm.get('description', '')
        newRelayStream.tags.data = badForm.get('tags', '')
        newRelayStream.url.data = badForm.get('url', '')
        newRelayStream.uri.data = badForm.get('uri', '')
        newRelayStream.headers.data = badForm.get('headers', '')
        newRelayStream.payload.data = badForm.get('payload', '')
        newRelayStream.hook.data = badForm.get('hook', '')
        newRelayStream.history.data = badForm.get('history', '')
        return newRelayStream

    # exampleStream = [Stream(streamId=StreamId(source='satori', author='self', stream='streamName', target='target'), cadence=3600, offset=0, datatype=None, description='example datastream', tags='example, raw', url='https://www.satorineuron.com', uri='https://www.satorineuron.com', headers=None, payload=None, hook=None, ).asMap(noneToBlank=True)]
    global firstRun
    theFirstRun = firstRun
    firstRun = False
    streamOverviews = (
        [model.miniOverview() for model in start.engine.models]
        if start.engine is not None else [])  # StreamOverviews.demo()
    start.openWallet()
    if start.vault is not None:
        start.openVault()
    return render_template('dashboard.html', **getResp({
        'firstRun': theFirstRun,
        'wallet': start.wallet,
        'vaultBalanceAmount': start.vault.balanceAmount if start.vault is not None else 0,
        'streamOverviews': streamOverviews,
        'configOverrides': config.get(),
        'paused': start.paused,
        'newRelayStream': present_stream_form(),
        'shortenFunction': lambda x: x[0:15] + '...' if len(x) > 18 else x,
        'quote': getRandomQuote(),
        'relayStreams':  # example stream +
        ([
            {
                **stream.asMap(noneToBlank=True),
                **{'latest': start.relay.latest.get(stream.streamId.topic(), '')},
                **{'late': start.relay.late(stream.streamId, timeToSeconds(start.cacheOf(stream.streamId).getLatestObservationTime()))},
                **{'cadenceStr': deduceCadenceString(stream.cadence)},
                **{'offsetStr': deduceOffsetString(stream.offset)}}
            for stream in start.relay.streams]
         if start.relay is not None else []),

        'placeholderPostRequestHook': """def postRequestHook(response: 'requests.Response'):
    '''
    called and given the response each time
    the endpoint for this data stream is hit.
    returns the value of the observation
    as a string, integer or double.
    if empty string is returned the observation
    is not relayed to the network.
    '''
    if response.text != '':
        return float(response.json().get('Close', -1.0))
    return -1.0
""",
        'placeholderGetHistory': """class GetHistory(object):
    '''
    supplies the history of the data stream
    one observation at a time (getNext, isDone)
    or all at once (getAll)
    '''
    def __init__(self):
        pass

    def getNext(self):
        '''
        should return a value or a list of two values,
        the first being the time in UTC as a string of the observation,
        the second being the observation value
        '''
        return None

    def isDone(self):
        ''' returns true when there are no more observations to supply '''
        return None

    def getAll(self):
        '''
        if getAll returns a list or pandas DataFrame
        then getNext is never called
        '''
        return None

""",
    }))


# @app.route('/fetch/balance', methods=['POST'])
# @authRequired
# def fetchBalance():
#    start.openWallet()
#    if start.vault is not None:
#    return 'OK', 200


@app.route('/pin_depin', methods=['POST'])
@authRequired
def pinDepinStream():
    # tell the server we want to toggle the pin of this stream
    # on the server that means mark the subscription as chosen by user
    # s = StreamId.fromTopic(request.data) # binary string actually works
    s = request.json
    payload = {
        'source': s.get('source', 'satori'),
        # 'pubkey': start.wallet.publicKey,
        'author': s.get('author'),
        'stream': s.get('stream', s.get('name')),
        'target': s.get('target'),
        # 'client': start.wallet.publicKey, # gets this from authenticated call
    }
    success, result = start.server.pinDepinStream(stream=payload)
    # return 'pinned' 'depinned' based on server response
    if success:
        return result, 200
    logging.error('pinDepinStream', s, success, result)
    return 'OK', 200


@app.route('/connections-status/refresh', methods=['GET'])
def connectionsStatusRefresh():
    start.connectionsStatusQueue.put(start.latestConnectionStatus)
    return str(start.latestConnectionStatus).replace("'", '"').replace(': True', ': true').replace(': False', ': false'), 200


@app.route('/connections-status')
def connectionsStatus():
    def update():
        while True:
            try:
                return_code = process.poll()
                if return_code is not None:
                    print(f'Satori exited with code {return_code}.')
                    break
                time.sleep(1)
            except KeyboardInterrupt:
                print("Shutting down monitor...")
                process.terminate()
                process.wait()
                return


if __name__ == "__main__":
    monitorAndRestartSatori()
