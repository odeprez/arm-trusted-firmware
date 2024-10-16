#!/usr/bin/python3

import struct
import os

def Main():
    print("run forrest run")
    with open("hob.bin", "wb") as hob:
        hob_struct = struct.pack("hhl", 1, 2, 3)
        hob.write(hob_struct)
        print(hob_struct)

Main()
