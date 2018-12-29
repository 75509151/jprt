import compileall
from cutils.kioskinfo import get_kiosk_home
import os


if __name__ == '__main__':
    kiosk_path = os.path.join(get_kiosk_home(), "kiosk")
    print "compile: %s" % kiosk_path

    compileall.compile_dir(kiosk_path, quiet=True)
    print "compile end"
