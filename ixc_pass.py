#!/usr/bin/env python3


import sys, getopt, os, signal, importlib, json, socket, struct

BASE_DIR = os.path.dirname(sys.argv[0])

if not BASE_DIR: BASE_DIR = "."

sys.path.append(BASE_DIR)

PID_FILE = "/tmp/ixc_pass.pid"
LOG_FILE = "/tmp/ixc_pass.log"
ERR_FILE = "/tmp/ixc_pass_error.log"

import pywind.evtframework.evt_dispatcher as dispatcher
import pywind.lib.netutils as netutils
import ixc_proxy.lib.logging as logging
import ixc_proxy.lib.proc as proc
import ixc_proxy.lib.osnet as osnet
import ixc_proxy.handlers.forward as fwd
import ixc_proxy.handlers.tapdev as tapdev


class ixc_passd(dispatcher.dispatcher):
    __debug = None
    __DEVNAME = "ixcpass node"
    __server_address = None
    __tap_fd = None
    __fwd_fd = None
    __use_ipv6 = None
    __ifname = None

    def init_func(self, debug, device_name, ifname, host, use_ipv6):
        self.__tap_fd = -1
        self.__fwd_fd = -1
        self.__server_address = host
        self.__debug = debug
        self.__DEVNAME = device_name
        self.__use_ipv6 = use_ipv6
        self.__ifname = ifname

        if not debug:
            sys.stdout = open(LOG_FILE, "w")
            sys.stderr = open(ERR_FILE, "w")

        self.create_poll()
        self.start()

    def start(self):
        self.__tap_fd = self.create_handler(-1, tapdev.tap_handler)
        self.__fwd_fd = self.create_handler(-1, fwd.forward_handler, is_ipv6=self.__use_ipv6)

        self.config_local_network()

    def server_addr(self):
        return self.__server_address

    def send_msg_to_router(self, message: bytes):
        self.get_handler(self.__fwd_fd).send_msg(message)

    def send_msg_to_local(self, message: bytes):
        self.get_handler(self.__tap_fd).send_msg(message)

    def config_local_network(self):
        """配置本地网络
        """
        cmds = [
            "ip link add name ixcpassbr type bridge",
            "ip link set dev ixcpassbr up",
            # "echo 1 >/proc/sys/net/ipv6/conf/all/forwarding",
            # "echo 1 > /proc/sys/net/ipv4/ip_forward"
        ]

        for cmd in cmds: os.system(cmd)
        cmd = "ip link set dev %s master ixcpassbr" % (self.__ifname,)
        os.system(cmd)
        cmd = "ip link set dev %s master ixcpassbr" % (self.tap_devname(),)
        os.system(cmd)
        os.system("ip link set %s promisc on" % self.__ifname)
        os.system("ip link set %s promisc on" % self.tap_devname())
        os.system("ip link set %s up" % self.__ifname)
        # 关闭外网IPv6支持
        os.system("echo 1 > /proc/sys/net/ipv6/conf/ixcpassbr/disable_ipv6")
        os.system("echo 1 > /proc/sys/net/ipv6/conf/%s/disable_ipv6" % self.tap_devname())

    def unconfig_local_network(self):
        os.system("ip link set %s down" % self.__ifname)
        os.system("ip link set ixcpassbr down")
        os.system("ip link del ixcpassbr")

    def tap_devname(self):
        return "ixcpass"

    def myname(self):
        return self.__DEVNAME

    def release(self):
        if self.__fwd_fd >= 0:
            self.delete_handler(self.__fwd_fd)
        if self.__tap_fd >= 0:
            self.delete_handler(self.__tap_fd)
        self.unconfig_local_network()


def __start_service(debug, device_name, ifname, host, use_ipv6):
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
        try:
            cls.ioloop(debug, device_name, ifname, host, use_ipv6)
        except:
            cls.release()
            logging.print_error()
        return
    try:
        cls.ioloop(debug, device_name, ifname, host, use_ipv6)
    except:
        cls.release()
        logging.print_error()

    os.remove(PID_FILE)
    sys.exit(0)


def __stop_service():
    pid = proc.get_pid(PID_FILE)

    if pid < 0:
        print("cannot found pass process")
        return
    try:
        os.kill(pid, signal.SIGINT)
    except:
        pass
    os.remove(PID_FILE)


def main():
    help_doc = """
    -d                  debug | start | stop    debug,start or stop application
    --ifname=           set local ethernet card
    --host=             set server address,if not set,it will use default gateway
    [--use-ipv6]        use ipv6 connect to host
    [--device-name=]    set device name
    
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:", ['ifname=', '--use-ipv6', "device-name=", "host="])
    except getopt.GetoptError:
        print(help_doc)
        return

    if len(sys.argv) < 3:
        print(help_doc)
        return

    if not os.path.isfile("/usr/bin/ip"):
        print("not found linux ip command,please install it")
        return

    d = ""
    device_name = ""
    ifname = ""
    use_ipv6 = False
    host = None

    for k, v in opts:
        if k == "-d": d = v
        if k == "--device-name": device_name = v
        if k == "--ifname": ifname = v
        if k == "--use-ipv6": use_ipv6 = True
        if k == "--host": host = v

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

    if ifname == "":
        print("ERROR:please set ifname")
        return

    if ifname not in osnet.get_if_net_devices():
        print("ERROR:not found system ethernet card %s" % ifname)
        return

    if not host:
        print("ERROR:please set remote host")
        return

    if use_ipv6 and netutils.is_ipv4_address(host):
        print("ERROR:not ipv6 address %s" % host)
        return

    if not device_name:
        if os.path.isfile("/etc/hostname"):
            with open("/etc/hostname", "r") as f:
                device_name = f.read()
            f.close()
        else:
            device_name = "ixcpass node"
        ''''''
    if d == "debug": debug = True
    if d == "start": debug = False

    __start_service(debug, device_name, ifname, host, use_ipv6)


if __name__ == '__main__': main()
