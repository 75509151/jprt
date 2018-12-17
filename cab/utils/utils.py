import threading

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
