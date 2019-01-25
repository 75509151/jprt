# -*- coding: UTF-8 -*-
"""
Created on 2017-10-26

@author: jay
"""
from subprocess import call
import click
import os

import json

import update_exceptions as upex
import update_utils as upu 
from update_info import (REAL_SERVER, TEST_SERVER, UPDATE_FOLDER, UPDATE_PWD_FILE, UPDATE_lOG,
                         DOWNLOAD_LOCK_PATH, REMOTE_UPDATE_BASE_DIR)


class VersionDownload(object):
    """docstring for VersionDownload"""

    def __init__(self, version, test=True):
        super(VersionDownload, self).__init__()
        self.version = version
        self.test = test
        self.pwd_file = UPDATE_PWD_FILE
        self.log = UPDATE_lOG
        self.lock = upu.ProcessLock(DOWNLOAD_LOCK_PATH)
        self.update_main_path = os.path.join(UPDATE_FOLDER, "main")
        self.update_kiosk_path = os.path.join(self.update_main_path, "kiosk")
        upu.check_and_creat_path(self.update_main_path)
        self.initialize()

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
            raise upex.ConfigException("Configuration file Error: Update server")
        except Exception as ex:
            self.log.error("Exception caught when _initialize: %s" % str(ex))
            raise

    def rsync_file(self, src, dest):
        cmd = "rsync -az --delete --password-file={pwd_file} {user}@{server}::update/{base_path}/{version}/{src} {dest} ".format(
            pwd_file=self.pwd_file, user=self.user, server=self.server, base_path=REMOTE_UPDATE_BASE_DIR, version=self.version, src=src,
            dest=dest)
        
        ret = call(cmd, shell=True)
        self.log.info("do cmd: %s, ret:%s" % (cmd, ret))
        if ret != 0:
            raise Exception("rsync failed")

    def generate_pwd_file(self):
        os.system("echo %s > %s" % (self.pwd, self.pwd_file))
        os.system("chmod 600 %s" % self.pwd_file)


    def _download_project(self):
        self.rsync_file("kiosk", self.update_main_path)



    def cp_project(self):
        backup_path = os.path.join(UPDATE_FOLDER, self.version)

        upu.cp_folder(self.update_main_path, backup_path)

    def download(self, retry=3):
        try:
            self.lock.acquire()
            for try_count in range(retry):
                try:
                    self._download_project()
     
                    self.cp_project()
                    upu.set_machine_downloaded_version(self.version)
                    self.log.info("[download end]")
                    return True
                except Exception as e:
                    # TODO: if is network err, try again
                    import traceback
                    self.log.warning("download error: %s" %
                                     str(traceback.format_exc()))
                    raise e
        except Exception as e:
            raise e

        finally:
            self.lock.release()

        self.log.warning("download failed!!!")
        return False


@click.command()
@click.option("--version", "-v", prompt="version like 1.2.1", help=u"版本")
def download_from_test(version, reboot=True):
    print ("download starting...")
    d = VersionDownload(version=version)
    if d.download() and reboot:
        os.system("sudo reboot")


if __name__ == '__main__':

    download_from_test()
