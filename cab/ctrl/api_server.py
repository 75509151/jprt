import sys
import json
import queue
import time
import threading
import traceback
from cab.services import code
from cab.utils.utils import get_extern_if
from cab.utils.console import embed
from cab.utils.c_log import init_log

from cab.utils.server import Server, run_server, ClientHandler

log = init_log("ctl")

class ApiClient(ClientHandler):
    def __init__(self, sock, address, ctrl):
        super(ApiClient, self).__init__(sock, address)
        self.ctrl = ctrl

    def _get_func(self, data):
        try:
            data = json.loads(data)
        except ValueError as e:
            log.warning("could not decoded: %s" % str(data))
            raise code.InternalErr("")

        func = get_extern_if(self.ctrl, data["func"])
        if not func:
            raise code.NoSuchApiErr(data["func"])
        return func, data["params"]


    def handle_read(self):
        err_no = 0
        sub_data = {}

        data = self.recv(80960)
        if not data:
            return
        log.info("recv: %s" % data)
        try:
            func, params = self._get_func(data)

            sub_data = func(**params)
        except code.InternalErr as e:
            sub_data["sub_code"] = e.code
            sub_data["msg"] = e.msg

        except code.ExternalErr as e:
            err_no = e.code

        except Exception as e:
            log.warning(str(traceback.format_exc()))
            err_no = code.INTERNAL_ERROR

        try:
            self.send(json.dumps({"code": err_no,
                                "sub_data": sub_data}).encode())
        except Exception as e:
            log.warning("replay err: %s" % str(e))



class ApiServer(Server):

    def __init__(self, address, client, ctrl):
        super(ApiServer, self).__init__(address, client)
        self.ctrl = ctrl

    def handle_accept(self):
        try:
            client_info = self.accept()
            if client_info is not None:
                self.client(client_info[0], client_info[1], self.ctrl)
        except Exception as e:
            log.warning("accept: %s" % str(e))


if __name__ == "__main__":
    ser= ApiServer(("0.0.0.0", 1508), ApiClient, None)
    run_server()
    while True:
        time.sleep(1)

