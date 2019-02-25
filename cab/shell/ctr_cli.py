import threading
import traceback
import queue
import time

from cab.utils.client import Client
from cab.utils.console import embed
from cab.utils.c_log import init_log
from cab.utils.machine_info import get_config, get_machine_id
from cab.services.protocol import (Protocol, Request, HeartBeat,
                                   Reply,
                                   MSG_TYPE_REPLY,
                                   CommunicateException,
                                   ProtocolException,
                                   UserException,
                                   NoMethodException,
                                   MAX_MESSAGE_LENGTH,
                                   MSG_TYPE_REQUEST)


__all__ = ["call_once", "CtrCli"]

cab_server = get_config("ckc").get("server", "cab_server")
cab_port = get_config("ckc").getint("server", "cab_port")
print("%s %s" % (cab_server, cab_port))

log = init_log("server_api")


def call_once(func, params=None, timeout=60):
    cli = Client(cab_server, cab_port)
    r = Request(func, params)
    _id, data = Protocol().request_to_raw(r)
    cli.send(data)
    print(cli.recv(80960))
    cli.close()

    return


class CtrCli(threading.Thread):

    def __init__(self):
        super(CtrCli, self).__init__()
        self.lock = threading.Lock()
        self.cli = Client(cab_server, cab_port)

    def call(self, func, params=None, timeout=60):
        with self.lock:
            r = Request(func, params)
            _id, data = Protocol().request_to_raw(r)
            self.cli.send(data)
            return self.on_recv()


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
        try:
            protocol = Protocol()
            head_size = protocol.get_head_size()
            head = self.recvall(head_size)
            if len(head) != head_size:
                raise CommunicateException("Connection closed by peer")

            _type, size, codec = protocol.parse_head(head)

            if size > 0 and size < MAX_MESSAGE_LENGTH:
                body = self.recvall(size)  # raise CommunicateException
                try:
                    body = codec.decode(body[:-4])
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
        except Exception as e:
            log.warning("on_recv: %s" % str(traceback.format_exc()))



if __name__ == "__main__":
    cc = CtrCli()
    embed()