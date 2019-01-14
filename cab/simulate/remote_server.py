import time
import traceback

from cab.services import code
from cab.utils.machine_info import get_config
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

log = init_log("remote_server", count=1)

c2r_server = get_config("ckc").get("server", "c2r_server") 
c2r_port = get_config("ckc").getint("server", "c2r_port") 

class ApiClient(ClientHandler):

    def __init__(self, sock, address):
        super(ApiClient, self).__init__(sock, address)

    def handle_read(self):
        self.on_recv()

    def recvall(self, size, timeout=60):
        recv_len = 0
        data = b""
        while recv_len < size:
            try:
                data += self.recv(size - recv_len)
                recv_len = len(data)
            except BlockingIOError:
                pass

        return data

    def reply_cli(self, req_id, func, params):
        try:
            reply_id = req_id
            reply_code = 0
            reply_msg = "Success"
            simulate_func = getattr(self, func, None)
            data = simulate_func(params) if simulate_func else {}
            reply = Reply(reply_id, reply_code, reply_msg, data)
            protocol = Protocol()
            msg = protocol.reply_to_raw(reply)
            self.send(msg)
            print("send: %s" % msg)
            log.info("send: %s" % msg)
        except Exception as e:
            log.warning("reply_cli: %s" % str(e))

    def register(self, params):
        mac = params["mac"]
        machine_id = params["machine_id"]
        data = {"status": 0,
                "machine_id": "001",
                "info": ""}
        return data

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
                    print("recv raw: %s" % body)
                    body = codec.decode(body[:-4])
                    log.info("recv: %s" % body)
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
                self.reply_cli(req_id, func_name, params)
                log.info("out %s(%s)" % (func_name, params))
        except Exception as e:
            log.warning("on_recv: %s" % str(traceback.format_exc()))


class ApiServer(Server):

    def __init__(self, address, client):
        super(ApiServer, self).__init__(address, client)


if __name__ == "__main__":

    api_server = ApiServer(("127.0.0.1", c2r_port), ApiClient)
    run_server()
    while True:
        time.sleep(2)
