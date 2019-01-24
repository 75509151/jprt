import threading

import traceback
import queue
import time
import json
import socket

from cab.services import code
from cab.services.protocol import (Protocol, Request,
                                   Reply, HeartBeat,
                                   CommunicateException,
                                   ProtocolException,
                                   UserException,
                                   NoMethodException,
                                   MAX_MESSAGE_LENGTH,
                                   MSG_TYPE_REQUEST)
from cab.utils.client import Client
from cab.utils.c_log import init_log
from cab.utils.utils import run_in_thread
from cab.utils.machine_info import get_config, get_machine_id


r2c_server = get_config("ckc").get("server", "r2c_server")
r2c_port = get_config("ckc").getint("server", "r2c_port")

cab_host = get_config("ckc").get("server", "cab_server")
cab_port = get_config("ckc").getint("server", "cab_port")

log = init_log("call_cab")


class CallCab(threading.Thread):

    def __init__(self, call_module_path):
        super(CallCab, self).__init__()
        self.lock = threading.Lock()
        self.call_module_path = call_module_path
        self.stop = threading.Event()
        self.remote_cli = Client(r2c_server, r2c_port)
        # self.remote_cli = Client("127.0.0.1", 1507)


    def _send_heardbeat(self):
        r = HeartBeat(get_machine_id())
        data = Protocol().heart_to_raw(r)
        self.send_to_remote(data)

    @run_in_thread
    def _heart_beat(self):
        while True:
            try:
                self._send_heardbeat()
            except Exception as e:
                log.warning("heatbeat: %s" % str(e))
                time.sleep(1)
            else:
                time.sleep(60)

    def send_to_remote(self, data):
        with self.lock:
            self.remote_cli.send(data)


    def run(self):
        self._heart_beat()
        while not self.stop.isSet():
            try:
                log.info("recv begin....")
                self.on_recv()
            except CommunicateException as e:
                log.warning("retry remote server....: %s" % str(traceback.format_exc()))
                self.remote_cli.connect(timeout=None)
                try:
                    self._send_heardbeat()
                except Exception as e:
                    log.warning("connect send heart: %s" % str(e))
            except Exception as e:
                log.warning("run: %s" % str(traceback.format_exc()))

    def recvall(self, size):
        """ recieve all. """
        try:
            s = size
            buf = b""
            while True:
                b = self.remote_cli.recv(s)
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
                body = codec.decode(body[:-4])
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
            reply_code = code.SUCCESS
            # break up the request
            req_id, func_name, params = body["id"], body["func"], body["params"]

            log.info("in %s(%s)" % (func_name, params))

            # get the result for the request
            sub_data = None
            try:
                cab_cli = Client(cab_host, cab_port)
                cab_cli.send(json.dumps({"func": func_name,
                                                "params": params}).encode())
                recv_data = cab_cli.recv(80960)

                recv_data_dic = json.loads(recv_data)

                reply_code = recv_data_dic.get("code")
                sub_data = recv_data_dic.get("sub_data")

            except ConnectionRefusedError as e:
                reply_code = code.UNAVALIABLE_SERVICE

            except Exception as ex:
                log.warning(str(traceback.format_exc()))
                reply_code = code.FAILED

            # print "reqid, result: ", reqId, res
            log.info("out %s(%s)" % (func_name, params))

            reply_msg = code.CODE2MSG.get(reply_code, "Unknown Error")
            sub_data = json.dumps({}) if not sub_data else json.dumps(sub_data)
            reply = Reply(req_id, reply_code, reply_msg, sub_data)

            msg = protocol.reply_to_raw(reply)
            # print "reply msg: ", msg
            self.send_to_remote(msg)
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
