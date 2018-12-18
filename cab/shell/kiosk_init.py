import traceback
import os
import time
import json
import sqlite3
import sys

import requests
from cab.api.server_api import call_once
from cab.utils.c_log import init_log
from cab.utils.machine_info import (
    get_machine_home,
    get_machine_server,
    get_machine_type,
    get_machine_id,
    get_hw_addr,
    get_config)


try:
    SERVER = get_machine_server("app", "conn.cereson.cn")
except Exception:
    SERVER = "conn.cereson.cn"


HOME_PATH = get_machine_home()
PROGRESS = os.path.join(HOME_PATH, "var/progress")
print(PROGRESS)

log = init_log("machine_init")
TRY_TIMES = 3


class KioskInit():
    '''
    when the device power on, this py will be excetued once
    '''

    def __init__(self):
        self.config = get_config("ckc")

        try:
            self.machine_id = get_machine_id().upper()
        except Exception:
            self.machine_id = ""
        log.debug("old machine_id:%s" % self.machine_id)
        self._get_mac()
        self.machine_type = get_machine_type(real=True)

    def _get_mac(self, iface='eth0'):
        """
        Get ethernet card MAC address
        param (str)eth: Ethernet Card number
        return: String of the MAC address.
        """
        self.mac = get_hw_addr(iface)
        return self.mac

    def _get_machine_id_from_mac(self, mac):
        """
        Get kiosk id from server api
        param mac: MAC address.
        """
        param = {'machine_id': self.machine_id,
                 'mac': self.mac, 'machine_type': self.machine_type}
        return call_once("")

    def _verify_db(self):
        VERIFY_DB_PY = os.path.join(
            get_machine_home(), "kiosk", "box", "shell", "verify_db.pyc")
        ret = os.system("%s %s" % ("python", VERIFY_DB_PY))
        log.info("verify db...: %s" % str(ret >> 8))

    def _set_machine_id(self, machine_id):
        """
        Set kiosk id for kiosk.
        """
        log.debug("Set machine_id:%s" % machine_id)

        f = open(get_machine_home() + ".kioskconfig/machine_id", 'w')
        f.write(machine_id)
        f.close()

        conn = sqlite3.connect(HOME_PATH + '/var/data/db/ckc.db')
        db = conn.cursor()
        try:
            db.execute(
                "SELECT tbl_name FROM sqlite_master WHERE tbl_name LIKE 'machine%'")
            rows = db.fetchall()
            for table in rows:
                sql = "UPDATE %s SET machine_id='%s'" % (table[0], machine_id)
                print(sql)
                db.execute(sql)
            conn.commit()
        except:
            log.error(traceback.format_exc())

        self._verify_db()

    def run(self):
        mac = self._get_mac()
        result = self._get_machine_id_from_mac(mac)
        log.info("status:%s" % str(result))
        # code = result['status_code']
        # try:
            # log.debug("run_get_machine_id_from_mac")
            # if code in [0, 3]:
                # log.debug("Correct machine_id %s" % result['machine_id'])

            # elif code == 1:
                # self.machine_id = result['machine_id']
                # self._set_machine_id(self.machine_id)
            # elif code in [2, 4]:  # 2 new disk, old board; 4 old disk old board,
                                            # # but id not equal, will use board
                                            # # machine_id
                # log.info("code: %s " % code)
                # os.mknod(PROGRESS)
                # self.machine_id = result['machine_id']
                # self._set_machine_id(self.machine_id)
                # os.system("sudo reboot")
            # else:
                # #self.msgbox.information(None,"Warning",u"Get machine_id failure,Please contact the staff")
                # pass
        # except Exception:
            # log.error(traceback.format_exc())
        # finally:
            # if code in [1, 2, 4]:
                # log.error("finally reboot")
                # os.system("sudo reboot")
                # sys.exit(-1)


    def reset(self):
        pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        KioskInit().run()
    elif sys.argv[1] == 'reset':
        KioskInit().reset()
