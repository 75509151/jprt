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
#from cab.db.db_pool import DB_POOL as DBP
from cab.ctrl.prt_manager import PrtManager
from cab.services.server_api import CallServer, call_once
from cab.services import code
from cab.utils.utils import (get_extern_if, 
        extern_if, 
        download_file, 
        upload_file,
        get_udisk)

from cab.prts.prt_exceptions import PrtError


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
        err_no = 0
        sub_data = {}

        data = self.recv(80960)
        try:
            func, params = self._get_func(data)

            sub_data = self._do_func(func, params)
        except code.InternalErr as e:
            sub_data["sub_code"] = e.code
            sub_data["msg"] = e.msg

        except code.ExternalErr as e:
            err_no = e.code

        except Exception as e:
            log.warning(str(e))
            err_no = code.INTERNAL_ERROR

        self.send(json.dumps({"code": err_no,
                              "sub_data": sub_data}))


class ApiServer(Server):

    def __init__(self, address, client, ctrl):
        super(ApiServer, self).__init__(address, client)
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

    # def _print_file_check_params()

    @extern_if
    def print_file(self, **kw):
        try:
            doucument_or_url, callback_url, trans_id = kw["file"], kw["callback_url"], kw["trans_id"]
        except KeyError as e:
            raise code.MissFieldsErr(str(e))
        num = kw.get("num", 1)
        sides = kw.get("sides", "one-sided")
        colorful = kw.get("colorful", False)
        udisk = kw.get("udisk", False)

        sub_data = {"sub_code": 0,
                    "msg": "Printing"}

        document = doucument_or_url if udisk else download_file(doucument_or_url)

        try:
            self.prt_manager.print_file(document, num, colorful, sides)
        except PrtError as e:
            sub_data["code"] = e.code
            sub_data["msg"] = e.msg

        return sub_data

    @extern_if
    def open_door(self, **kw):
        sub_data = {"sub_code": 0,
                    "msg": "Success"}
        return sub_data

    @extern_if
    def get_printer_status(self, **kw):
        sub_data = {"sub_code": 0,
                    "msg": ""}
        try:
            _, status = self.prt_manager.query(status=True)
            sub_data["msg"] = status
        except PrtError as e:
            sub_data["code"] = e.code
            sub_data["msg"] = e.msg

        return sub_data

    @extern_if
    def upload_file(self, **kw):
        sub_data = {"sub_code": 0,
                    "msg": "Success"}
        try:
            src, dst = kw["src"], kw["dst"]
        except KeyError as e:
            raise code.MissFieldsErr(str(e))
        
        server = "{user}@{ip}".format("pi", "127.0.0.1")
        dst = "{server}:{dst}".format(server, dst)

        upload_file(src, dst)

        return sub_data

    @extern_if
    def get_udisk_info(self, **kw):
        sub_data = {"sub_code": 0,
                    "msg": []}
        try:
            path = kw["path"]
        except KeyError as e:
            raise code.MissFieldsErr(str(e))

        files = get_udisk(path) 

        if files is None:
            raise code.FileUnEixstError()

        sub_data["msg"] = files
        
        return sub_data



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
