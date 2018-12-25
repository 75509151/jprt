import json

from prnt import cups
from base import device

from cab.utils.c_log import init_log
from cab.db.db_pool import DB_POOL
from cab.prts.printer import get_register_printer_info
from cab.prts.hp.hp_prt import HpPrinter
from cab.prts.prt_exceptions import PrtSetupError



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

        if not self.printer.device_uri and exist_uris:
            return True
        
        if self.printer.device_uri not in exist_uris and self.printer.dev is None:
            return True

        return False



    def install_printer(self):
        try:
            HpPrinter.setup()
            self.printer = HpPrinter()

        except PrtSetupError as e:
            log.warning("install printer failed: %s" % str(e))

    def report_printer_params(self):
        params = self.printer.get_params()


    def check_and_report_status(self):
        status = self.printer.get_status()

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
    manager = PrtManager()
    if manager.need_install():
        manager.install_printer()


