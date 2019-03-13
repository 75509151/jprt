# coding: utf-8
import traceback
import subprocess
import pexpect
import time
import threading
import os
from cab.utils.utils import (get_ui_state,
                             run_in_thread)
from cab.utils.c_log import init_log
from cab.utils.machine_info import get_config
from cab.db.dbm import get_db_instance


config = get_config("ckc")
video_path = config.get("videos", "path")

log = init_log("video")


def main():
    stop = False
    update_shape_start_flag = False
    while not stop:
        try:

            for root, dirs, files in os.walk(video_path, topdown=False):
                if not files:
                    time.sleep(1)
                for name in files:
                    video = os.path.join(root, name)
                    if os.path.exists(video):
                        ret = os.system("mplayer -vo x11 '%s'  -fs fullscreen" % video )
                        if ret:
                            time.sleep(1)
        except Exception as e:
            log.info("main err:%s" % str(e))
            time.sleep(1)


if __name__ == '__main__':
    main()
