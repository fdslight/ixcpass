import os
import socket, time

fdst = os.popen('ip addr')
for line in fdst:
    p = line.find("end0")
    if p < 0: continue
    print(line)
fdst.close()
