# -*- coding: utf-8 -*-
"""
Created on 2013-01-28
@author: tim.guo@cereson.com
"""
# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')

import os
import time
import base64
import logging
import logging.handlers
from logging.handlers import SocketHandler
from logging.handlers import DatagramHandler
from .machine_info import (
    get_machine_home,
    get_machine_id,
    get_machine_name,
    get_machine_version,
    get_machine_location,
    get_config
)
try:
    import simplejson as json
except ImportError:
    import json


__all__ = ["merchanical_failure", "status_summary", "inventory_warning", "recycle_bin", "network",
           "user_operation", "init_log"]

merchanical_failure, status_summary, inventory_warning, recycle_bin, network, user_operation = \
    ('merchanical_failure', 'status_summary', 'inventory_warning',
     'recycle_bin', 'network', "user_operation")
alert_type_zh = {
    merchanical_failure: u"机械报错",
    status_summary: u"状态汇总",
    inventory_warning: u"库存预警",
    recycle_bin: u"交易异常",
    network: u"网络",
    user_operation: u"用户操作",
}
error_type_zh = {
    "NOTICE": u"提醒",
    "FATAL": u"报错"
}

email_EOL = "<br>"




def init_log(handle_name, file_name="", debug=False, rotate="size", count=5):
    """
    New logger rotate
    @param handle_name: The logger name, and log file name as default.
    @param file_name: The log file path, set as handle_name as default if it's empty.
    @param debug: Logging debug information.
    @param rotate: Log file rotate by 'date' or 'size'.
    """
    create_file = True
    log = MachineLog(create_file, handle_name, file_name,
                     debug, rotate, count=count)
    return log



class UdpHandler(DatagramHandler):
    """
    Send log which is already formatted to the recieve end in string format.
    """

    def __init__(self, host, port, machine_id):
        DatagramHandler.__init__(self, host, port)
        self.machine_id = machine_id

    def emit(self, record):

        try:
            msg = {
                'id': self.machine_id,
                'data': self.format(record),
                'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            msg = json.dumps(msg)
            self.send(msg)
        except (KeyboardInterrupt, SystemExit):
            print("udp catch exception")
        except Exception:
            self.handleError(record)


class MySocketHandler(SocketHandler):

    def __init__(self, host, port, machine_id):
        SocketHandler.__init__(self, host, port)
        self.machine_id = machine_id

    def emit(self, record):
        record.args = {'machineid': self.machine_id, 'errtime': time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime())}
        SocketHandler.emit(self, record)


class MachineLog(object):

    def __init__(self, create_file, handle_name, file_name="", debug=False, rotate="size", count=5, level=logging.INFO):
        if not create_file:
            self.log = logging.getLogger(name=handle_name)
        else:
            self.log = logging.getLogger(name=handle_name)
            self.level = level
            if not file_name:
                file_name = handle_name
            logfile = os.path.join(
                os.environ["HOME"], "var/log/%s.log" % file_name.lower())
            path, f = os.path.split(logfile)
            if not os.path.exists(path):
                os.makedirs(path)

            self.formatter = logging.Formatter(
                '%(asctime)s,%(msecs)03d %(levelname).1s %(thread).4s %(message)s', "%y-%m%d %H:%M:%S")
            if not self.log.handlers:
                if rotate is False:
                    handle = logging.FileHandler(logfile)
                    handle.setFormatter(self.formatter)
                    self.log.addHandler(handle)
                else:
                    if rotate == 'size':
                        rotate_handle = logging.handlers.RotatingFileHandler(
                            logfile, maxBytes=1024 * 1024 * 10, backupCount=count, encoding="utf-8")
                    elif rotate == 'date':
                        rotate_handle = logging.handlers.TimedRotatingFileHandler(
                            logfile, 'midnight', backupCount=count, encoding="utf-8")
                    else:
                        rotate_handle = logging.handlers.RotatingFileHandler(
                            logfile, maxBytes=1024 * 1024 * 10, backupCount=count, encoding="utf-8")
                    rotate_handle.setFormatter(self.formatter)
                    self.log.addHandler(rotate_handle)
                if debug:
                    ch = logging.StreamHandler()
                    # chf = logging.Formatter('%(levelname)-8s %(message)s')
                    ch.setFormatter(self.formatter)
                    self.log.addHandler(ch)
                    self.log.setLevel(logging.DEBUG)
                else:
                    self.log.setLevel(logging.INFO)
            else:
                self.log.info("already add handler")

    def add_sock_handler(self, host, port):
        """ add socket handler for the log instance
        """
        hand = MySocketHandler(host, port, get_machine_id())
        # hand.setFormatter(self.formatter)
        self.log.addHandler(hand)

    def add_udp_handler(self, host, port):
        """[summary]

        [description]

        Arguments:
            host {[type]} -- [description]
            port {[type]} -- [description]
        """
        hand = UdpHandler(host, port, get_machine_id())
        self.log.addHandler(hand)

    def getlog(self):
        return self.log

    def debug(self, log):
        try:
            self.log.debug(log)
        except Exception:
            self.log.exception("error: ")

    def info(self, log):
        try:
            self.log.info(log)
        except Exception:
            self.log.exception("info: ")

    def warning(self, log):
        try:
            self.log.warning(log)
        except Exception:
            self.log.exception("error: ")

    def error(self, log):
        try:
            self.log.error("\033[1;31m\n%s\n\033[0m" % log)
        except Exception:
            self.log.exception("error: ")

    def fatal(self, log, error_type="FATAL", alert_type=merchanical_failure,
              attachment_path=None, alert_level="PUBLIC",
              interval=0, interval_type="default"):
        try:
            self.log.fatal(log)
        except Exception:
            self.log.exception("fatal: ")

if __name__ == "__main__":
    pass
