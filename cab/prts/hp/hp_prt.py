import time
import pexpect


from base import device, status, utils, tui, module
from prnt import cups

from cab.utils.console import embed
from cab.utils.utils import get_mimetype
from cab.utils.c_log import init_log
from cab.prts.prt_exceptions import (PrtSetupException,
       DeviceNotFoundExcetion)

log = init_log("prt")

class HpPrinter():

    def __init__(self, device_uri=None, printer_name=None):
        self.printer_name = printer_name 
        self.device_uri = device_uri 
        self.dev = None

        if self.printer_name and not self.device_uri:
            self.device_uri = device.getDeviceURIByPrinterName(self.printer_name)

        if not self.printer_name and not self.device_uri:
            printers = cups.getPrinters()
            printer = printers[0] if printers else None

            if printer:
                self.printer_name = printer.name
                self.device_uri = printer.device_uri
        
        try:
            self._init_device()
        except Exception as e:
            log.waring(str(e))

        log.info("hp")


    def _init_device(self):
        if not self.device_uri:
            raise DeviceNotFoundException("device_uri miss")

        self.dev = device.Device(self.device_uri)
     
    
    def open(self):
        self.dev.open()

    def close(self):
        self.dev.close()

    def print_file(self, file_name, remove=True):
        if get_mimetype(file_name) != "application/msword": 
            self.dev.printFile(file_name, self.printer_name, raw=False, remove=remove)
        else:
            raise Exception("Not implete")
        

    @staticmethod
    def setup(connection_type="usb"):
        log_file = open("/tmp/hp_setup.log",'w')
        cmd = 'hp-setup -i'
        child = pexpect.spawnu(cmd)
        try:
            child.logfile = log_file

            ind = child.expect(["enter=usb*", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline("0")
            else:
                raise PrtSetupException("error when choose connection type")

            ind = child.expect(["use model name", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline()
            else:
                raise PrtSetupException("error when choose model name")

            ind = child.expect(["be the correct one", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline("y")
            else:
                raise PrtSetupException("error when choose ppd")

            ind = child.expect(["description for this printer", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline()
            else:
                raise PrtSetupException("error when add description")

            ind = child.expect(["information or notes for this printer", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline()
            else:
                raise PrtSetupException("error when add information")

            ind = child.expect(["print a test page", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline("y")
            else:
                raise PrtSetupException("error when choose ppd")

            child.expect([pexpect.EOF, pexpect.TIMEOUT])
        finally:
            child.logfile.close()


if __name__ == "__main__":
    embed()
