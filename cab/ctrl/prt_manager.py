import json
import pudb

from prnt import cups
from base import device

from cab.utils.c_log import init_log
from cab.db.db_pool import DB_POOL
from cab.prts.hp.hp_prt import HpPrinter
from cab.prts.prt_exceptions import PrtSetupError

log = init_log("prt_manager")

class PrtManager(object):
    def __init__(self):
        self.printer = HpPrinter()

    def discovery_uris(self, bus=None):
        if not bus:
            bus = ["usb"]
        return list(device.probeDevices(bus).keys())

    def need_install(self):
        exist_uris = self.discovery_uris()
        if not exist_uris:
            return False

        if not self.printer.device_uri:
            log.info("need new install: %s" % exist_uris)
            return True

        if self.printer.device_uri not in exist_uris and self.printer.dev is None:
            log.info("need install for other: %s" % exist_uris)
            return True

        return False

    def install_printer(self):
        try:
            HpPrinter.setup()
            self.printer = HpPrinter()

        except PrtSetupError as e:
            log.warning("install printer failed: %s" % str(e))

    def report(self, params=True, status=True):
    
        params, status = self.printer.query()
        if params:
            print("params: %s" % params)
        if status:
            print("status: %s" % status)


    def print_file(self, document):
        pass

    def report_print_result(self):
        pass

    def open(self):
        if self.printer.dev:
            # TODO: try
            self.printer.open()
        else:
            pass
            # if self.need_install():
            # self.install_printer()


if __name__ == "__main__":
    pudb.set_trace()
    manager = PrtManager()
    if manager.need_install():
        manager.install_printer()
        manager.report_params()
    else:
        print("not need install")
    manager.report_status()
