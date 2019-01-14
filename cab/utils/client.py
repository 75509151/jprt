import socket
import os
import traceback
import select
import threading

from cab.utils.c_log import init_log

_log = init_log("client", count=1)



class Client(object):
    #TODO:

    def __init__(self, serv_addr, serv_port, log=None):
        self.lock = threading.Lock()
        self.serv_addr = serv_addr
        self.serv_port = serv_port
        self.sock = None
        self.connected = False
        self.log = log if log else _log

    def init_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.connect((self.serv_addr, self.serv_port))
            self.log.debug("connected ")
        except socket.error as e:
            self.sock = None
            self.log.warning("connect failed: %s" % str(e))
            raise e

    def send(self, data, retry=3):
        with self.lock:
            err = None
            for i in range(retry):
                try:
                    if not self.sock:
                        self.init_sock()
                    ret = self.sock.sendall(data)
                    self.log.info("send: %s " % data)
                    return ret
                except socket.error as e:
                    err = e
                    self.sock = None
                    self.log.warning("send failed %s: %s, %s" % (i, data, str(e)))
                    continue

                except Exception as e:
                    self.log.warning("send failed %s: %s, %s" % (i, data, str(e)))
                    err = e
                    break
            raise err

    def recv(self, size):
        return self.sock.recv(size)


    def recv_with_timeout(self, size=80960,timeout=None):
        fd_in, fd_out, fd_err = select.select((self.sock,), (), (), timeout)
        if self.sock in fd_in:
            data = self.sock.recv(size)
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
    i = 0
    while True:
        # c.send(json.dumps({"t": 1}).encode(encoding='utf_8', errors='strict'))
        c.send(json.dumps({"t": 1}).encode())
        print("recv: %s %s" % (i, c.recv(8096)))
        i += 1
        import time
        time.sleep(1)
