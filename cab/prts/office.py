import os

def print_file(document, prniter_name):
    if not os.path.isfile(document):
        raise Exception("not file")
    cmd = "/usr/bin/libreoffice --headless --invisible --pt '%s' 'document'" % (printer_name, document)
    return os.system(cmd)


