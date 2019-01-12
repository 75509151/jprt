import threading
import os
import subprocess
import uuid
import getpass
import fcntl

import magic
from cab.services import code

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


@file_lock(__file__)
def get_ui_state():
    try:
        with open("/tmp/ui_state","r") as f:
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


def get_udisk(sub_path="/", suffix=None):
    #TODO: only one udisk exist
    udisk_mount_path = os.path.join("/media/", getpass.getuser())
    udisk_paths = os.listdir(udisk_mount_path)
    if not udisk_paths or len(udisk_paths)>1:
        return None

    udisk_path = udisk_paths[0]
    check_path = os.path.join(udisk_path, sub_path)
    return get_sub_files(check_path)

def get_sub_files(path):
    if not os.path.isdir(path):
        return None
    all_files = os.listdir(path)
    dirs = [dir_name+"/" for dir_name in all_files if os.path.isdir(os.path.join(path,dir_name))]
    files = [file for file in all_files if os.path.isfile(os.path.join(path,file))]
    return dirs+files

def get_files(path, suffix=None):
    if not os.path.isdir(path):
        return None
    files = []
    for root, dirs, file_names in os.walk(path):
        for f in file_names:
            files.append(os.path.join(root, f))
    return files

def download_file(url, dst="/tmp/", retry=3):
    new_name = str(uuid.uuid4())
    cmd = "wget -c  -t 3 --timeout=600 %s -O %s" % new_name
    for i in range(retry):
        ret = subprocess.call(cmd)
        if ret == 0:
            return os.path.join(dst, new_name)
    raise code.DownloadError(url)


def upload_file(src, dst, retry=3, port=22, rename=True):
    if rename:
        new_name = str(uuid.uuid4())


    ssh_cmd = "ssh -p %s" % port
    cmd = "rsync -avz -e '{ssh_cmd}' {src} {dst} ".format(ssh_cmd, src, dst)
    for i in range(retry):
        ret = subprocess.call(cmd)
        if ret == 0:
            return
    raise code.UploadError()


def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

