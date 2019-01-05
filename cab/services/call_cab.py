import threading
import traceback
import queue
import time
import json

from cab.services import code
from cab.services.protocol import (Protocol, Request,
                                   Reply,
                                   CommunicateException,
                                   ProtocolException,
                                   UserException,
                                   NoMethodException,
                                   MAX_MESSAGE_LENGTH,
                                   MSG_TYPE_REQUEST)
from cab.utils.client import Client
from cab.utils.c_log import init_log
# from cab.utils.machine_info import  get_server


# HOST = "127.0.0.1"
HOST = "127.0.0.1"
PORT = 1507

cab_host = "127.0.0.1"
cab_port = 1507 



log = init_log("call_cab")


class CallCab(threading.Thread):

    def __init__(self, call_module_path):
        super(CallCab, self).__init__()
        self.call_module_path = call_module_path
        self.stop = threading.Event()
        self.cli = Client(HOST, PORT)
        self.cab_cli = Client(HOST, PORT)

    def run(self):

        while not self.stop.isSet():
            try:
                self.on_recv()
            except CommunicateException as e:
                print(str(e))
                time.sleep(1)
                log.warning("retry remote server....")
            except Exception as e:
                log.warning("run: %s" % str(traceback.format_exc()))

            

    def recvall(self, size):
        """ recieve all. """
        try:
            s = size
            buf = ""
            while True:
                b = self.cli.recv(s, init_sock=True)
                buf = buf + b
                s = s - len(b)
                if s == 0 or not b:
                    return buf

        except Exception as ex:
            raise CommunicateException("RecvALL Error:%s" % ex)

    def _on_recv_body(self, protocol):
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
                body = codec.decode(body)
            except Exception as ex:
                e = "Decode Request Message Body Error: %s" % ex
                log.error(e)
                raise ProtocolException(e)
        else:
            raise CommunicateException("size error: " + str(size))
        
        return _type, body


    def on_recv(self):
        """ recieve request and return reply. """
        protocol = Protocol()
        _type, body = self._on_recv_body(protocol)
        
        if _type == MSG_TYPE_REQUEST:
            # break up the request
            req_id, func_name, params = body["id"], body["func"], body["params"]

            log.info("in %s(%s)" % (func_name, params))

            # get the result for the request
            reply_code = code.SUCCESS
            sub_data = ""
            if func_name == "is_on_line":
                pass
            else:
                try:
                    self.cab_cli.send(json.dumps({"func": func_name,
                        "params": params}))
                    sub_data = self.cab_cli.recv()
                
                except ConnectionRefusedError as e:
                    reply_code = code.UNAVALIABLE_SERVICE

                except Exception as ex:
                    log.warning(str(ex))
                    reply_code = code.FAILED

            # print "reqid, result: ", reqId, res
            log.info("out %s(%s)" % (func_name, params))

            reply_msg = code.CODE2MSG.get(reply_code)

            reply = Reply(req_id, reply_code, reply_msg, sub_data)
            msg = protocol.reply_to_raw(reply)
            # print "reply msg: ", msg
            self.cli.send(msg)  # CommunicateException
        else:
            log.error("Unknown Message Ignoring...")


if __name__ == "__main__":

    try:
        call_cab = CallCab("cab.ckservice.cab_api")
        call_cab.start()
    except Exception as ex:
        log.error("error in main: %s" % ex)
        time.sleep(5)
    call_cab.join()
