import py3dtiles.points.task.las_reader as reader
import py3dtiles.points.task.las_reader as lasReader
import py3dtiles.points.task.pnts_writer as writer
import math
import numpy as np
from octtree import oct_block
import pntsoutput as pnts
import progress as prog
import time
import globalV
import pylas
from pylas import lasreader


folder = r"C:/Users/Ajay/Desktop/output"


def place(root, pointInfo):
    root.addPoint(pointInfo)


def clearTemps():
    import os
    if (os.path.exists("output/tmp")):
        for f in os.listdir("output/tmp"):
            if (f.endswith(".tmp")):
                os.remove("output/tmp/" + f)
        for f in os.listdir("output"):
            if (f.endswith(".pnts") or f.endswith(".json")):
                os.remove("output/" + f)


def generateTileset(root):
    import json
    data = {}
    data['asset'] = {}
    data['asset']['version'] = "1.0"

    data['geometricError'] = root.computeApproximateGeometricError()*0.1

    data['root'] = root.toJson()

    with open('output/tileset.json', 'w') as outfile:
        json.dump(data, outfile)


def compute_spacing(aabb):
    return float(np.linalg.norm(aabb[1] - aabb[0]) / 125)


def moveTilesAndTileset(to):
    import os
    import shutil
    for f in os.listdir("output/"):
        if (f.endswith(".json") or f.endswith(".pnts")):
            # os.rename("output/" + f, r"C:/Users/Ajay/Desktop/Job/3D-TileSet-Viewer/public/test/" + f)
            # shutil.move("output/" + f, r"C:/Users/Ajay/Desktop/Job/3D-TileSet-Viewer/public/test/" + f)
            os.replace(
                "output/" + f, r"C:/Users/Ajay/Desktop/py3dtiles/3D-TileSet-Viewer/public/test/" + f)


def exportToXYZ(points):
    import os
    with open("output/root.xyz", "w") as writer:
        for pnt in points:
            x, y, z = pnt
            writer.write(str(x) + " " +
                         str(y) + " " + str(z) + "\n")


def eightbitify(colour):
    notzero = np.where(colour > 0)
    colour[notzero] = (colour[notzero]/255) - 1
    return colour


def loadFile(reader: lasreader.LasReader):

    clearTemps()

    data = reader.read()

    v = data.header

    minBounds = [v.x_min, v.y_min, v.z_min]
    maxBounds = [v.x_max, v.y_max, v.z_max]

    length = len(data.points)

    points = zip(data.x, data.y, data.z,
                 eightbitify(data.points['red']), eightbitify(data.points['green']), eightbitify(data.points['blue']))

    print("Bounds : " + str(minBounds) +
          " - > " + str(maxBounds))

    count = 0

    root_aabb = np.array([minBounds, maxBounds]) - np.array(minBounds)

    rtc = maxBounds

    base_spacing = compute_spacing(root_aabb)

    root_oct = oct_block(
        None,
        {
            # [root_aabb[0][0], root_aabb[0][1], minBounds[2]],
            'min': np.array(minBounds),
            # 'min': np.array(minBounds),
            # [root_aabb[1][0], root_aabb[1][1], maxBounds[2]],
            'max': np.array(maxBounds),
            # 'max': np.array(maxBounds)
        },
        [],
        [],
        level=0,
        id="root",

    )

    for pnt in points:
        x, y, z, r, g, b = pnt
        # x = x - np.array(minBounds)[0]
        # y = y - np.array(minBounds)[1]

        #z = (z + offset_scale[0][2]) * offset_scale[1][2]
        p = {
            'x': x,
            'y': y,
            'z': z,
            'r': r,
            'g': g,
            'b': b,
        }

        count += 1
        place(root_oct, p)

        if (count % length//10 == 0):
            prog.printProgressBar(count, length, 'Processing Octree')

    print(f"LEN: {count}")
    root_oct.outputToPnts()
    generateTileset(root_oct)
    moveTilesAndTileset("")


# TEST WRITER
if __name__ == '__main__':
    import sys
    # print("Loading File : " + sys.argv[1])
    with pylas.open(sys.argv[1], "r") as f:
        loadFile(f)
