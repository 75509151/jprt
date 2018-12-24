import json

from prnt import cups

from cab.db.db_pool import DB_POOL
from cab.prts.printer import get_register_printer_info
from cab.prts.hp.hp_prt import HpPrinter



class PrtManager(object):
    def __init__(self):
        self.printer_info = get_register_printer_info()
        self.printer = HpPrinter()



    def check_printer(self):
        self.check_and_report_status()


    def install_printer(self):
        pass

    def report_printer_params(self):
        pass

    def check_and_report_status(self):
        pass

    def print_file(self, document):
        pass
    

    def report_print_result(self):
        pass
