
from cab.api.protocol import Protocol, Request
from cab.utils.client import Client
# from cab.utils.machine_info import  get_server

__all__ = ["call_once"]

HOST = "127.0.0.1"
PORT = 1507


def call_once(func, params=None, timeout=60):
    cli = Client(HOST, PORT)
    r = Request(func, params)
    _id, data = Protocol().request_to_raw(r)
    cli.send(data)
    cli.recv(timeout=6)
    cli.close()

    return


if __name__ =="__main__":
    call_once("test", {"t": 1})

