import asyncore
import socket
import platform
from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, EINVAL, \
    ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EBADF, ECONNABORTED, EPIPE, EAGAIN, \
    errorcode
from .c_log import init_log
from .utils import run_in_thread


__all__ = ["Server", "run_server"]

log = init_log("server", count=1)


_DISCONNECTED = frozenset((ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED,
                           EPIPE,
                           EBADF))


class FixDispatcher(asyncore.dispatcher):
    def __init__(self, sock=None, map=None):
        asyncore.dispatcher.__init__(self, sock, map)
        if platform.python_version().startswith("2.7"):
            self.recv = self.fix_recv

    def fix_recv(self, buffer_size):
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return ''
            else:
                return data
        except socket.error, why:
            # winsock sometimes throws ENOTCONN
            if why.args[0] in _DISCONNECTED:
                self.handle_close()
                return ''
            elif why.args[0] in (EAGAIN, EWOULDBLOCK):
                return ''
            else:
                raise


class Server(FixDispatcher):

    def __init__(self, address, read_data_handler=None):
        FixDispatcher.__init__(self)
        self.read_data_handler = read_data_handler
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(address)
        self.address = self.socket.getsockname()
        log.info('binding to %s, %s' % (address[0], address[1]))
        # print self.address
        self.listen(5)

    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        if client_info is not None:
            log.info('handle_accept:  %s, %s' %
                     (client_info[0], client_info[1]))
            ClientHandler(client_info[0], client_info[
                          1], self.read_data_handler)


class ClientHandler(FixDispatcher):

    def __init__(self, sock, address, read_data_handler=None):
        FixDispatcher.__init__(self, sock)
        self.data_to_write = []
        self.data = ""
        self.read_data_handler = read_data_handler

    def writable(self):
        return bool(self.data_to_write)

    def handle_write(self):
        data = self.data_to_write.pop(0)
        self.sendall(data)

        # log.debug('handle_write() -> (%d) "%s"', sent, data[:sent].rstrip())
        log.info("send: %s" % data)

    def handle_read(self):
        self.data += self.recv(8192)
        if self.data:
            log.info("handle_read: %s" % self.data)

            # # !!!!! EAXAMPLE - ECHO
            if self.read_data_handler:
                self.read_data_handler(self)
            else:
                self.default_read_data_handler(self)

    def handle_close(self):
        log.info('handle_close()')
        self.close()

    def default_read_data_handler(self, client):
        if client.data:
            client.data_to_write.append(client.data)
            print "data_to_write:%s" % client.data_to_write
            client.data = ''


@run_in_thread
def run_server():
    asyncore.loop()


def main():
    HOST = '0.0.0.0'
    PORT = 1507
    s = Server((HOST, PORT))
    asyncore.loop()


if __name__ == '__main__':
    """python -m box.cutils.server"""
    main()

