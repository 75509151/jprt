# coding:utf-8
import binascii
import re
import json
import sys
import copy
import struct
import random
import time
import select
import serial
import threading
import traceback
from cab.utils.c_log import init_log
from cab.utils.console import embed

log = init_log("dc_cab")

BOUDRATE = 9600

PACK_STX = '\x8A'
PACK_ETX = '\x9B'

IND_STX = 0
IND_ADDR = 1
IND_DOOR = 2
IND_CMD = 3
IND_ST = 3
IND_BCC = 4

CMD_OPEN_DOOR = '\x11'


def pretty(data, space=" "):
    return space.join(["%0.2X" % ord(c) for c in data])


def get_bcc(data):
    bcc = 0
    for d in data:
        bcc ^= ord(d)
    return chr(bcc)



class SDCDoor(object):

    def __init__(self, port="/dev/dc_door"):
        self.port = port

    def open_door(self, door, board=0, retry=3):
        if not self.port:
            raise serial.SerialException
        time.sleep(1)
        log.info("open_door: %s, %s" % (door, board))


class DCDoor(object):

    def __init__(self, port="/dev/dc_door", parent=None):
        self.port = port
        self.info = {"serial": False}
        self.boudrate = BOUDRATE
        self.ser = None
        self.open_serial()
        self.lock = threading.Lock()

    def open_serial(self):
        if not self.port:
            return
        log.info("open ser".center(100, '-'))

        if not self.ser:
            try:
                self.ser = serial.Serial(
                    self.port, self.boudrate, parity=serial.PARITY_NONE, timeout=0.5)
                self.info["serial"] = True

                self.ser.flushOutput()
                self.ser.flushInput()
            except:
                log.error("open serial %s error!!!" % self.port)

    def close_serial(self):
        if self.ser:
            self.ser.close()
            self.ser = None
            self.info["serial"] = False

    def send(self, bean):
        with self.lock:
            try:
                self.ser.flushInput()
                self.ser.flushOutput()
                all_data = bean.encode_frame()
                log.info("tx: %s" % pretty(all_data))
                self.ser.write(all_data)
            except serial.SerialException as e:
                self.ser = None
                log.warning(traceback.format_exc())
                raise e

            except Exception as e:
                log.warning(traceback.format_exc())
                raise e

    def open_door(self, door=1, board=1, retry=3):
        head_part = PACK_STX + chr(board) + chr(door) + CMD_OPEN_DOOR
        bcc = get_bcc(head_part)
        data = head_part + bcc
        return self.do_cmd(data)


    def do_cmd(self, data, retry=3):
        for i in range(retry):
            try:
                self.send(data)
                raw_data = self.ser.read(5)
                log.info("rx: %s" % pretty(raw_data))
                if len(raw_data) != 5:
                    continue
                bcc = get_bcc(raw_data[:-1])
                if bcc != chr(raw_data[IND_BCC]):
                    log.info("bcc: %s, %s" % (bcc, raw_data[IND_BCC]))
                    continue
                st = ord(raw_data[IND_ST])

                return True
            except serial.SerialException:
                self.close_serial()
                self.open_serial()
                continue
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = None

    r = DCDoor(port)
    embed()
