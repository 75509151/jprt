# coding: utf-8
import os

import codecs
from update_utils import (check_and_creat_path, init_log,
                          get_kiosk_home, get_kiosk_server)

PYTHON_PATH = os.path.join(
    get_kiosk_home(), ".pyenv", "versions", "parking_env", "bin", "python")

UPDATE_lOG = init_log()

UPDATE_FOLDER = os.path.join(get_kiosk_home(), "update")
VERSION_DOWN = os.path.join(UPDATE_FOLDER, "version")
REMOTE_VERSION = os.path.join(UPDATE_FOLDER, "remote_version")

check_and_creat_path(UPDATE_FOLDER)

BACKUP_FOLDER = os.path.join(get_kiosk_home(), "backup")
UPDATE_PWD_FILE = "/tmp/update_pwd"


REAL_SERVER = {"addr": get_kiosk_server(
    "update", "parking.cereson.cn"), "user": "updown", "password": "updatedown8810"}
TEST_SERVER = {"addr": "192.168.2.54",
               "user": "upup", "password": "update9527"}

REMOTE_UPDATE_BASE_DIR = "PARK"
#
DOWNLOAD_INTERVAL_SEC = 2 * 60 * 60
DOWNLOAD_LOCK_PATH = "/tmp/.download_lock"
