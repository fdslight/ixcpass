import os
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", 0))

for i in range(30):
    data=os.urandom(32)
    s.sendto(data, ("192.168.1.1", 53))
    time.sleep(10)

s.close()
