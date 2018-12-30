import compileall
import os

from cab.utils.machine_info import get_machine_home

if __name__ == '__main__':
    machine_path = os.path.join(get_machine_home(), "jprt")
    print ("compile: %s" % machine_path)

    compileall.compile_dir(machine_path, quiet=True)
    print ("compile end")
