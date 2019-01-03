import asyncore
import traceback
import sys
import socket
from cab.utils.c_log import init_log
from cab.utils.utils import run_in_thread


__all__ = ["Server", "run_server"]

log = init_log("server", count=1)



class Server(asyncore.dispatcher):

    def __init__(self, address, read_data_handler=None):
        asyncore.dispatcher.__init__(self)
        self.read_data_handler = read_data_handler
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(address)
        self.address = self.socket.getsockname()
        log.info('binding to %s, %s' % (address[0], address[1]))
        self.listen(5)

    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        if client_info is not None:
            log.info('handle_accept:  %s, %s' %
                     (client_info[0], client_info[1]))
            ClientHandler(client_info[0], client_info[
                          1], self.read_data_handler)



class ClientHandler(asyncore.dispatcher):

    def __init__(self, sock, address, read_data_handler=None):
        asyncore.dispatcher.__init__(self, sock)
        self.data_to_write = ""
        self.data = ""
        self.read_data_handler = read_data_handler

    def writable(self):
        return (len(self.data_to_write)>0)

    def handle_write(self):
        try:
            try:
                sent = self.send(self.data_to_write)
            except UnicodeDecodeError:
                sent = self.send(self.data_to_write)
            log.info("send: %s" % self.data_to_write[:sent])
            self.data_to_write = self.data_to_write[sent:]
        except Exception:
            log.warning("send error: %s" % str(traceback.format_exc()))
            raise

    def handle_read(self):

        if self.read_data_handler:
            # # !!!!! EAXAMPLE - ECHO
            self.read_data_handler(self)
        else:
            self.default_read_data_handler(self)

    def handle_close(self):
        log.info('handle_close()')
        self.close()

    def default_read_data_handler(self, client):
        #TODO: not safe
        data = self.recv(8096)
        client.data_to_write = data
        print("data_to_write:%s" % client.data_to_write)


@run_in_thread
def run_server():
    asyncore.loop()


def test_server(port=1507):
    HOST = '0.0.0.0'
    s = Server((HOST, port))
    asyncore.loop()

if __name__ == '__main__':
    test_server()

