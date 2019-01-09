import threading
import os
import subprocess
import uuid

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


def download_file(url, dst="/tmp/", retry=3):
    new_name = str(uuid.uuid4())
    for i in range(retry):
        cmd = "wget -c  -t 3 --timeout=600 %s -O %s"
        ret = subprocess.call(cmd)
        if ret == 0:
            return os.path.join(dst, new_name)
    raise DownloadError()


