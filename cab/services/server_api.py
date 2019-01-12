import threading
import queue
import time

from cab.utils.client import Client
from cab.utils.console import embed
from cab.utils.c_log import init_log
from cab.utils.machine_info import get_config
from cab.services.protocol import (Protocol, Request,
                                   Reply,
                                   MSG_TYPE_REPLY,
                                   CommunicateException,
                                   ProtocolException,
                                   UserException,
                                   NoMethodException,
                                   MAX_MESSAGE_LENGTH,
                                   MSG_TYPE_REQUEST)


__all__ = ["call_once", "CallServer"]

if get_config("ckc").get("main", "test") == "False":
    HOST = "127.0.0.1"
    PORT = 5525
else:
    HOST = "127.0.0.1"
    PORT = 5525

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

    def __init__(self):
        super(CallServer, self).__init__()
        self.lock = threading.Lock()
        self.cli = Client(HOST, PORT)
        self.task = queue.Queue()

    def call(self, func, params=None, timeout=60):
        with self.lock:
            r = Request(func, params)
            _id, data = Protocol().request_to_raw(r)
            self.cli.send(data)
            return self.on_recv()

    def call_async(self, func, params=None):
        r = Request(func, params)
        self.task.put(r)

    def recvall(self, size):
        """ recieve all. """
        try:
            s = size
            buf = b""
            while True:
                b = self.cli.recv(s)
                buf = buf + b
                s = s - len(b)
                if s == 0 or not b:
                    return buf
        except Exception as ex:
            raise CommunicateException("RecvALL Error:%s" % ex)

    def on_recv(self):
        """ recieve request and return reply. """
        protocol = Protocol()
        head_size = protocol.get_head_size()
        head = self.recvall(head_size)
        if len(head) != head_size:
            raise CommunicateException("Connection closed by peer")

        _type, size, codec = protocol.parse_head(head)

        if size > 0 and size < MAX_MESSAGE_LENGTH:
            body = self.recvall(size)  # raise CommunicateException
            try:
                body = codec.decode(body)
            except Exception as ex:
                e = "Decode Request Message Body Error: %s" % ex
                log.error(e)
                raise ProtocolException(e)
        else:
            raise CommunicateException("size error: " + str(size))
        
        if _type == MSG_TYPE_REPLY:
            log.info("recv : %s" % body)
        else:
            log.error("Unknown Message Ignoring...")
        return body

 

    def run(self):
        recv_time_out = 60
        while True:
            try:
                request = self.task.get(timeout=1)
                _id, data = Protocol().request_to_raw(request)
                with self.lock:
                    while True:
                        try:
                            self.cli.send(data)
                            break
                        except Exception as e: 
                            log.warning(str(e))
                            time.sleep(1)
                    self.on_recv()

            except queue.Empty:
                time.sleep(0.5)
            except Exception as e: 
                log.warning(str(e))


if __name__ =="__main__":
    # call_once("test", {"t": 1})
    call_server = CallServer()
    call_server.call("register", params={"num": 4, "path": "/doc/test.txt"})
    embed()
    

