import sys
import json
import queue
import os
import time
import threading
import traceback
import signal
import uuid

from cab.utils.server import Server, run_server, ClientHandler
from cab.utils.c_log import init_log
from cab.utils.console import embed
from cab.utils import constant as cst
from cab.db.db_pool import DB_POOL
from cab.ctrl.prt_manager import PrtManager, wait_job_done
from cab.services.web_api import (register, report_printer_params, report_printer_status,
                                  upload_file,
                                  print_notify)
# from cab.services.server_api import CallServer, call_once
from cab.ctrl.api_server import ApiServer, ApiClient
from cab.services.call_cab import CallCab
from cab.services import code
from cab.utils.utils import (get_extern_if,
                             run_in_thread,
                             extern_if,
                             download_file,
                             get_udisk,
                             get_udisk_path)

from cab.prts.prt_exceptions import PrtError
from cab.utils.machine_info import (get_machine_id,
                                    get_machine_type,
                                    get_config,
                                    get_hw_addr,
                                    set_machine_id)
from cab.ext.dc_door import DCDoor, SDCDoor


log = init_log("ctl")

cab_port = get_config("ckc").getint("server", "cab_port")


class Controler(object):
    def __init__(self):
        super(Controler, self).__init__()
        self.log = log
        self.test = get_config("ckc").get("main", "test") == "false"
        self.call_cab = CallCab("")
        self._stop_event = threading.Event()
        self.job_queue = queue.Queue()
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.door = DCDoor() if not self.test else SDCDoor()
        self.prt_manager = PrtManager()
        self.prt_st = None

    def exit_gracefully(self, signum, frame):
        self._stop_event.set()
        log.info("catch signal: %s, %s" % (signum, frame))

    def init_server(self):
        self.serv = ApiServer(("127.0.0.1", cab_port), ApiClient, self)

    def before_work(self):
        self.register()
        self.prt_manager.cancel_uncomplete_jobs()

        self.call_cab.start()
        first_install = False
        try:
            if self.prt_manager.need_install():
                first_install = True
                self.prt_manager.install_printer()
        except Exception as e:
            log.warning(str(traceback.format_exc()))

        if first_install:
            while True:
                params_reported, _ = self.report(params=True)
                if params_reported:
                    log.info("report params Success")
                    return
                time.sleep(5)
        else:
            self.report(params=True)

    @run_in_thread
    def jobs_report(self):
        def _report(trans_id, code):
            while True:
                res = print_notify(trans_id, code=code)
                if res["status"] in (0, 1):
                    with DB_POOL as db:
                        db.del_trans(trans_id)
                    return
        try:
            with DB_POOL as db:
                trans_list = db.get_trans()
                for trans in trans_list:
                    _report(trans["trans_id"], "FAILED")
        except Exception as e:
            log.warning("clear old trans: %s" % str(e))

        while True:
            try:
                job, trans_id = self.job_queue.get()
                job = wait_job_done(job)
                code = "SUCCESS" if job else "FAILED"
                _report(trans_id, code)
            except Exception as e:
                log.warning("jobs report: %s" % str(e))

    @extern_if
    def print_file(self, **kw):
        try:
            self.prt_manager.open()
        except Exception as e:
            log.info("prt open: %s" % str(e))
            raise code.PrtLostError()
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

        # with DB_POOL as db:
        # db.add_trans(trans_id)
        try:
            dst_dir = "/tmp/"
            suffix = os.path.splitext(doucument_or_url)[1]

            new_name = "%s%s" % (str(uuid.uuid4()),suffix)
            if udisk:
                udisk_paths = get_udisk_path(abs_path=True)
                if not udisk_paths:
                    raise code.FileUnEixstError()

                udisk_path = udisk_paths[0]
                udisk_file = os.path.join(udisk_path, doucument_or_url)
                document = os.path.join(dst_dir, new_name)
                cmd = "cp '%s' '%s'" % (udisk_file, document)
                ret = os.system(cmd)
                if ret != 0:
                    log.warning("cp failed: %s , %s" % (cmd, ret))

            else:
                new_file = os.path.join(dst_dir, new_name)
                document = download_file(doucument_or_url, new_file)

            if not os.path.isfile(document):
                raise code.FileUnEixstError()

            job = self.prt_manager.print_file(document, num, colorful, sides)
            self.job_queue.put((job, trans_id))

        except PrtError as e:
            sub_data["code"] = e.code
            sub_data["msg"] = e.msg

        return sub_data

    @extern_if
    def open_door(self, **kw):
        sub_data = {"sub_code": 0,
                    "msg": "Success"}
        try:
            if not self.door.open_door():
                sub_data["sub_code"] = 1
                sub_data["msg"] = "Failed"
        except Exception as e:
            sub_data["sub_code"] = 1
            sub_data["msg"] = str(e)

        return sub_data

    @extern_if
    def get_printer_status(self, **kw):
        sub_data = {"sub_code": 0,
                    "msg": ""}
        try:
            _, status = self.prt_manager.query()
            st = {"status-code": status["status-code"],
                  "status-desc": status["status-desc"],
                  "device-uri": status["device-uri"],
                  "device-state": status["device-state"],
                  "error-state": status["error-state"]}
            sub_data["msg"] = st
        except PrtError as e:
            sub_data["code"] = e.code
            sub_data["msg"] = e.msg

        return sub_data

    @extern_if
    def upload_file(self, **kw):
        try:
            src = kw["src"]
        except KeyError as e:
            raise code.MissFieldsErr(str(e))

        sub_data = {"sub_code": 0,
                    "msg": "Success",
                    "path": src}

        udisk_paths = get_udisk_path(abs_path=True)
        if not udisk_paths:
            raise code.FileUnEixstError()

        udisk_path = udisk_paths[0]

        udisk_file = os.path.join(udisk_path, src)
        if not os.path.isfile(udisk_file):
            raise code.FileUnEixstError()

        res = upload_file(udisk_file, src)
        status = res["status"]
        if status == 1:
            return sub_data
        else:
            return {"sub_code": 3,
                    "info": res["info"]}

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

    def register(self):
        while True:
            try:
                machine_id = get_machine_id()
                res = register()
                log.info("id: %s, register: %s" % (machine_id, res))
                status = res["status"]
                if status == 1:
                    register_id = res.get("machine_id")
                    if register_id != machine_id:
                        set_machine_id(register_id)
                    return
                else:
                    continue

            except Exception as e:
                log.warning("register: %s" % str(e))
            time.sleep(5)

    def report(self, params=False, status=True, force=False, retry=3):
        now_params, now_status = self.prt_manager.query()
        params_reported = False
        status_reported = False
        if params:
            pa = {"two-side": True,
                  "colorful": False}
            log.info("params: %s" % pa)
            for i in range(retry):
                res = report_printer_params(pa)
                if res["status"] == 1:
                    params_reported = True
                    break

        elif status:
            st = {"status-code": now_status["status-code"],
                  "status-desc": now_status["status-desc"],
                  "device-uri": now_status["device-uri"],
                  "device-state": now_status["device-state"],
                  "error-state": now_status["error-state"]}
            log.info("status: %s" % st)
            if self.prt_st != st["status-code"] or force:
                for i in range(retry):
                    res = report_printer_params(st)
                    if res["status"] == 1:
                        self.prt_st = st["status-code"]
                        status_reported = True
                        break

        return params_reported, status_reported

    def run(self, test=False):
        try:
            log.info("start".center(100, '-'))
            self.before_work()

            self.init_server()
            run_server()
            self.jobs_report()

            if test:
                embed()
            else:
                interval_time = 5 * 60
                while not self._stop_event.is_set():
                    time.sleep(interval_time)
                    try:
                        self.report(status=True)
                    except Exception as e:
                        log.warning(str(e))

        except Exception as e:
            log.error("exit unexpect: %s" % str(traceback.format_exc()))


if __name__ == "__main__":
    ctrl = Controler()
    test = True if len(sys.argv) >= 2 and sys.argv[1] == "test" else False
    ctrl.run(test)
