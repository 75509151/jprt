import os
import time
import datetime
import socket
import fcntl
import struct
import os
import codecs
import json
import platform
from urllib.request import urlopen
from configparser import ConfigParser




def get_machine_type(real=False):
    g_machine_type = get_file_content(
        get_machine_home() + ".machineconfig/machine_type")

    if not real:
        if g_machine_type in ("q0", "m0"):
            g_machine_type = "m0"
        if g_machine_type in ("m1", "m1d", "m1s"):
            g_machine_type = "m1"
        elif g_machine_type in ("r2s", "r2sd", "r2f"):
            g_machine_type = "r2"

    return g_machine_type


def get_sys_ver():
    with open("/etc/issue", 'r') as f:
        content = f.read().lower()
    if content.find("debian") > -1:
        return 'debian'
    if content.find("ubuntu") > -1:
        return "ubuntu"
    else:
        return 'gentoo'


def get_sys_bit():
    return platform.architecture()[0].lower()


def get_file_content(file_path):
    try:
        with codecs.open(file_path, 'r', "utf-8") as f:
            return f.read().strip()
    except IOError:
        return ''


def set_file_content(file_path, content):
    with codecs.open(file_path, 'w', "utf-8") as f:
        f.write(content)


def get_machine_id():
    return get_file_content(get_machine_home() + ".machineconfig/machine_id")


def get_machine_name():
    return get_file_content(get_machine_home() + ".machineconfig/machine_name")


def set_machine_name(machine_name):
    set_file_content(get_machine_home() + ".machineconfig/machine_name", machine_name)


def get_machine_location():
    return get_file_content(get_machine_home() + ".machineconfig/machine_location")


def set_machine_location(machine_location):
    set_file_content(get_machine_home() +
                     ".machineconfig/machine_location", machine_location)


def get_client_id():
    return get_file_content(get_machine_home() + ".machineconfig/client_id")


def set_client_id(client_id):
    set_file_content(get_machine_home() + ".machineconfig/client_id", client_id)


def set_machine_server(machine_type, default_server=""):
    set_file_content(get_machine_home() + ".machineconfig/machine_" +
                     machine_type + "_server", default_server)


def get_machine_server(s_type, default_serve=""):
    """
    :param s_type: api, access, update
    :return: ser
    """
    ser = get_file_content("/home/mm/.machineconfig/machine_" + s_type + "_server")
    if not ser:
        set_machine_server(s_type, default_serve)
        ser = default_serve
    return ser


def get_machine_home():
    return get_file_content("/home/mm/.machineconfig/machine_home")


def get_ckc_version():
    """ get the machine version
    """
    return get_file_content("/home/mm/.machineconfig/latest_version")


def get_ckc_upgrade_time():
    return get_file_content("/home/mm/.machineconfig/upgrade_time")


def get_timezone():
    try:
        rs = os.popen("cat /etc/timezone")
        return rs.read().strip()
    except:
        return 'Unknown'


def get_eth_ip():
    lo = '127.0.0.1'
    ip = '127.0.0.1'
    try:
        ifname = os.popen(
            "/sbin/ifconfig |grep eth|awk '{print $1}'").read().split('\n')
        for eth in ifname:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ip = socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(), 0x8915, struct.pack('256s', eth[:15]))[20:24])
            except:
                ip = lo
            if ip == lo:
                continue
            else:
                break
    except:
        return lo
    return ip


def get_external_ip():
    GET_IP_API = "myip.ipip.net"
    try:
        f =urlopen(GET_IP_API, timeout=15)
        ip = json.loads(f.read())
        return ip
    except:
        return ""


def get_ifname():
    # interface name must be start with 'e'
    ifname_list = os.popen(
        "/sbin/ifconfig |grep '^e'|awk '{print $1}'").read().split('\n')
    print (ifname_list)
    for ifname in ifname_list:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])
        except:
            ip = None
        if ip:
            return ifname.strip()


def get_hw_addr(ifname="eth0"):
    try:
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
        '''
        mac = os.popen(
            "/sbin/ifconfig |awk '/eth/{print $5}'").read().split('\n')[0]
        return mac
    except:
        return ""


def get_linux_date():
    return time.strftime("%a %b %d %H:%M:%S %Z %Y")


def get_cur_time(time_fmt="%Y-%m-%d %H:%M:%S"):
    return time.strftime(time_fmt)


def get_cur_utctime(time_fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.utcnow().strftime(time_fmt)


def get_machine_version_lock():
    """
    Get the update version lock for reseaons.
    @return: The version number string format or False.
    """
    try:
        with open(get_machine_home() + '/.machineconfig/version_lock', 'r') as f:
            version_lock = f.read().strip()
    except:
        version_lock = False
    return version_lock


def get_active_information():
    information = ""
    try:
        with open(get_machine_home() + '/.machineconfig/.active_information', 'r') as f:
            information = f.read().strip()
    except:
        pass
    return information


def set_active_information(active_information=""):
    with open(get_machine_home() + '/.machineconfig/.active_information', "wb") as fd:
        fd.write(active_information)


def set_download_lock(lock="False"):
    with open(get_machine_home() + '/.machineconfig/.download_lock', "wb") as fd:
        fd.write(lock)


def get_download_status():
    try:
        with open(get_machine_home() + '/.machineconfig/.download_lock', 'r') as f:
            s = f.read().strip().split(',')
            lock = s[0]
            if not lock:
                lock = "False"
            last_download_time = s[1]
            if int(time.time()) - int(last_download_time) > 60 * 30:
                lock = "False"
    except:
        lock = "False"
    return lock


def set_card_present_flag(present):
    """ set the card present flag to a file
    """
    file_path = os.path.join(get_machine_home(), "var", "card_reader_error")
    with open(file_path, 'w') as f:
        f.write(present)


def get_card_present_flag():
    """ get the card present flag from a file
    """
    file_path = os.path.join(get_machine_home(), "var", "card_reader_error")
    if not os.path.exists(file_path):
        flag = ""
    else:
        with open(file_path, 'r') as f:
            flag = f.read().strip()
    return flag


def get_config(config_type):
    """
    """
    if config_type == "ckc":
        config_file = os.path.join(
            get_machine_home(), "machine", "config", "ckc.ini")
    elif config_type == "gui":
        config_file = os.path.join(
            get_machine_home(), "machine", "config", "gui.ini")
    elif config_type == "simulator":
        config_file = os.path.join(
            get_machine_home(), "machine", "config", "simulator.ini")
    else:
        raise Exception("invalid config_type: %s" % config_type)
    config = ConfigParser()
    config.read(config_file)
    return config



