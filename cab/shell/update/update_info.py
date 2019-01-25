# coding: utf-8
import os

import update_utils as upu


PYTHON_PATH = "python3"

UPDATE_lOG = upu.init_log()

UPDATE_FOLDER = os.path.join(upu.get_machine_home(), "update")
VERSION_DOWN = os.path.join(UPDATE_FOLDER, "version")
REMOTE_VERSION = os.path.join(UPDATE_FOLDER, "remote_version")

upu.check_and_creat_path(UPDATE_FOLDER)

BACKUP_FOLDER = os.path.join(upu.get_machine_home(), "backup")
UPDATE_PWD_FILE = "/tmp/update_pwd"


REAL_SERVER = {"addr": "67.218.146.76", "user": "jprt", "password": "jprt-up"}
TEST_SERVER = {"addr": "67.218.146.76", "user": "jprt", "password": "jprt-up"}

REMOTE_UPDATE_BASE_DIR = "JPRT"
#
DOWNLOAD_INTERVAL_SEC = 1 * 60 * 60
DOWNLOAD_LOCK_PATH = "/tmp/.download_lock"
