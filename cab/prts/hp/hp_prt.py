import os
import time
import pexpect


from base import device, status, utils, tui, module
from prnt import cups

from cab.utils.console import embed
from cab.utils.utils import get_mimetype
from cab.utils.c_log import init_log
from cab.prts.prt_exceptions import (PrtSetupException,
       DeviceNotFoundExcetion,
       PrtPrintException)
from cab.prts import office

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

    def print_file(self, document, options='', remove=False):
        """黑白彩色，单双面，份数 """
        if not os.path.isfile(document):
            raise Exception("not file")

        if get_mimetype(document) in ("application/msword", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.presentationml.presentation"): 
            log.info("office")
            if office.print_file(document, printer_name):
                raise PrtPrintException("print file error")

        else:
            log.info("not office")
            cmd = "/usr/bin/lpr -P '%s' '%s'" % (self.printer_name, document) 
            if os.system(cmd) != 0:
                raise PrtPrintException("print file error")

        if remove:
            os.system("rm %s" % document)

        

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