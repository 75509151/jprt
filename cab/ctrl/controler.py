import sys
import json
import time
import threading
import traceback
import signal

from cab.utils.server import Server, run_server, ClientHandler
from cab.utils.c_log import init_log
from cab.utils.console import embed
from cab.utils import constant as cst
from cab.db.db_pool import DB_POOL as DBP
from cab.ctrl.prt_manager import PrtManager
from cab.services.server_api import CallServer, call_once
from cab.services import code
from cab.utils.utils import get_extern_if, extern_if


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

    def _do_func(self, func, params):
        return func(params)

    def handle_read(self):
        code = None
        data = self.recv(80960)
        try:
            func, params = self._get_func(data)

            sub_data = self._do_func(func, params)
            self.send(json.dumps(sub_data))
            return
        except code.InternalErr:
            code = code.INTERNAL_ERROR
        except code.NoSuchApiErr:
            code = code.UNKNOWN_API
        except Exception as e:
            log.warning(str(e))
            code = code.INTERNAL_ERROR

        self.send(json.dumps({"code": code}))
        


class ApiServer(Server):

    def __init__(self, address, client, ctrl):
        super(ApiServer, self).__init__(address, client, ctrl)
        self.ctrl = ctrl

    def handle_accept(self):
        client_info = self.accept()
        if client_info is not None:
            self.client(client_info[0], client_info[1], self.ctrl)


class Controler(object):
    def __init__(self):
        super(Controler, self).__init__()
        self.log = log
        self._stop_event = threading.Event()
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.prt_manager = PrtManager()

    def exit_gracefully(self, signum, frame):
        self._stop_event.set()
        log.info("catch signal: %s, %s" % (signum, frame))

    def init_server(self):
        self.serv = ApiServer(("0.0.0.0", cst.G_CTRL_PORT), ApiClient, self)

    def before_work(self):
        try:
            if self.prt_manager.need_install():
                self.prt_manager.install_printer()
            self.prt_manager.report()
        except Exception as e:
            log.warning(str(traceback.format_exc()))

    @extern_if
    def print_file(self, **kw):
        return {}

    def run(self, test=False):
        try:
            log.info("start".center(100, '-'))
            self.before_work()

            self.init_server()
            run_server()

            if test:
                embed()
            else:
                interval_time = 5 * 60
                while not self._stop_event.is_set():
                    time.sleep(interval_time)
                    try:
                        self.prt_manager.open()
                    except Exception as e:
                        log.warning(str(e))

        except Exception as e:
            log.error("exit unexpect: %s" % str(traceback.format_exc()))


if __name__ == "__main__":
    ctrl = Controler()
    test = True if len(sys.argv) >= 2 and sys.argv[1] == "test" else False
    ctrl.run(test)
