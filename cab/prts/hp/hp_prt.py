import os
import sys
import time
import pexpect
import site
site.getsitepackages()
sys.path.append("/usr/share/hplip")


from base import device, status, utils, module
from prnt import cups

from cab.utils.console import embed
from cab.utils.utils import get_mimetype, run_cmd
from cab.utils.c_log import init_log
from cab.prts.prt_exceptions import (PrtSetupError,
                                     DeviceNotFoundError,
                                     PrtPrintError)
# from cab.prts import office

log = init_log("prt")


class HpPrinter():

    def __init__(self, device_uri=None, name=None):
        self.name = None
        self.device_uri = None
        self.dev = None

        hp_printers = device.getSupportedCUPSPrinters(["hp"])
        for printer in hp_printers:
            if (device_uri is None and name is None) or \
                    (device_uri and device_uri == printer.device_uri and name and printer.name == name):
                self.name = printer.name
                self.device_uri = printer.device_uri
                break

        try:
            self._init_device()
        except Exception as e:
            log.warning(str(e))

        log.info("hp")

    def _init_device(self):
        if not self.device_uri:
            raise DeviceNotFoundError("device_uri miss")

        print(self.device_uri)
        self.dev = device.Device(self.device_uri)

    def open(self):
        self.dev.open()

    def query(self):
        self.open()
        self.dev.queryDevice()
        params = self.dev.mq
        status = self.dev.dq
        return params, status

    def close(self):
        self.dev.close()

    def print_file(self, document, options='', remove=False, use_office=True):
        """黑白彩色，单双面，份数 """
        if not os.path.isfile(document):
            raise Exception("not file")
        suffix = os.path.splitext(document)[1]
        ms_types = (".doc", ".docx", ".xlsx", ".xls",
                    ".ppt", ".pptx")
        # if suffix == ".pdf" and options.find("-#1 -o sides=one-sided") != -1:
            # cmd = "/usr/local/bin/libreoffice6.2 --headless --invisible --pt '%s' '%s'" % (self.name, document)

        tmp_document = None
        if use_office and suffix in ms_types:
            dst = "/tmp"
            cmd = "libreoffice --headless --print-to-file --printer-name '{printer}' --outdir {dst} '{document}' ".format(printer=self.name, dst=dst, document=document)
            returncode, out, err = run_cmd(cmd, timeout=180)
            log.info("office code: %s, out: %s, err: %s" % (returncode, out,err)) 
            name = os.path.splitext(document)[0] + '.ps'
            tmp_document = os.path.join(dst, name)
            cmd = "/usr/bin/lpr {options} -P '{printer}' '{document}'".format(options=options, printer=self.name, document=tmp_document)


        elif suffix in ms_types:
            cmd = "unoconv -T 25 --stdout '{document}' | /usr/bin/lpr {options} -P '{printer}'".format(options=options, document=document, printer=self.name)
        else:
            cmd = "/usr/bin/lpr {options} -P '{printer}' '{document}'".format(options=options, printer=self.name, document=document)
        log.info("print cmd: %s" % cmd)
        try:
            returncode, out, err = run_cmd(cmd, timeout=120)
            log.info("return code: %s out: %s, err:%s" % (returncode, out, err))
            if  returncode:
                raise PrtPrintError("print file error")
        finally:
            if remove:
                os.system("rm '%s'" % document)
                if tmp_document:
                    os.system("rm '%s'" % tmp_document)

    @staticmethod
    def setup(connection_type="usb"):
        log_file = open("/tmp/hp_setup.log", 'w')
        cmd = 'hp-setup -i'
        child = pexpect.spawnu(cmd)
        try:
            child.logfile = log_file

            ind = child.expect(["enter=usb*", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                if connection_type == "usb":
                    type_ind = "0"
                else:
                    # TODO
                    type_ind = "1"

                child.sendline(type_ind)
            else:
                raise PrtSetupError("error when choose connection type")

            ind = child.expect(["use model name", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline()
            else:
                raise PrtSetupError("error when choose model name")

            ind = child.expect(["be the correct one", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline("y")
            else:
                raise PrtSetupError("error when choose ppd")

            ind = child.expect(["description for this printer", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline()
            else:
                raise PrtSetupError("error when add description")

            ind = child.expect(["information or notes for this printer", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline()
            else:
                raise PrtSetupError("error when add information")

            ind = child.expect(["print a test page", pexpect.TIMEOUT])
            if ind == 0:
                time.sleep(0.1)
                child.sendline("y")
            else:
                raise PrtSetupError("error when choose ppd")

            child.expect([pexpect.EOF, pexpect.TIMEOUT])
        finally:
            child.logfile.close()


if __name__ == "__main__":
    prt = HpPrinter()
    embed()
