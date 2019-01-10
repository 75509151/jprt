import threading
import os
import subprocess
import uuid
import getpass

import magic
from cab.services.code import DownloadError

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
    return get_sub_files(check_path, suffix)

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
    for i in range(retry):
        cmd = "wget -c  -t 3 --timeout=600 %s -O %s"
        ret = subprocess.call(cmd)
        if ret == 0:
            return os.path.join(dst, new_name)
    raise DownloadError()


