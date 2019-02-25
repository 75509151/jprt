import requests
import json
from cab.utils.machine_info import (get_config, get_machine_id,
                                    get_machine_type,
                                    get_hw_addr)
from cab.utils.c_log import init_log
from cab.utils.console import embed

log = init_log("web_api")

WEB_SERVER = get_config("ckc").get("server", "web_server")


def _http_call(api, data, files=None, jsonly=True):
    result = {"status": "error", "info": ""}
    url = "%s%s" % (WEB_SERVER, api)
    if jsonly:
        d = json.dumps(data)
    else:
        d = data
    try:
        if files is None:
            res = requests.post(url, data=d)
        else:
            res = requests.post(url, data=d, files=files)

        log.info("%s %s" % (res.url, d))
        result = json.loads(res.json())
        log.info("response: %s" % result)
    except requests.exceptions.HTTPError as err:
        log.info("Http Error: %s" % err)
        result = {"status": "http error", "info": str(err)}
    except requests.exceptions.ConnectionError as err:
        log.info("Error Connecting:%s" % err)
        result = {"status": "connect error", "info": str(err)}
    except requests.exceptions.Timeout as err:
        log.info("Timeout Error: %s" % err)
        result = {"status": "timeout error", "info": str(err)}
    except requests.exceptions.RequestException as err:
        log.info("OOps: Something Else: %s" % err)
        result = {"status": "request error", "info": str(err)}
    except Exception as e:
        log.warning("%s %s" % (url, d))
        result["info"] = str(e)
    return result


def upload_file(file, dst=""):
    api = "/Api/uploadfile"
    url = "%s%s" % (WEB_SERVER, api)
    log.info("upload: %s" % file)
    data = {"machine_id": get_machine_id()}
    if not dst:
        files = {"file": open(file, "rb")}
    else:
        files = {"file": (dst, open(file, "rb"))}
    return _http_call(api, data, files, jsonly=False)


def register():
    api = "/Api/register"

    machine_id = get_machine_id()
    machine_type = get_machine_type()
    mac = get_hw_addr()

    params = {"id": machine_id,
              "machine_type": machine_type,
              "mac": mac}
    return _http_call(api, params)


def report_printer_params(params):
    api = "/Api/report_printer_params"
    machine_id = get_machine_id()
    params = {"machine_id": machine_id,
              "params": params}
    return _http_call(api, params)


def report_printer_status(status):
    api = "/Api/report_printer_status"
    machine_id = get_machine_id()
    params = {"machine_id": machine_id,
              "params": status}
    return _http_call(api, params)


def print_notify(trans_id, code, msg=""):
    api = "/Api/report_printer_status"
    params = {"trans_id": trans_id,
              "code": code,
              "msg": msg}

    return _http_call(api, params)


if __name__ == "__main__":
    embed()
