import threading
import uuid

import magic

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

