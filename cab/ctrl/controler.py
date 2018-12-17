from threading
import signal

from cab.utils.server import Server, run_server
from cab.utils.c_log import init_log

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

    def run(self):
        self.log



def main():
    ctrl = Controler()
    ckc_ctrl.run()
