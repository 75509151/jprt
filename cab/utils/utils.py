import threading
import signal
import os
import subprocess
import uuid
import getpass
import fcntl

import magic
from cab.services import code
from cab import PRJ_DIR
from cab.utils.c_log import init_log
from cab.utils.console import embed

log = init_log("utils")


def file_lock(lock):
    def handle_func(func):
        def wrap(*args, **kw):
            with open(lock, "r") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    ret = func(*args, **kw)
                    return ret
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        return wrap
    return handle_func


def run_cmd(cmd, timeout=None):
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid) as process:
        try:
            out, stderr  = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGINT)  # send signal to the process group
            out, stderr = process.communicate()
        return process.returncode, out, stderr


@file_lock(__file__)
def get_ui_state():
    try:
        with open("/tmp/ui_state", "r") as f:
            return f.read().strip()
    except:
        return "hide"


@file_lock(__file__)
def set_ui_state(hide=False):
    st = "hide" if hide else "show"
    with open("/tmp/ui_state", "w") as f:
        f.write(st)


def get_mimetype(file_name):
    mime = magic.Magic(mime=True)
    return mime.from_file(file_name)


def run_in_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.setDaemon(True)
        t.start()
        return t
    return run


def get_db_uuid():
    return str(uuid.uuid4())


def extern_if(fn):
    setattr(fn, "__extern_if__", True)
    return fn


def get_extern_if(obj, cmd):
    fn = getattr(obj, cmd, None)
    if fn and getattr(fn, "__extern_if__") is True:
        return fn
    return None


def get_udisk_path(abs_path=True):
    udisk_mount_path = os.path.join("/media/", getpass.getuser())
    udisk_paths = os.listdir(udisk_mount_path)
    if abs_path and udisk_paths:
        return [os.path.join(udisk_mount_path, disk_path) for disk_path in udisk_paths]
    else:
        return udisk_paths


def get_udisk(sub_path=""):
    # TODO: only one udisk exist
    udisk_paths = get_udisk_path()
    if not udisk_paths or len(udisk_paths) > 1:
        return None

    udisk_path = udisk_paths[0]

    print(udisk_path)
    check_path = os.path.join(udisk_path, sub_path)
    print(check_path)
    return get_sub_files(check_path, sub_path)


def get_root_pwd():
    return "cereson121"

@run_in_thread
def play_video(video):
    video_path = os.path.join(PRJ_DIR, "resources", "sounds", video)

    cmd = "mplayer %s" % video_path
    os.system(cmd)


def get_sub_files(path, suffix=None):
    if not os.path.isdir(path):
        return None
    all_files = os.listdir(path)
    dirs = [dir_name + "/" for dir_name in all_files if os.path.isdir(os.path.join(path, dir_name))]
    files = [file for file in all_files if os.path.isfile(os.path.join(path, file))]
    dirs = [os.path.join(suffix, dir_name) for dir_name in dirs] if suffix else dirs
    files = [os.path.join(suffix, f) for f in files]  if suffix else files
    return dirs + files


def get_files(path, suffix=None):
    if not os.path.isdir(path):
        return None
    files = []
    for root, dirs, file_names in os.walk(path):
        for f in file_names:
            files.append(os.path.join(root, f))
    return files


def download_file(url, dst, retry=3):
    timeout = 600
    cmd = "wget -c  -t 3 --timeout=%s '%s' -O '%s'" % (timeout, url, dst)
    log.info(cmd)

    for i in range(retry):
        returncode, out, err = run_cmd(cmd, timeout)
        if returncode == 0:
            log.info("download success")
            return dst

        log.warning("download failed: (%s) %s" % (returncode, err) )

    raise code.DownloadError(url)


def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


if __name__ == "__main__":
    embed()
