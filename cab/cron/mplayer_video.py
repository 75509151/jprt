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
from math import log as math_log
from cab import PRJ_DIR

__all__ = ["OmxPlayer"]

config = get_config("ckc")
video_path = config.get("videos", "path")
db = get_db_instance()

log = init_log("video")

wx_width = 865

screen_width = 1920
screen_height = 1080

pro = float(1920) / float(1080)
mini_omx_h = int((screen_width - wx_width) / pro)
mini_omx_y = int((screen_height - mini_omx_h) / 2)


def count_omx_vol(vol_percent):
    try:
        float_percent = float(vol_percent) / 100
    except Exception as e:
        float_percent = 0.01
    try:
        return int(2000 * (math_log(float_percent, 10)))
    except Exception as e:
        return -4000


class OmxPlayer(object):
    """docstring for OmxPlayer"""
    DBUS = os.path.join(PRJ_DIR, "cab" ,"shell", "dbuscontrol.sh")

    (PAUSE_ST, PLAY_ST, IDLE_ST) = range(3)

    @staticmethod
    def play(video, mode="full", vol_percent=100, output="local", loop=False):
        """
        @mode: full or mini

        """
        assert mode in ("full", "mini")
        vol = count_omx_vol(vol_percent)
        if mode == "full":
            cmd = "omxplayer -o {output} --vol {vol} --no-osd --aspect-mode stretch '{video}'".format(
                video=video, output=output, vol=vol)
        elif mode == "mini":
            cmd = "omxplayer -o {output} --vol {vol} --no-osd --aspect-mode stretch --win {x},{y},{w},{h} '{video}'".format(
                x=1, y=mini_omx_y,
                w=screen_width- wx_width, h=mini_omx_h + mini_omx_y, video=video, output=output, vol=vol)
        if loop:
            cmd = cmd.replace("omxplayer", "omxplayer --loop")
        log.info("mode: %s, %s" % (mode, cmd))
        os.system(cmd)

    @staticmethod
    def set_video_pos(x, y, w, h):
        cmd = '{dbus} setvideopos {x} {y} {w} {h}'.format(
            dbus=OmxPlayer.DBUS, x=x, y=y, w=w, h=h)
        ret = subprocess.check_call(cmd, shell=True)
        log.info("cmd : %s, ret:%s" % (cmd, ret))
        return ret

    @staticmethod
    def set_aspectmode(mode="stretch"):
        assert mode in ("fill", "default", "stretch", "letterbox")
        cmd = '{dbus} setaspectmode {mode}'.format(
            dbus=OmxPlayer.DBUS, mode=mode)
        ret = subprocess.call(cmd, shell=True)
        log.info("cmd : %s, ret:%s" % (cmd, ret))
        return ret

    @staticmethod
    def do_cmd(cmd):
        cmd = '{dbus} {cmd}'.format(dbus=OmxPlayer.DBUS, cmd=cmd)
        ret = subprocess.call(cmd, shell=True)
        log.info("cmd : %s, ret:%s" % (cmd, ret))
        return ret

    @staticmethod
    def pause():
        if OmxPlayer.get_status() != OmxPlayer.PAUSE_ST:
            cmd = '{dbus} pause'.format(dbus=OmxPlayer.DBUS)
            ret = subprocess.call(cmd, shell=True)
            log.info("cmd : %s, ret:%s" % (cmd, ret))

    @staticmethod
    def contin():
        if OmxPlayer.get_status() != OmxPlayer.PLAY_ST:
            cmd = '{dbus} pause'.format(dbus=OmxPlayer.DBUS)
            ret = subprocess.call(cmd, shell=True)
            log.info("cmd : %s, ret:%s" % (cmd, ret))

    @staticmethod
    def get_status():
        cmd = '{dbus} status'.format(dbus=OmxPlayer.DBUS)
        try:
            pro = pexpect.spawn(cmd)

            index = pro.expect(
                ['Paused: true', 'Paused: false', 'Error', pexpect.TIMEOUT])
            log.info("st: %s" % index)
            if index == 0:
                return OmxPlayer.PAUSE_ST
            elif index == 1:
                return OmxPlayer.PLAY_ST
            elif index in (2, 3):
                return OmxPlayer.IDLE_ST
            else:
                log.info("unexpect st")
        except Exception:
            log.info("unexpect err")
        return OmxPlayer.IDLE_ST

    @staticmethod
    def destroy():
        os.system("pkill omxplayer")

    @staticmethod
    def hide():
        cmd = '{dbus} hidevideo'.format(dbus=OmxPlayer.DBUS)
        ret = subprocess.call(cmd, shell=True)
        log.info("cmd : %s, ret:%s" % (cmd, ret))

    @staticmethod
    def show():
        cmd = '{dbus} unhidevideo'.format(dbus=OmxPlayer.DBUS)

        ret = subprocess.call(cmd, shell=True)
        log.info("cmd : %s, ret:%s" % (cmd, ret))


class VideoCtrl(object):

    def __init__(self):
        super(VideoCtrl, self).__init__()

    def change_mode(self, mode="full"):
        assert mode in ("full", "mini")
        if mode == "mini":
            OmxPlayer.set_aspectmode("stretch")
            OmxPlayer.set_video_pos(
                1, mini_omx_y, screen_width - wx_width, mini_omx_h + mini_omx_y)
            # OmxPlayer.contin()
        elif mode == "full":
            OmxPlayer.set_aspectmode("stretch")
            OmxPlayer.set_video_pos(0, 0, 0, 0)
            # OmxPlayer.contin()
        elif mode == "hide":
            OmxPlayer.hide()
        elif mode == "pause":
            OmxPlayer.pause()
        elif mode == "continue":
            OmxPlayer.contin()
        elif mode in ("volumeup", "volumedown"):
            OmxPlayer.do_cmd(mode)


def omxplayer_exist():
    omxplayer_pid = subprocess.Popen("pgrep omxplayer", shell=True, stdout=subprocess.PIPE).stdout.read()
    return True if omxplayer_pid else False


@run_in_thread
def update_video_shape():
    time.sleep(3)
    last_st = ""
    video_ctrl = VideoCtrl()
    log.info("update shape thread")
    while True:
        try:
            if omxplayer_exist():
                try:
                    ui_st = get_ui_state()
                    if ui_st != last_st:
                        mode = "mini" if ui_st != "hide" else "full"
                        video_ctrl.change_mode(mode)
                        last_st = ui_st
                except subprocess.CalledProcessError:
                    log.info("unlive")
        except Exception as e:
            log.info("update_shape: %s" % str(e))

        time.sleep(0.3)


def main():
    OmxPlayer.destroy()
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
                        # omxplayer_output = db.get_kv(
                            # "machine_config", "omxplayer_output")
                        # omxplayer_volume = db.get_kv(
                            # "machine_config", "omxplayer_volume_percent")
                        # TODO: need use video_ctrl to control play
                        # if not update_shape_start_flag:
                            # update_video_shape()
                            # update_shape_start_flag = True
                        # mode = "full" if get_ui_state() == "hide" else "mini"
                        # OmxPlayer.play(
                            # video, mode, vol_percent=omxplayer_volume, output=omxplayer_output, loop=True)
                        OmxPlayer.play(
                            video, "full", loop=True)
        except Exception as e:
            log.info("main err:%s" % str(e))
            time.sleep(1)


if __name__ == '__main__':
    main()

