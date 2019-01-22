import socket
import time
import os
import traceback
import select
import threading

from cab.utils.c_log import init_log

_log = init_log("client", count=1)


class Client(object):
    # TODO:

    def __init__(self, serv_addr, serv_port, log=None):
        self.lock = threading.Lock()
        self.serv_addr = serv_addr
        self.serv_port = serv_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connected = False
        self.log = log if log else _log
        try:
            self.connect(timeout=1)
        except Exception as e:
            pass

    def _connect(self):
        try:
            self.sock.connect((self.serv_addr, self.serv_port))
            self.connected = True
            self.log.info("connected ")
        except socket.error as e:
            self.connected = False
            self.log.warning("connect failed: %s" % str(e))


    def connect(self, timeout=1):
        with self.lock:
            if timeout is None:
                while self.connected is False:
                    self._connect()
                    time.sleep(2)
            else:
                start = time.time()
                while self.connected is False and time.time() - start < timeout:
                    self._connect()
                    time.sleep(2)


    def send(self, data, retry=3):
        with self.lock:
            try:
                ret = self.sock.sendall(data)
                self.log.info("send: %s " % data)
                return ret
            except socket.error as e:
                self.connected = False
                self.log.warning("send failed: %s" % str(e))
                raise e


    def recv(self, size):
        try:
            return self.sock.recv(size)
        except socket.error as e:
            self.connected = False
            self.log.warning("recv failed: %s" % str(e))
            raise e



    def readable(self, timeout=None):
        fd_in, fd_out, fd_err = select.select((self.sock,), (), (), timeout)
        return True if self.sock in fd_in else False

    def recv_with_timeout(self, size=80960, timeout=None):
        fd_in, fd_out, fd_err = select.select((self.sock,), (), (), timeout)
        if self.sock in fd_in:
            data = self.sock.recv(size)
            self.log.info("recv: %s" % data)
            return data
        return None

    def close(self):
        self.sock.close()


if __name__ == '__main__':

    import json
    c = Client("127.0.0.1", 1507)
    i = 0
    while True:
        # c.send(json.dumps({"t": 1}).encode(encoding='utf_8', errors='strict'))
        c.send(json.dumps({"t": 1}).encode())
        print("recv: %s %s" % (i, c.recv(8096)))
        i += 1
        import time
        time.sleep(1)
