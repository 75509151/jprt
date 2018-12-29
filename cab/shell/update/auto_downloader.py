# -*- coding: UTF-8 -*-
"""
Created on 2017-10-30

@author: jay
"""
from subprocess import call
import os
import time
import sys

from update_utils import (get_kiosk_downloaded_version,
                          set_kiosk_downloaded_version,
                          get_file_content,
                          run_with_eat_exceptions)
from project_download import VersionDownload
from update_exceptions import ConfigException
from update_info import (DOWNLOAD_INTERVAL_SEC, UPDATE_lOG, UPDATE_PWD_FILE,
                         TEST_SERVER, REAL_SERVER, REMOTE_UPDATE_BASE_DIR, REMOTE_VERSION)
import random
import json
import datetime


class AutoDownloader(object):
    """docstring for AutoDownloader"""

    def __init__(self, test=False):
        super(AutoDownloader, self).__init__()
        self.log = UPDATE_lOG
        self.test = test
        self.pwd_file = UPDATE_PWD_FILE
        self.remote_version_file = REMOTE_VERSION
        self.initialize()

    @run_with_eat_exceptions
    def _remove_kownhosts(self):
        os.system("rm ~/.ssh/known_hosts")

    def initialize(self):
        self._remove_kownhosts()
        try:
            if self.test is True:
                self.server = TEST_SERVER["addr"]
                self.user = TEST_SERVER["user"]
                self.pwd = TEST_SERVER["password"]
            else:
                self.server = REAL_SERVER["addr"]
                self.user = REAL_SERVER["user"]
                self.pwd = REAL_SERVER["password"]
            self.generate_pwd_file()
        except KeyError as ex:
            self.log.error("Configuration file Error: %s" % str(ex))
            raise ConfigException("Configuration file Error: Update server")
        except Exception as ex:
            self.log.error("Exception caught when _initialize: %s" % str(ex))
            raise

    def rsync_file(self, src, dest):
        cmd = "rsync -az --password-file={pwd_file} {user}@{server}::update/{base_dir}/{src} {dest} ".format(
            pwd_file=self.pwd_file, user=self.user, server=self.server, base_dir=REMOTE_UPDATE_BASE_DIR, src=src,
            dest=dest)

        self.log.info("do cmd: %s" % cmd)
        call(cmd, shell=True)

    def get_remote_version_info(self):
        self.rsync_file("version", self.remote_version_file)
        info = {}
        with open(self.remote_version_file, "r") as f:
            info = json.load(f)
        return info

    def generate_pwd_file(self):
        os.system("echo %s > %s" % (self.pwd, self.pwd_file))
        os.system("chmod 600 %s" % self.pwd_file)

    def get_need_download_version(self):
        allow_version_info = self.get_remote_version_info()
        downloaded_version = get_kiosk_downloaded_version()
        allow_version = allow_version_info.get("version", "")
        update_day = allow_version_info.get("date", "")
        self.log.info("allow_version: %s downloaded_version: %s" %
                      (allow_version, downloaded_version))
        if allow_version > downloaded_version and update_day <= str(datetime.date.today()):
            self.log.info("need_download_version ---allow: %s" % allow_version)
            return allow_version
        else:
            return ""

    def run(self):
        time.sleep(60 * random.randint(8, 12))
        while True:
            try:
                need_download_version = self.get_need_download_version()
                if need_download_version:
                    downloader = VersionDownload(
                        need_download_version, test=self.test)
                    downloader.download()
            except Exception as e:
                self.log.warning("auto downloader exception: %s" % str(e))
            self.log.info("sleep: %s" % DOWNLOAD_INTERVAL_SEC)
            time.sleep(DOWNLOAD_INTERVAL_SEC)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        downloader = AutoDownloader(test=True)
    else:
        downloader = AutoDownloader(test=False)
    downloader.run()
