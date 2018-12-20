import socket
import os
import traceback
import select

from cab.utils.c_log import init_log

_log = init_log("client", count=1)


class Client(object):

    def __init__(self, serv_addr, serv_port, log=None):
        self.serv_addr = serv_addr
        self.serv_port = serv_port
        self.sock = None
        self.connected = False
        self.log = log if log else _log

    def init_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect((self.serv_addr, self.serv_port))
        self.log.debug("connected ")

    def send(self, data):
        if not self.sock:
            self.init_sock()
        try:
            self.sock.sendall(data)
            self.log.info("send: %s " % data)
        except Exception as e:
            raise e

    def recv(self, timeout=None):

        fd_in, fd_out, fd_err = select.select((self.sock,), (), (), timeout)
        if self.sock in fd_in:
            data = self.sock.recv(80960)
            self.log.info("recv: %s" % data)
            return data
        return None

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


if __name__ == '__main__':

    import json
    c = Client("127.0.0.1", 1507)
    while True:
        # c.send(json.dumps({"t": 1}).encode(encoding='utf_8', errors='strict'))
        c.send(json.dumps({"t": 1}).encode())
        c.send("1212".encode())
        print("recv: %s" % c.recv())
        import time
        time.sleep(1)
