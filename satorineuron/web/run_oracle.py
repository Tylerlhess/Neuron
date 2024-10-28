from oracle.oracle import Oracle
import threading
from satorineuron import logging
import time

if __name__ == "__main__":
    while True:
        try:
            oracle = Oracle()
            threading.Thread(target=oracle.run, args=([24621])).start()
                    
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

