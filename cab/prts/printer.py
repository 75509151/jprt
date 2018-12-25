
from prnt import cups

from cab.db.db_pool import DB_POOL


class PrinterInfo(object):
    def __init__(self, **kw):
        self.name = kw.get("name", None)
        self.device_uri = kw.get("device_uri", None)


