#!/usr/bin/env python3
# 守护程序,程序意外退出时自动重启
import getopt, os, sys, signal, time

BASE_DIR = os.path.dirname(sys.argv[0])

if not BASE_DIR: BASE_DIR = "."

sys.path.append(BASE_DIR)

import ixc_proxy.lib.proc as proc

PID_PATH = "/tmp/ixc_pass.pid"
MYPID_PATH = "/tmp/ixc_pass_monitor.pid"

import ixc_proxy.lib.osnet as osnet
import pywind.lib.netutils as netutils


def stop_myself():
    if not os.path.isfile(MYPID_PATH):
        print("ERROR:not found ixc_pass_monitor process")
        return

    pid = proc.get_pid(MYPID_PATH)
    if pid < 0: return
    try:
        os.kill(pid, signal.SIGINT)
    except:
        pass

    os.remove(MYPID_PATH)


def stop_ixcpass():
    cmd = "%s %s/ixc_pass.py -d stop" % (sys.executable, BASE_DIR,)
    os.system(cmd)


def start_ixcpass(args: list):
    cmd = "%s %s/ixc_pass.py -d start %s" % (sys.executable, BASE_DIR, " ".join(args))
    os.system(cmd)


def start(args: list):
    pid = os.fork()
    if pid != 0: sys.exit(0)

    up_time = time.time()
    is_exited = False

    proc.write_pid(MYPID_PATH)

    # 等待操作系统其他模块加载完成
    time.sleep(60)

    try:
        while 1:
            if not is_exited: up_time = time.time()
            if not os.path.isfile(PID_PATH):
                if not is_exited:
                    is_exited = True
                    continue
                now = time.time()
                if now - up_time >= 10:
                    start_ixcpass(args)
                    is_exited = False
                ''''''
            time.sleep(10)
        ''''''
    except KeyboardInterrupt:
        stop_ixcpass()


def main():
    help_doc = """
      -d                 start | stop    debug,start or stop application
      --ifname=          set local ethernet card
      --host=            set server address,if not set,it will use default gateway
      [--use-ipv6]       use ipv6 connect to host
      [--device-name=]   set device name

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

    if d not in ("start", "stop"):
        print(help_doc)
        return

    if d == "stop":
        stop_myself()
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
        device_name = device_name.replace("\r", "")
        device_name = device_name.replace("\n", "")

    args = [
        "--device-name=%s" % device_name,
        "--ifname=%s" % ifname,
        "--host=%s" % host,
    ]
    if use_ipv6:
        args.append("--use-ipv6")
    start(args)


if __name__ == '__main__': main()
