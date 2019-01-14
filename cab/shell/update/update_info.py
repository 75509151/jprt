# coding: utf-8
import os

import update_utils as upu

PYTHON_PATH = "python3"

UPDATE_lOG = init_log()

UPDATE_FOLDER = os.path.join(upu.get_machine_home(), "update")
VERSION_DOWN = os.path.join(UPDATE_FOLDER, "version")
REMOTE_VERSION = os.path.join(UPDATE_FOLDER, "remote_version")

upu.check_and_creat_path(UPDATE_FOLDER)

BACKUP_FOLDER = os.path.join(upu.get_machine_home(), "backup")
UPDATE_PWD_FILE = "/tmp/update_pwd"


REAL_SERVER = {"addr": upu.get_machine_server(
    "update"), "user": "jprt", "password": "jprt"}
TEST_SERVER = {"addr": "192.168.2.101",
               "user": "jprt", "password": "jprt"}

REMOTE_UPDATE_BASE_DIR = "JPRT"
#
DOWNLOAD_INTERVAL_SEC = 2 * 60 * 60
DOWNLOAD_LOCK_PATH = "/tmp/.download_lock"
