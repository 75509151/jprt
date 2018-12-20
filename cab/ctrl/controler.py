import threading
import traceback
import signal

from cab.utils.server import Server, run_server
from cab.utils.c_log import init_log
from cab.db.db_pool import DB_POOL as DBP
from cab.utils import constant as cst


log = init_log("ctl")


class Controler(object):
    def __init__(self):
        super(Controler, self).__init__()
        self.log = log
        self._stop_event = threading.Event()
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self._stop_event.set()
        log.info("catch signal: %s, %s" % (signum, frame))

    def init_server(self):
        self.serv = Server(
            ("0.0.0.0", cst.G_CTRL_PORT), self.sock_process_hook)

    def sock_process_hook(self, data):
        pass

    def run(self):
        try:
            log.info("start".center(100, '-'))
            self.init_server()
            run_server()

            while not self._stop_event.is_set():
                pass
        except Exception as e:
            log.error("exit unexpect: %s" % str(traceback.format_exc()))


def main():
    ctrl = Controler()
    ctrl.run()
