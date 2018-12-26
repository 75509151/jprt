import sys
import threading
import traceback
import signal

from cab.utils.server import Server, run_server
from cab.utils.c_log import init_log
from cab.utils.console import embed 
from cab.utils import constant as cst
from cab.db.db_pool import DB_POOL as DBP
from cab.ctrl.prt_manager import PrtManager


log = init_log("ctl")



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
        self.serv = Server(
            ("0.0.0.0", cst.G_CTRL_PORT), self.sock_process_hook)

    def sock_process_hook(self, data):
        pass

    def before_work(self):
        try:
            if self.prt_manager.need_install():
                self.prt_manager.install_printer()
            self.prt_manager.report_params()
            self.prt_manager.report_status()
        except Exception as e:
            log.warning(str(traceback.format_exec()))


    def run(self, test=False):
        try:
            log.info("start".center(100, '-'))
            self.before_work()

            self.init_server()
            run_server()

            if test:
                embed()
            else:
                interval_time = 5*60
                while not self._stop_event.is_set():
                    time.sleep(interval_time)
                    try:
                        self.prt_manager.open()
                    except Exception as e:
                        log.waring(str(e))

        except Exception as e:
            log.error("exit unexpect: %s" % str(traceback.format_exc()))



if __name__ == "__main__":
    ctrl = Controler()
    test =True if len(sys.argv) >= 2 and sys.argv[1] == "test" else False
    ctrl.run(test)
    

