import time

from cab.utils.server import Server, run_server
from cab.services.protocol import (Protocol, Request,
                                   Reply,
                                   CommunicateException,
                                   ProtocolException,
                                   UserException,
                                   NoMethodException,
                                   MAX_MESSAGE_LENGTH,
                                   MSG_TYPE_REQUEST)


class ApiServer(Server):

    def __init__(self, address):
        super(ApiServer, self).__init__(address)
        self.read_data_handler = self.reply_cli

    def reply_cli(self, cli, msg):
        reply_id = "000001"
        reply_code = 0
        reply_msg = "Success"
        data = {"sub_code": 1,
                "msg": "ok"}
        reply = Reply(reply_id, reply_code, reply_msg, data)
        protocol = Protocol()
        msg = protocol.reply_to_raw(reply)
        cli.send(msg)


if __name__ == "__main__":
    api_server = ApiServer(("127.0.0.1", 1507))
    run_server()
    while True:
        time.sleep(2)
    
