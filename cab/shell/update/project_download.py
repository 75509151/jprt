# -*- coding: UTF-8 -*-
"""
Created on 2017-10-26

@author: jay
"""
from subprocess import call
import click
import os

import json

from update_exceptions import *
from update_utils import (run_with_eat_exceptions,
                          set_kiosk_downloaded_version, generate_md5_info, ProcessLock,
                          cp_folder, check_and_creat_path)
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
        self.lock = ProcessLock(DOWNLOAD_LOCK_PATH)
        self.update_kiosk_md5_file = os.path.join(
            UPDATE_FOLDER, "main", "kiosk.json")
        self.update_main_path = os.path.join(UPDATE_FOLDER, "main")
        self.update_kiosk_path = os.path.join(self.update_main_path, "kiosk")
        check_and_creat_path(self.update_main_path)
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
        except KeyError, ex:
            self.log.error("Configuration file Error: %s" % str(ex))
            raise ConfigException("Configuration file Error: Update server")
        except Exception, ex:
            self.log.error("Exception caught when _initialize: %s" % str(ex))
            raise

    def rsync_file(self, src, dest):
        cmd = "rsync -az --delete --password-file={pwd_file} {user}@{server}::update/{base_path}/{version}/{src} {dest} ".format(
            pwd_file=self.pwd_file, user=self.user, server=self.server, base_path=REMOTE_UPDATE_BASE_DIR, version=self.version, src=src,
            dest=dest)

        self.log.info("do cmd: %s" % cmd)
        call(cmd, shell=True)

    def generate_pwd_file(self):
        os.system("echo %s > %s" % (self.pwd, self.pwd_file))
        os.system("chmod 600 %s" % self.pwd_file)

    def _download_md5_info(self):
        try:
            os.remove(self.update_kiosk_md5_file)
        except Exception:
            pass

        self.rsync_file("kiosk.json", self.update_kiosk_md5_file)

    def _download_project(self):
        self.rsync_file("kiosk", self.update_main_path)

    def check_md5_and_del_wrong_file(self):

        if not os.path.exists(self.update_kiosk_md5_file):
            self.log.info("md5 file miss")
            return False

        def get_json(file):
            with open(file, "r") as f:
                return json.load(f)

        def del_files(files):
            if isinstance(files, list) or isinstance(files, set):
                pass
            else:
                files = [files]
            for file in files:
                try:
                    os.remove(file)
                    self.log.info("del: %s" % file)
                except Exception as e:
                    self.log.warning("del wrong: %s" % str(e))

        kiosk_md5_dic = get_json(self.update_kiosk_md5_file)
        # print kiosk_md5_dic
        download_kiosk_md5_dic = generate_md5_info(
            self.update_kiosk_path, output_path="/tmp", info_name="kiosk.json")

        if kiosk_md5_dic != download_kiosk_md5_dic:
            self.log.warning("kiosk_md5 != download_kiosk_md5")
            # del wrong files
            for file, md5 in kiosk_md5_dic.items():
                if file != "files_count" and file in download_kiosk_md5_dic and download_kiosk_md5_dic[file] != md5:
                    del_files(os.path.join(self.update_kiosk_path, file))
            # del needless files
            remote_files = set(
                [file for file in kiosk_md5_dic.keys() if file != "files_count"])
            local_files = set(
                [file for file in download_kiosk_md5_dic.keys() if file != "files_count"])

            needless_files = local_files - remote_files
            self.log.info("needless files: %s, %s" %
                          (len(needless_files), needless_files))
            miss_files = remote_files - local_files
            self.log.info("miss files: %s, %s" %
                          (len(miss_files), miss_files))
            if needless_files:
                self.log.info("del needless files")
                needless_files = [os.path.join(
                    self.update_kiosk_path, file) for file in needless_files]
                del_files(needless_files)
            return False

        return True

    def cp_project(self):
        backup_path = os.path.join(UPDATE_FOLDER, self.version)

        cp_folder(self.update_main_path, backup_path)

    def download(self, retry=3):
        try:
            self.lock.acquire()
            for try_count in range(retry):
                try:
                    self._download_md5_info()
                    self._download_project()
                    if self.check_md5_and_del_wrong_file():
                        self.cp_project()
                        set_kiosk_downloaded_version(self.version)
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
@click.option("--test", "-t", prompt=u"是否使用54测试?", type=bool, default=False, help=u"false采用真实服务器|true use2.54")
def download_from_test(version, reboot=True, test=False):
    print "download starting..."
    d = VersionDownload(version=version, test=test)
    if d.download() and reboot:
        os.system("sudo reboot")


if __name__ == '__main__':

    download_from_test()
