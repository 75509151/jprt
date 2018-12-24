
from prnt import cups

from cab.db.db_pool import DB_POOL

def delete_printers(printers):
    pass


class PrinterInfo(object):
    def __init__(self, **kw):
        self.name = kw.get("name", None)
        self.device_uri = kw.get("device_uri", None)


def get_register_printer_info():
    with DB_POOL as db:
        printer_info = db.get_kv("machine_info", "printer")
        register_printer = PrinterInfo(**json.loads(printer_info)) if printer_info else PrinterInfo({})
    return register_printer

def save_register_printer_info(prt_info):
    with DB_POOL as db:
        db.set_kv("machine_info", "printer",
                json.dumps{"name":prt_info.name,
                    "device_uri": prt_info.device_uri})

