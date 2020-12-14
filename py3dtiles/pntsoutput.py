import numpy as np
import pickle as pickle
import struct
import py3dtiles.points.task.pnts_writer as writer
from struct import *


def generateFeatureTable():
    print("TE")


def outputToFile(name, pointArray, folder):
    writer.points_to_pnts(name, pointArray, folder, False)
    # import ctypes

    # magic = b"pnts"
    # version = (1)

    # packed = bytes(
    #     [magic,
    #      version]
    # )

    # magicPack = struct.pack(magic)
    # versionPack = struct.pack(version)

    # import os

    # if (not os.path.exists("output/{}.pnts".format(name))):
    #     with open("output/{}.pnts".format(name), "ab+") as f:
    #         f.write(packed)
    #         # f.write(versionPack)

    # with open("output/{}.pnts".format(name), "rb") as f:
    #     print(str(struct.unpack('=4s', f.read(4))[0]))
    #     print(str(struct.unpack('=i', f.read(4))[0]))
