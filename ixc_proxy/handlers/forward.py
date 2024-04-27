#!/usr/bin/env python3
import time, socket, struct

import pywind.evtframework.handlers.udp_handler as udp_handler


class forward_handler(udp_handler.udp_handler):
    __time = None

    def init_func(self, creator_fd, is_ipv6=False):
        self.__time = time.time()
        if is_ipv6:
            fa = socket.AF_INET6
        else:
            fa = socket.AF_INET

        s = socket.socket(fa, socket.SOCK_DGRAM)
        self.set_socket(s)
        self.connect((self.dispatcher.server_addr(), 1999))
        self.register(self.fileno)
        self.add_evt_read(self.fileno)
        self.set_timeout(self.fileno, 10)

        return self.fileno

    def send_msg(self, message: bytes):
        self.send_to_router(8, message)

    def udp_readable(self, message, address):
        if len(message) < 7: return
        _type, = struct.unpack("!I", message[0:4])
        if _type != 8: return
        self.__time = time.time()
        new_msg = message[4:]
        self.dispatcher.send_msg_to_local(new_msg)

    def udp_writable(self):
        self.remove_evt_write(self.fileno)

    def udp_error(self):
        self.delete_handler(self.fileno)

    def send_to_router(self, _type: int, message: bytes):
        wrap_msg = struct.pack("!I", _type) + message

        self.send(wrap_msg)
        self.add_evt_write(self.fileno)

    def send_notify(self):
        dev_name = self.dispatcher.myname()
        s = "IXCSYS\r\n\r\n" + dev_name
        self.send_to_router(0, s.encode())

    def udp_timeout(self):
        now = time.time()
        if now - self.__time > 60:
            self.dispatcher.tell_fwd_disconnect()
            self.delete_handler(self.fileno)
            return

        self.send_notify()
        self.set_timeout(self.fileno, 10)

    def udp_delete(self):
        self.unregister(self.fileno)
        self.close()
