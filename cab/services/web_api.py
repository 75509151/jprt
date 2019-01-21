import requests
import json
from cab.utils.machine_info import (get_config, get_machine_id,
                                    get_machine_type,
                                    get_hw_addr)
from cab.utils.c_log import init_log
from cab.utils.console import embed

log = init_log("web_api")

WEB_SERVER = get_config("ckc").get("server", "web_server")


def _http_call(api, data, timeout=None, json_reply=True):
    url = "%s%s" % (WEB_SERVER, api)
    d = json.dumps(data)
    try:
        res = requests.post(url, data=d)
        log.info("%s %s" % (res.url, d))
        if json_reply:
            reply = res.json()
            log.info("response: %s" % reply)
            return reply
        else:
            log.info("respon" % (res.text))
            return res.text
    except Exception as e:
        log.warning("%s %s" % (url, d))
        raise e


def upload_file(file, retry=3):
    api = "/Api/uploadfile"
    url = "%s%s" % (WEB_SERVER, api)
    data = {"machine_id": get_machine_id(),
            "file": file}
    files = {"file": open(file, "r")}
    for i in range(retry):
        res = requests.post(url, data, files=files)
        res = res.json()
        log.info("response: %s" % res)
        if res["status"] == 1:
            return True
        else:
            continue
    return False


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


if __name__ == "__main__":
    embed()
