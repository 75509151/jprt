import asyncore
import traceback
import sys
import socket
from cab.utils.c_log import init_log
from cab.utils.utils import run_in_thread


__all__ = ["Server", "run_server", "ClientHandler"]

log = init_log("server", count=1)



class Server(asyncore.dispatcher):

    def __init__(self, address, client=None):
        asyncore.dispatcher.__init__(self)
        self.client = ClientHandler if not  client  else client
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
            self.client(client_info[0], client_info[1])



class ClientHandler(asyncore.dispatcher):

    def __init__(self, sock, address):
        asyncore.dispatcher.__init__(self, sock)
        self.data_to_write = b""
        self.data = b""

    def writable(self):
        return (len(self.data_to_write)>0)

    def handle_write(self):
        #TODO: unsafe
        try:
            sent = self.send(self.data_to_write)
            self.data_to_write = self.data_to_write[sent:]
        except Exception as e:
            log.warning("send error: %s" % str(traceback.format_exc()))
            raise e

    def handle_read(self):
        data = self.recv(8096)
        if not data:
            return
        self.data_to_write+=data
        print("data_to_write:%s" % self.data_to_write)


    def handle_close(self):
        log.info('handle_close()')
        self.close()



@run_in_thread
def run_server():
    asyncore.loop()


def test_server(port=1507):
    HOST = '0.0.0.0'
    s = Server((HOST, port))
    asyncore.loop()

if __name__ == '__main__':
    test_server()

