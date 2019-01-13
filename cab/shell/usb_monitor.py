import traceback
import subprocess
import time
import os

from cab.utils.c_log import init_log
from cab.utils.utils import (get_udisk, get_root_pwd, 
        get_udisk_path, play_video)

log = init_log("usb_monitor")

wifi_conf = "wifi.ini"
sys_wifi_conf = "/etc/wpa_supplicant/wpa_supplicant.conf"

def usb_monitor():
    udisk_exist = False
    while True:
        try:
            udisk_paths = get_udisk_path()
            if not udisk_paths:
                udisk_exist = True
            elif udisk_exist is False:
                for disk_path in udisk_paths:
                    user_conf = os.path.join(disk_path, wifi_conf)
                    if os.path.isfile(user_conf):
                        if set_wiif_config(user_conf, sys_wifi_conf):
                            play_video("please_reboot.mp3")
                        else:
                            play_video("config_failed.mp3")
                    else:
                        log.info("wifi.ini does not exist in: %s" % disk_path)

                udisk_exist = True

        except Exception as e:
            log.warning("usb_monitor: %s" % str(traceback.format_exc()))
        finally:
            time.sleep(1)

def set_wiif_config(user_config, sys_config):
    pwd = get_root_pwd() 
    cmd = "echo '{pwd}' | sudo -S cp '{user_config}' '{sys_config}'".format(pwd=pwd, 
            user_config=user_config, sys_config=sys_config)
    ret = subprocess.call(cmd, shell=True)
    log.info("set_wiif_config: %s" % ret)
    return ret


if __name__ == "__main__":
    usb_monitor()

