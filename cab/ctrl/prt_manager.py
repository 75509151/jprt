import time
import os
import threading
import pudb

from prnt import cups
from base import device

from cab.utils.c_log import init_log
from cab.utils.utils import run_cmd
from cab.db.db_pool import DB_POOL
from cab.prts.hp.hp_prt import HpPrinter
from cab.prts.prt_exceptions import PrtSetupError
from cab.prts import office

log = init_log("prt_manager")


def wait_job_done(job, timeout=60 * 5):
    #TODO: need op
    start = time.time()
    while time.time() - start < timeout:
        jobs = cups.getJobs()
        if job.id not in [j.id for j in jobs]:
            completed_jobs = cups.getJobs(completed=1)
            for completed_job in completed_jobs[::-1]:
                if completed_job.id == job.id:
                    try:
                        err_msg = cups.getPrintJobErrorLog(job.id)
                        log.info("job_id: %s, msg: %s" % (completed_job.id, err_msg))
                    except Exception as e:
                        log.warning("get_err_log:%s" % str(e))

                    return completed_job
            else:
                log.info("can not find this job")
                return None

        else:
            time.sleep(1)
    log.info("find job timeout :%s" % job.id)
    return None

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

    def cancel_uncomplete_jobs(self):
        try:
            jobs = cups.getJobs(completed=0)
            for job in jobs:
                cups.cancelJob(job.id)

        except Exception as e:
            log.warning("cancel_uncomplete_jobs: %s" % str(e))


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

    def print_file(self, document, num=1, colorful=False, sides="one-sided", fit_page=True):
        """
        -o sides=one-sided
            Prints on one side of the paper.

        -o sides=two-sided-long-edge
            Prints on both sides of the paper for portrait output.

        -o sides=two-sided-short-edge
        """
        with self.lock:
            jobs = cups.getJobs(completed=0)
            log.info("old jobs len: %s" % len(jobs))

            options = "-#{num} -o sides={sides} ".format(num=num, sides=sides)
            if fit_page:
                options += " -o fit-to-page"


            self.printer.print_file(document, options, remove=True)
            jobs = cups.getJobs(completed=0)
            curr_job = jobs[-1] if jobs else cups.getJobs(completed=1)[-1]

            log.info("now all jobs len: %s, new job-id: %s" % (len(jobs), curr_job.id))
            return curr_job

    def open(self):
        if self.printer.dev:
            # TODO: try
            self.printer.open()



if __name__ == "__main__":
    m = PrtManager()
    if m.need_install():
        m.install_printer()
