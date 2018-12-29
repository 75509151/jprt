# -*- coding: UTF-8 -*-
"""
Created on 2017-10-26

@author: jay
"""
import os
import hashlib
import shutil
import subprocess
import logging
import json
import codecs
import fcntl
import time

from update_exceptions import *


def check_and_creat_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def init_log():
    log = logging.getLogger('auto_update')
    log_path = os.path.join("/home/mm/var/log")
    check_and_creat_path(log_path)
    log_file = os.path.join(log_path, "update.log")
    handle = logging.FileHandler(log_file)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s : %(name)-7s: %(levelname)-8s %(message)s')
    chf = logging.Formatter('%(levelname)-8s %(message)s')
    handle.setFormatter(formatter)
    ch.setFormatter(chf)
    log.addHandler(handle)
    log.addHandler(ch)
    log.setLevel(logging.INFO)
    return log


class ProcessLock():

    def __init__(self, file_name):
        self.file_name = file_name
        self.handle = open(file_name, "w")

    def acquire(self, block=True):
        if block:
            fcntl.flock(self.handle, fcntl.LOCK_EX)
        else:
            fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)

    def __del__(self):
        try:
            self.handle.close()
            # os.remove(self.filename)  # if remove
        except Exception:
            pass


def run_with_eat_exceptions(func):
    def wrap(*args, **kwargs):
        ret = func(*args, **kwargs)
        return ret
    return wrap


def change_working_path(path):
    os.chdir(path)


def get_home_dir():
    return get_kiosk_name()


def cp_folder(source_path, dst_path, overwrite=True):
    print "cp %s to %s" % (source_path, dst_path)
    if os.path.exists(dst_path):
        print "dst path exist. delete it: %s" % dst_path
        shutil.rmtree(dst_path)
    # os.makedirs(dst_path)
    shutil.copytree(source_path, dst_path)
    # ret = os.system("cp -rf %s %s " % (source_path, dst_path))
    # if ret:
    #     raise Exception("cp folder failed")


def get_recursive_file_list(path, only_file=True):
    current_files = os.listdir(path)
    all_files = []
    for file_name in current_files:
        full_file_name = os.path.join(path, file_name)

        if os.path.isdir(full_file_name):
            if not only_file:
                all_files.append(full_file_name)
            next_level_files = get_recursive_file_list(full_file_name)
            all_files.extend(next_level_files)
        else:
            all_files.append(full_file_name)

    return all_files


def generate_md5_info(path, output_path=None, info_name="md5.json"):
    if output_path and not os.path.isabs(output_path):
        raise Exception("output_path is not absolute path")
    files = get_recursive_file_list(path)
    info_dict = {}
    info_dict = {"files_count": len(files)}

    for file in files:
        file_md5 = md5(file)
        relative_file_name = file.replace(path + "/", "")
        info_dict[relative_file_name] = file_md5

    if output_path is not None:
        info_file = os.path.join(output_path, info_name)
        with open(info_file, "w") as f:
            json.dump(info_dict, f)

    return info_dict


def get_bool_input():
    yes = set(['yes', 'y', 'y'])
    no = set(['no', 'n'])
    while True:
        choice = raw_input().lower()
        if choice in yes:
            return True
        elif choice in no:
            return False
        else:
            print "Please respond with 'yes' or 'no'"


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def do_cmd(cmd, raise_ex=True):
    print "do cmd: %s" % cmd
    child = subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    child.wait()
    out = child.stdout.read()
    err = child.stderr.read()
    if raise_ex and (child.returncode or err):
        raise CmdFailedExecetion("do cmd get unexpect result")
    return child.returncode, out, err


def get_cur_time(time_fmt="%Y-%m-%d %H:%M:%S"):
    return time.strftime(time_fmt)


def set_ckc_version(ver):
    """
    set kiosk version
    """
    version_path = "/home/mm/.kioskconfig/latest_version"
    if os.path.exists(version_path):
        with open(version_path, 'w') as f:
            f.write(ver)
        with open("/home/mm/.kioskconfig/upgrade_time", 'w') as ff:
            ff.write(get_cur_time())


def set_kiosk_downloaded_version(version):
    from update_info import VERSION_DOWN
    with open(VERSION_DOWN, "w") as f:
        f.write(version)


def get_kiosk_downloaded_version():
    from update_info import VERSION_DOWN
    if os.path.exists(VERSION_DOWN):
        with open(VERSION_DOWN, 'r') as file:
            content = file.readline().strip()
        return content
    else:
        return ""


def get_sys_ver():
    with open("/etc/issue", 'r') as f:
        content = f.read().lower()
    if content.find("debian") > -1:
        return 'debian'
    else:
        return 'gentoo'


def get_file_content(file_path):
    try:
        with codecs.open(file_path, 'r', "utf-8") as f:
            return f.read().strip()
    except IOError:
        return ''


def set_file_content(file_path, content):
    with codecs.open(file_path, 'w', "utf-8") as f:
        f.write(content)


def get_kiosk_id():
    return get_file_content(get_kiosk_home() + ".kioskconfig/kiosk_id")


def get_kiosk_payurl():
    return get_file_content(get_kiosk_home() + ".kioskconfig/kiosk_payurl")


def get_kiosk_type(real=False):
    g_kiosk_type = get_file_content(
        get_kiosk_home() + ".kioskconfig/kiosk_type")

    if not real:
        if g_kiosk_type in ["q0", "m0"]:
            g_kiosk_type = "m0"
        # if g_kiosk_type in ["m1", "l1"]:
            # g_kiosk_type = "m1"
        if g_kiosk_type in ["r2s", "r2sd"]:
            g_kiosk_type = "r2"
    return g_kiosk_type


def get_kiosk_name():
    return get_file_content(get_kiosk_home() + ".kioskconfig/kiosk_name")


def set_kiosk_name(kiosk_name):
    set_file_content(get_kiosk_home() + ".kioskconfig/kiosk_name", kiosk_name)


def get_kiosk_location():
    return get_file_content(get_kiosk_home() + ".kioskconfig/kiosk_location")


def set_kiosk_location(kiosk_location):
    set_file_content(get_kiosk_home() +
                     ".kioskconfig/kiosk_location", kiosk_location)


def get_client_id():
    return get_file_content(get_kiosk_home() + ".kioskconfig/client_id")


def set_client_id(client_id):
    set_file_content(get_kiosk_home() + ".kioskconfig/client_id", client_id)


def set_kiosk_server(kiosk_type, default_server=""):
    set_file_content(get_kiosk_home() + ".kioskconfig/kiosk_" +
                     kiosk_type + "_server", default_server)


def get_kiosk_server(s_type, default_serve=""):
    """
    :param s_type: api, access, update
    :return: ser
    """
    ser = get_file_content("/home/mm/.kioskconfig/kiosk_" + s_type + "_server")
    if not ser:
        set_kiosk_server(s_type, default_serve)
        ser = default_serve
    return ser


def get_kiosk_home():
    return get_file_content("/home/mm/.kioskconfig/kiosk_home")


def get_ckc_version():
    """ get the kiosk version
    """
    return get_file_content("/home/mm/.kioskconfig/latest_version")


if __name__ == '__main__':
    generate_md5_info("/home/mm/abox_release", "/home/mm/")
