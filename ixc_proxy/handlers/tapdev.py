#!/usr/bin/env python3

import os
import struct

import pywind.evtframework.handlers.handler as handler
import ixc_proxy.lib.pytap as pytap


class tap_handler(handler.handler):
    __block_size = None
    __write_queue = None

    def init_func(self, creator_fd, *args, **kwargs):
        self.__block_size = 16 * 1024
        self.__write_queue = []
        fd = pytap.tap_open(self.dispatcher.tap_devname())

        if fd < 0: return -1

        self.set_fileno(fd)
        self.register(self.fileno)
        self.add_evt_read(self.fileno)

        return self.fileno

    def evt_read(self):
        for i in range(32):
            try:
                ether_data = os.read(self.fileno, self.__block_size)
            except BlockingIOError:
                break
            self.dispatcher.send_msg_to_router(ether_data)
        ''''''

    def evt_write(self):
        while 1:
            try:
                ether_data = self.__write_queue.pop(0)
            except IndexError:
                self.remove_evt_write(self.fileno)
                break
            try:
                os.write(self.fileno, ether_data)
            except BlockingIOError:
                self.__write_queue.insert(0, ether_data)
                break
            ''''''
        ''''''

    def send_msg(self, message: bytes):
        self.__write_queue.append(message)
        self.add_evt_write(self.fileno)

    def delete(self):
        self.unregister(self.fileno)
        pytap.tap_close(self.fileno)
