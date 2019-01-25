# -*- coding: UTF-8 -*-
"""
Created on 2017-10-30

@author: jay
"""
import os
import click
import traceback

import update_info as upi 
import update_utils as upu 
import migration 
import update_exceptions as upex


class Deployer(object):

    def __init__(self):
        self.log = upi.UPDATE_lOG
        self.download_lock = upu.ProcessLock(upi.DOWNLOAD_LOCK_PATH)

    def do_cmd(self, cmd):
        self.log.info("command: %s" % cmd)
        return os.system(cmd)

    def need_update(self):
        downloaded_version = upu.get_machine_downloaded_version()
        ckc_version = upu.get_machine_version()
        self.log.info("download:%s    ckc:%s" %
                      (downloaded_version, ckc_version))
        if downloaded_version and ckc_version <= downloaded_version:
            return True
        return False

    def backup(self):

        self.backuppath = os.path.join(upi.BACKUP_FOLDER, self.ckc_version)
        self.do_cmd("rm -rf %s" % self.backuppath)
        self.do_cmd("mkdir -p %s" % self.backuppath)
        self.do_cmd("cp -r %s %s" %
                    (os.path.join(upu.get_machine_home(), "jprt"), self.backuppath))

    def cp_downloaded_to_project_path(self):
        project_path = os.path.join(upu.get_machine_home(), "jprt")
        certain_project_path = os.path.join(
            upi.UPDATE_FOLDER, self.downloaded_version, "jprt")
        self.do_cmd("rm -rf %s" % project_path)
        self.do_cmd("cp -r %s %s" % (certain_project_path, project_path))

    def do_migration(self):
        m = migration.Migration(self.ckc_version, self.downloaded_version)
        ret = m.do_migrations()
        if not ret:
            raise upex.MigrationException("DB migration failed.")

    def roll_back(self):
        self.log.info("update failed, rolling back...")
        self.do_cmd("rm -rf %s" % (os.path.join(upu.get_machine_home(), "jprt")))
        self.do_cmd("cp -r %s %s" %
                    (os.path.join(self.backuppath, "jprt"), upu.get_machine_home()))

    def _update(self):
        self.ckc_version = upu.get_machine_version()
        self.downloaded_version = upu.get_machine_downloaded_version()
        self.backup()

        try:
            self.cp_downloaded_to_project_path()
            self.do_migration()
            upu.set_machine_version(self.downloaded_version)
            self.log.info("update success")
        except Exception:
            self.log.warning("update err: %s" % str(traceback.format_exc()))
            self.roll_back()
        else:
            self.log.info("try reboot")
            self.do_cmd("sudo reboot")

    def run(self):
        if self.need_update():
            try:
                self.download_lock.acquire()
            except IOError:
                self.log.info("loading now")
            else:
                self._update()
            finally:
                self.download_lock.release()
        else:
            self.log.info("no need update. end...")


def main():
    deploy = Deployer()
    deploy.run()


if __name__ == "__main__":
    main()
