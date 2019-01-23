import json
import os
import threading
import pudb

from prnt import cups
from base import device

from cab.utils.c_log import init_log
from cab.db.db_pool import DB_POOL
from cab.prts.hp.hp_prt import HpPrinter
from cab.prts.prt_exceptions import PrtSetupError
from cab.prts import office

log = init_log("prt_manager")


class PrtManager(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.printer = HpPrinter()

    def discovery_uris(self, bus=None):
        if not bus:
            bus = ["usb"]
        return list(device.probeDevices(bus).keys())

    def need_install(self):
        exist_uris = self.discovery_uris()
        if not exist_uris:
            log.info("no printer connect")
            return False

        if not self.printer.device_uri:
            log.info("need new install: %s" % exist_uris)
            return True

        if self.printer.device_uri not in exist_uris:
            # TODO: not pythonic
            self.delete_printer(self.printer.name)
            log.info("need install for other: %s" % exist_uris)
            return True

        return False

    def delete_printer(self, name):
        ret = os.system("lpadmin -x '%s'" % name)
        log.warning("delete printer: %s, ret: %s" % (name, ret))

    def install_printer(self):
        try:
            HpPrinter.setup()
            self.printer = HpPrinter()

        except PrtSetupError as e:
            log.warning("install printer failed: %s" % str(e))

    def query(self):
        try:
            params, status = self.printer.query()
            log.info("params: %s" % params)
            log.info("status: %s" % status)
        except Exception as e:
            log.warning("query: %s" % str(e))
            params = None
            status = {"status-code": 1019,
                      "status-desc": "power down",
                      "device-uri": "",
                      "device-state": 0,
                      "error-state": 0}
        return params, status

    def print_file(self, document, num=1, colorful=False, sides="one-sided"):
        """
        -o sides=one-sided
            Prints on one side of the paper.

        -o sides=two-sided-long-edge
            Prints on both sides of the paper for portrait output.

        -o sides=two-sided-short-edge
        """
        with self.lock:
            all_jobs = cups.getAllJobs()
            log.info("old jobs len: %s" % len(all_jobs))

            options = "-#{num} -o sides={sides} ".format(num=num, sides=sides)

            self.printer.print_file(document, options, remove=True)
            all_jobs = cups.getAllJobs()

            log.info("now all jobs len: %s, new job-id: %s" % (len(all_jobs), all_jobs[-1].job_id))
            return all_jobs[-1]

    def open(self):
        if self.printer.dev:
            # TODO: try
            self.printer.open()
        else:
            pass
            # if self.need_install():
            # self.install_printer()


if __name__ == "__main__":
    m = PrtManager()
    if m.need_install():
        m.install_printer()
