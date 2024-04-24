#!/usr/bin/env python3


import sys, getopt, os, signal, importlib, json, socket, struct

BASE_DIR = os.path.dirname(sys.argv[0])

if not BASE_DIR: BASE_DIR = "."

sys.path.append(BASE_DIR)

PID_FILE = "/tmp/ixc_pass.pid"
LOG_FILE = "/tmp/ixc_pass.log"
ERR_FILE = "/tmp/ixc_pass_error.log"

import pywind.evtframework.evt_dispatcher as dispatcher
import pywind.lib.configfile as configfile
import pywind.lib.netutils as netutils

import ixc_proxy.lib.proxy as proxy
import ixc_proxy.lib.logging as logging
import ixc_proxy.lib.proc as proc


class ixc_passd(dispatcher.dispatcher):
    __configs = None
    __debug = None
    __DEVNAME = "ixcpass"

    __proxy = None

    def init_func(self, debug, configs):
        self.create_poll()

        self.__debug = debug
        self.__proxy = proxy.proxy()

        signal.signal(signal.SIGINT, self.__exit)

    @property
    def proxy(self):
        return self.__proxy

    def get_gateway_address(self):
        """获取网关地址
        """
        pass

    def config_local_network(self):
        """配置本地网络
        """
        pass

    def __exit(self, signum, frame):
        sys.exit(0)


def __start_service(debug):
    if not debug and os.path.isfile(PID_FILE):
        print("the pass server process exists")
        return

    if not debug:
        pid = os.fork()
        if pid != 0: sys.exit(0)

        os.setsid()
        os.umask(0)
        pid = os.fork()

        if pid != 0: sys.exit(0)
        proc.write_pid(PID_FILE)

    cls = ixc_passd()

    if debug:
        cls.ioloop(debug)
        return
    try:
        cls.ioloop(debug)
    except:
        logging.print_error()

    os.remove(PID_FILE)
    sys.exit(0)


def __stop_service():
    pid = proc.get_pid(PID_FILE)

    if pid < 0:
        print("cannot found pass process")
        return

    os.kill(pid, signal.SIGINT)


def __update_user_configs():
    pid = proc.get_pid(PID_FILE)

    if pid < 0:
        print("cannot found pass process")
        return

    os.kill(pid, signal.SIGUSR1)


def main():
    help_doc = """
    -d      debug | start | stop    debug,start or stop application
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:", [])
    except getopt.GetoptError:
        print(help_doc)
        return
    d = ""

    for k, v in opts:
        if k == "-d": d = v
        if k == "-u": u = v

    if not d:
        print(help_doc)
        return

    if d not in ("debug", "start", "stop"):
        print(help_doc)
        return

    debug = False

    if d == "stop":
        __stop_service()
        return

    if d == "debug": debug = True
    if d == "start": debug = False

    __start_service(debug)


if __name__ == '__main__': main()
