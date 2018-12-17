import sqlite3
import traceback

from cab.utils.machine_info import get_config, get_cur_time
from cab.utils.c_log import init_log

__all__ = ["get_db_instance"]

_config = get_config("ckc")
_ckc_db_path = _config.get("db", "ckc_db")
_sync_db_path = _config.get("db", "sync_db")


log = init_log("db")

def get_db_instance():
    return DB()

class DB(object):

    def __init__(self, ckc_db_path=_ckc_db_path, sync_db_path=_sync_db_path):
        self.config = get_config("ckc")
        self.ckc_db_path = ckc_db_path
        self.sync_db_path = sync_db_path
        self._open_db(ckc_db_path, sync_db_path)

    def __del__(self):
        self._close_db()

    def _open_db(self, ckc_db_path, sync_db_path):
        self.conn = sqlite3.connect(
            ckc_db_path, isolation_level="IMMEDIATE", timeout=60, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.sync_conn = sqlite3.connect(
            sync_db_path, isolation_level="IMMEDIATE", timeout=60, check_same_thread=False)
        self.sync_cursor = self.sync_conn.cursor()

    def _close_db(self):
        self.cursor.close()
        self.conn.close()
        self.sync_cursor.close()
        self.sync_conn.close()

    def set_kv(self, table, changes, sync=True):
        """ change the info or config & sync to server

        @param table: str, machine_info or machine_config
        @param changes: dict, {key: value, ...}
        @param sync: bool, need sync to server?
        @return: None
        """
        try:
            now = get_cur_time()
            sql = "UPDATE %s SET value=?, last_update_time=? WHERE key=?;" % table
            for itm in changes.items():    # itm: (key, value)
                log.info('%s %s=%s' % (sql, itm[0], itm[1]))
                self.cursor.execute(sql, (itm[1], now, itm[0]))
            if sync:
                pass
                # self.add_to_sync(SYNC_SERVICE, SYNC_MODULE, "set_kv",
                                 # {"machine_id": get_kiosk_id(), "table": table, "changes": changes, "change_time": now})
            self.conn.commit()
        except Exception:
            log.error(traceback.format_exc())
            self.conn.rollback()
            raise

    def get_kv(self, table, key):
        """ get the value of key from table(machine_info or machine_config)

        @param table: str, machine_info or machine_config
        @param key: str
        @return: value
        @rtype: str
        """

        sql = "SELECT value FROM %s WHERE key=? LIMIT 1;" % table
        row = self.cursor.execute(sql, (key, )).fetchone()
        if row:
            return row[0]
        else:
            return ""

    def change_kv(self, table, key, val, sync=True):
        if self.get_kv(table, key) != val:
            self.set_kv(table, {key: val}, sync)

    def add_kv(self, table, add_list, sync=True):
        """ add new info or config & sync to server

        @param table: str, machine_info or machine_config
        @param add_list: list(tuple), [(id, client_id, machine_id, key, value, time), ...]
        @param sync: bool, need sync to server?
        @return: None
        """
        try:
            sql = "INSERT INTO %s(id, client_id, machine_id, key, value, last_update_time) " \
                  "VALUES(?, ?, ?, ?, ?, ?);" % table
            self.cursor.executemany(sql, add_list)
            if sync:
                pass
                # self.add_to_sync(SYNC_SERVICE, SYNC_MODULE, "add_kv",
                                 # {"machine_id": get_kiosk_id(),
                                  # "table": table,
                                  # "add_list": add_list})
            self.conn.commit()
        except Exception:
            log.error(traceback.format_exc())
            self.conn.rollback()
            raise
