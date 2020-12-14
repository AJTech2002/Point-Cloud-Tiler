import pylas
import sys
from pylas import lasreader


def exportToXYZ(points):
    import os
    with open("output/root.xyz", "w") as writer:
        for pnt in points:
            x, y, z = pnt
            writer.write(str(x) + " " +
                         str(y) + " " + str(z) + "\n")


def boundingBox(bounds):
    xL = (bounds['max'][0] - bounds['min'][0]) / 2
    yL = (bounds['max'][1] - bounds['min'][1]) / 2
    zL = (bounds['max'][2] - bounds['min'][2]) / 2

    x = bounds['min'][0] + xL
    y = bounds['min'][1] + yL
    z = bounds['min'][2] + zL

    return [x, y, z, xL, yL, zL]


def computeApproximateGeometricError(bounds, pointScale, pointCount):
    x = (bounds['max'][0] - bounds['min'][0])
    y = (bounds['max'][1] - bounds['min'][1])
    z = (bounds['max'][2] - bounds['min'][2])

    return (x * y * z) / max((pointCount * pointScale), 1)


def exportToPnts(points=[]):
    import py3dtiles.points.task.pnts_writer as writer
    import numpy as np

    totalPoints = []
    totalColors = []

    for p in points:
        x, y, z, r, g, b = p
        totalPoints.append(x)
        totalPoints.append(y)
        totalPoints.append(z)

        totalColors.append(r)
        totalColors.append(g)
        totalColors.append(b)

    arr = np.concatenate(
        (np.array(totalPoints, dtype=np.float32).view(np.uint8).ravel(), np.array(totalColors, dtype=np.uint8).ravel()))
    writer.points_to_pnts(
        'root', arr, "output", True)


def rootJson(bounds, pointCount, id="root"):
    data = {}
    data['refine'] = "REFINE" if (id == "root") else "ADD"
    arr = boundingBox(bounds)
    data['boundingVolume'] = {}
    data['boundingVolume']['box'] = [arr[0], arr[1],
                                     arr[2], arr[3], 0, 0, 0, arr[4], 0, 0, 0, arr[5]]

    data['geometricError'] = computeApproximateGeometricError(bounds, 0.001, pointCount) * \
        0.1

    

    if (id == "root"):
        data['content'] = {}
        data['content']['uri'] = 'root.pnts'

    return data


def outputTileset(bounds, pointCount):
    import json
    data = {}
    data['asset'] = {}
    data['asset']['version'] = "1.0"

    data['geometricError'] = computeApproximateGeometricError(
        bounds, 0.001, pointCount)*0.1

    data['root'] = rootJson(bounds, pointCount)

    with open('output/tileset.json', 'w') as outfile:
        json.dump(data, outfile)


def moveTilesAndTileset(to):
    import os
    import shutil
    for f in os.listdir("output/"):
        if (f.endswith(".json") or f.endswith(".pnts")):
            os.replace(
                "output/" + f, r"C:/Users/Lenovo/Desktop/3D-TileSet-Viewer/public/test/" + f)


def eightbitify(colour):
    import numpy as np
    notzero = np.where(colour > 0)
    colour[notzero] = (colour[notzero]/255) - 1
    return colour


def readPoints(reader: lasreader.LasReader):
    data = reader.read()

    v = data.header

    minBounds = [v.x_min, v.y_min, v.z_min]
    maxBounds = [v.x_max, v.y_max, v.z_max]

    points = zip(data.x, data.y, data.z,
                 eightbitify(data.points['red']), eightbitify(data.points['green']), eightbitify(data.points['blue']))

    exportToPnts(points)
    outputTileset({
        'min': minBounds,
        'max': maxBounds
    }, len(data.points))

    moveTilesAndTileset("")


with pylas.open(sys.argv[1], "r") as f:
    readPoints(f)
