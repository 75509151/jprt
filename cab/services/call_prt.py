import threading
import queue
import time

from cab.services.protocol import Protocol, Request
from cab.utils.client import Client
from cab.utils.c_log import init_log
# from cab.utils.machine_info import  get_server


HOST = "127.0.0.1"
PORT = 1507

class CallPrt(threading.Thread):

    def __init__(self):
        self.stop = threading.Event()
        self.cli = Client(HOST, PORT)
        self.task = queue.Queue()

    def get_request(self):


    def run(self):
        while not self.stop.isSet():
            




