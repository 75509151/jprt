import os
import traceback
from . import update_utils as upu 
from . import update_info as upi 


log = upi.UPDATE_lOG


class UpateTool(object):
    """docstring for UpateTool"""

    def __init__(self):
        super(UpateTool, self).__init__()
        self.downloaded_version = None

    def _doCommand(self, cmd):
        ret = os.system(cmd)
        log.info("CMD:%s: %s" % (ret, cmd))
        return ret

    def _need_update(self):
        self.downloaded_version = upu.get_machine_downloaded_version()
        ckc_version = upu.get_machine_version()
        log.info("ckc_version: %s, downloaded_version: %s" %
                 (ckc_version, self.downloaded_version))
        if self.downloaded_version and ckc_version < self.downloaded_version:
            log.info("need update")
            return True
        return False

    def _update(self):
        delpoly_py = os.path.join(
            upi.UPDATE_FOLDER, self.downloaded_version, "kiosk/src/shell/update/", "deploy.pyc")
        self._doCommand("%s %s" % (upi.PYTHON_PATH, delpoly_py))

    def run(self):
        if self._need_update():
            self._update()


def main():
    try:
        up = UpateTool()
        up.run()
    except Exception as e:
        log.info("update tool: %s" % str(e))


if __name__ == '__main__':
    main()
