import threading
import queue
import time

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


HOST = "127.0.0.1"
PORT = 1507

log = init_log("call_prt")


class CallCab(threading.Thread):

    def __init__(self, call_module_path):
        super(CallCab, self).__init__()
        self.call_module_path = call_module_path
        self.stop = threading.Event()
        self.cli = Client(HOST, PORT)

    def run(self):
        while not self.stop.isSet():
            self.on_recv()

    def recvall(self, size):
        """ recieve all. """
        try:
            s = size
            buf = ""
            while True:
                b = self.cli.recv(s)
                buf = buf + b
                s = s - len(b)
                if s == 0 or not b:
                    return buf
        except Exception as ex:
            raise CommunicateException("RecvALL Error:%s" % ex)

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
                body = codec.decode(body[:-1])
            except Exception as ex:
                e = "Decode Request Message Body Error: %s" % ex
                log.error(e)
                raise ProtocolException(e)
        else:
            raise CommunicateException("size error: " + str(size))

        if _type == MSG_TYPE_REQUEST:
            if len(body) != 3:
                raise ProtocolException("Request Message Body Content Error")

            # break up the request
            req_id, func_name, params = body["id"], body["func"], body["params"]

            log.info("in %s(%s)" % (func_name, params))

            # get the result for the request
            res = None
            exp = None
            if func_name == "is_on_line":
                res = 1
            else:
                try:
                    # imort module
                    mod = __import__(self.call_module_path)
                    components = self.call_module_path.split('.')
                    for comp in components[1:]:
                        mod = getattr(mod, comp)
                    func = getattr(mod, func_name, None)

                    if func is not None:
                        if hasattr(func, "__call__"):
                            try:
                                res = func(*params)
                            except Exception as ex:
                                log.error("Error when execute func(%s): %s" % (func_name, ex))
                                raise UserException(str(ex))
                        else:
                            raise NoMethodException("% can not be callable" % func_name)
                    else:
                        raise NoMethodException("No function or attr %s" % func_name)
                except Exception as ex:
                    print (ex)
                    exp = ex

            # print "reqid, result: ", reqId, res
            log.info("out %s(%s)" % (func_name, params))

            if exp is None:
                reply_status = code.SUCCESS
                reply_msg = res
            else:
                reply_status = code.FAILED
                reply_msg = exp

            reply = Reply(req_id, reply_status, reply_msg)
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
