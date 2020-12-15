import pylas
import sys
from pylas import lasreader
from nodestore import nodestore
from node import node
import progress as prog


def exportToXYZ(points):
    import os
    with open("output/root.xyz", "w") as writer:
        for pnt in points:
            x, y, z = pnt
            writer.write(str(x) + " "
                         + str(y) + " " + str(z) + "\n")


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


totalCount = 0


def exportToPnts(root: node, store: nodestore):
    global totalCount
    import py3dtiles.points.task.pnts_writer as writer
    import numpy as np

    if (root.hasSubdivided == False):
        totalPoints = []
        totalColors = []

        for p in store.returnPointIterator(root.strId):

            try:
                totalCount += 1
                x, y, z, r, g, b = p
                totalPoints.append(x)
                totalPoints.append(y)
                totalPoints.append(z)

                totalColors.append(r)
                totalColors.append(g)
                totalColors.append(b)
            except:
                print(list(p))

        arr = np.concatenate(
            (np.array(totalPoints, dtype=np.float32).view(np.uint8).ravel(), np.array(totalColors, dtype=np.uint8).ravel()))
        writer.points_to_pnts(
            'tile-{}'.format(root.strId), arr, "output", True)
    else:
        for b in root.children:
            exportToPnts(b, store)


def rootJson(root: node, store: nodestore):

    data = {}
    data['refine'] = "REFINE" if (root.id == 0) else "ADD"
    arr = boundingBox(root.bounds)
    data['boundingVolume'] = {}
    data['boundingVolume']['box'] = [arr[0], arr[1],
                                     arr[2], arr[3], 0, 0, 0, arr[4], 0, 0, 0, arr[5]]

    data['geometricError'] = root.computeApproximateGeometricError()

    if root.hasSubdivided == False:
        data['content'] = {}
        data['content']['uri'] = 'tile-' + root.strId + '.pnts'

    else:
        arr = []
        for c in root.children:
            jsonF = rootJson(c, store)
            if (jsonF != None):
                arr.append(jsonF)
        if (len(arr) > 0):
            data['children'] = arr

    return data


def clearTemps():
    import os
    if (os.path.exists("output/tmp")):
        for f in os.listdir("output/tmp"):
            if (f.endswith(".tmp")):
                os.remove("output/tmp/" + f)
        for f in os.listdir("output"):
            if (f.endswith(".pnts") or f.endswith(".json")):
                os.remove("output/" + f)


def outputTileset(bounds, pointCount, root: node, store: nodestore):
    import json
    data = {}
    data['asset'] = {}
    data['asset']['version'] = "1.0"

    data['geometricError'] = root.computeApproximateGeometricError()

    data['root'] = rootJson(root, store)

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
    colour[notzero] = (colour[notzero] / 255) - 1
    return colour


def readPoints(reader: lasreader.LasReader):
    data = reader.read()

    v = data.header

    minBounds = [v.x_min, v.y_min, v.z_min]
    maxBounds = [v.x_max, v.y_max, v.z_max]

    points = zip(data.x, data.y, data.z,
                 eightbitify(data.points['red']), eightbitify(data.points['green']), eightbitify(data.points['blue']))

    store = nodestore(int(sys.argv[3]), None)
    root = node({
        'min': minBounds,
        'max': maxBounds
    }, 0, 0.5, int(sys.argv[2]), store)

    for (i, p) in enumerate(points):
        root.addPoint(p)
        prog.printProgressBar(i, len(data.points), 'Progress')

    exportToPnts(root, store)
    outputTileset(boundingBox({
        'min': minBounds,
        'max': maxBounds
    }), len(data.points), root, store)

    moveTilesAndTileset("")

    global totalCount
    print()
    print("TOTAL : " + str(totalCount) + " vs DENSITY : " + str(root.density))


print("WARNING (RECURSION LIMIT) : " + str(sys.getrecursionlimit()))

clearTemps()
with pylas.open(sys.argv[1], "r") as f:
    readPoints(f)


##TODO : 
# 1. Recursion isn't efficient in Python (change to iterative using contigious array) [Node Catalog]
# 2. Therad the file stream