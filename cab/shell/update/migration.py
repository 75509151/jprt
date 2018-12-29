#!/usr/bin/python

"""
do migrations


Change Log:
    2015-03-04  Created by Tavis

"""
import os
import sys
from update_utils import get_kiosk_home

from update_info import UPDATE_lOG, PYTHON_PATH
from db.dbm import get_db_instance

# now 1.0.0 is trunk version
VERSION_LIST = ['1.1.0', '1.1.1', '1.1.2', '1.1.3','1.1.4', '1.1.5','1.1.6']

log = UPDATE_lOG


def header(func):
    def run(*argv):
        log.info(func.__name__)
        if argv:
            ret = func(*argv)
        else:
            ret = func()
        return ret
    return run


class Migration(object):

    def __init__(self, old_version, new_version):
        self.old_version = old_version
        self.new_version = new_version
        self.version_list = self.get_version_list()

        self.verify_db()
        self.db = get_db_instance()

    def get_version_list(self):
        return VERSION_LIST

    def verify_db(self):

        log.info("verify db!")

        VERIFY_DB_PY = os.path.join(
            get_kiosk_home(), "jprt", "cab", "db", "verify_db.pyc")
        os.system("%s %s" % (PYTHON_PATH, VERIFY_DB_PY))

    def __del__(self):
        del self.version_list

    def do_migrations(self):
        old_version = self.old_version
        new_version = self.new_version
        vlist = self.get_version_list()
        if old_version in vlist and new_version in vlist:
            need_rollback = False
            rollback_list = []
            migrate_list = vlist[vlist.index(
                old_version):vlist.index(new_version) + 1]
            # do all migrations
            for i in range(len(migrate_list)):
                if i != 0:
                    v1 = migrate_list[i - 1].replace(".", "")
                    v2 = migrate_list[i].replace(".", "")
                    migrate_name = "m%sto%s" % (v1, v2)
                    rollback_name = "r%sto%s" % (v2, v1)
                    migrate = getattr(self, migrate_name, None)
                    log.info("try: %s" % migrate_name)
                    if migrate:
                        try:
                            migrate()
                            rollback_list.append(rollback_name)
                        except Exception, ex:
                            need_rollback = True
                            log.error("%s: %s" % (migrate_name, str(ex)))
                            break

            # check if need rollback
            if need_rollback:
                log.info("SOMETHING WRONG.")

                if rollback_list:
                    log.info("NOW ROLLBACK.")
                    rollback_list.reverse()
                    for itm in rollback_list:
                        log.info("try: %s" % itm)
                        rollback = getattr(self, itm, None)
                        if rollback:
                            rollback()
            return not need_rollback
        if old_version not in vlist:
            log.error("%s not in VERSION_LIST" % old_version)
        if new_version not in vlist:
            log.error("%s not in VERSION_LIST" % new_version)

    @header
    def m122to123(self):
        pass

    @header
    def r123to122(self):
        pass


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print "Usage: ./migration.py old_version new_version"
    else:
        old_version = sys.argv[1]
        new_version = sys.argv[2]
        m = Migration(old_version, new_version)
        ret = m.do_migrations()
        if ret:
            log.info("Done!")
            sys.exit(0)
        else:
            log.info("Failed!")
            sys.exit(1)
    sys.exit(0)
