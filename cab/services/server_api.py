import threading
import queue
import time

from cab.services.protocol import Protocol, Request
from cab.utils.client import Client
from cab.utils.c_log import init_log
# from cab.utils.machine_info import  get_server

__all__ = ["call_once", "CallServer"]

HOST = "127.0.0.1"
PORT = 1507

log = init_log("call_server")

def call_once(func, params=None, timeout=60):
    cli = Client(HOST, PORT)
    r = Request(func, params)
    _id, data = Protocol().request_to_raw(r)
    cli.send(data)
    cli.recv(timeout=6)
    cli.close()

    return


class CallServer(threading.Thread):

    def __init__(self, host, port):
        super(CallServer, self).__init__()
        self.cli = Client(HOST, PORT)
        self.task = queue.Queue()

    def call(self, func, params=None):
        r = Request(func, params)
        self.task.put(r)

    def run(self):
        recv_time_out = 60
        while True:
            try:
                request = self.task.get(timeout=1)
                while True:
                    _id, data = Protocol().request_to_raw(request)
                    try:
                        self.cli.send(data)
                        self.cli.recv(timeout=recv_time_out)
                    except Exception as e: 
                        log.warning(str(e))

            except queue.Empty:
                time.sleep(0.5)
            except Exception as e: 
                log.warning(str(e))


if __name__ =="__main__":
    call_once("test", {"t": 1})

