import time

from cab.services import code
from cab.utils.server import Server, run_server, ClientHandler
from cab.services.protocol import (Protocol, Request,
                                   Reply,
                                   CommunicateException,
                                   ProtocolException,
                                   UserException,
                                   NoMethodException,
                                   MAX_MESSAGE_LENGTH,
                                   MSG_TYPE_REQUEST)

from cab.utils.c_log import init_log

log = init_log("server", count=1)

class ApiClient(ClientHandler):

    def __init__(self, sock, address):
        super(ApiClient, self).__init__(sock, address)

    def handle_read(self):
        self.on_recv()


    def recvall(self, size):
        """ recieve all. """
        try:
            s = size
            buf = b""
            while True:
                b = self.recv(s)
                buf = buf + b
                s = s - len(b)
                if s == 0 or not b:
                    return buf
        except Exception as ex:
            raise CommunicateException("RecvALL Error:%s" % ex)

    def reply_cli(self):
        try:
            reply_id = "000001"
            reply_code = 0
            reply_msg = "Success"
            data = {"sub_code": 1,
                    "msg": "ok"}
            reply = Reply(reply_id, reply_code, reply_msg, data)
            protocol = Protocol()
            msg = protocol.reply_to_raw(reply)
            self.send(msg)
        except Exception as e:
            log.warning("reply_cli: %s" % str(e))


    def on_recv(self):
        """ recieve request and return reply. """
        protocol = Protocol()
        head_size = protocol.get_head_size()
        head = self.recvall(head_size)
        if len(head) != head_size:
            raise CommunicateException("Connection closed by peer")

        _type, size, codec = protocol.parse_head(head)

        if size > 0 and size < MAX_MESSAGE_LENGTH:
            # print "request size:", size
            body = self.recvall(size)  # raise CommunicateException
            # print "request body", body
            try:
                body = codec.decode(body[:-4])
            except Exception as ex:
                e = "Decode Request Message Body Error: %s" % ex
                log.error(e)
                raise ProtocolException(e)
        else:
            raise CommunicateException("size error: " + str(size))

        if _type == MSG_TYPE_REQUEST:
            # break up the request
            req_id, func_name, params = body["id"], body["func"], body["params"]

            log.info("in %s(%s)" % (func_name, params))
            self.reply_cli()
            log.info("out %s(%s)" % (func_name, params))





class ApiServer(Server):

    def __init__(self, address, client):
        super(ApiServer, self).__init__(address, client)


if __name__ == "__main__":
    api_server = ApiServer(("127.0.0.1", 1507), ApiClient)
    run_server()
    while True:
        time.sleep(2)
