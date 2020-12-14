import py3dtiles.points.task.las_reader as reader
import py3dtiles.points.task.las_reader as lasReader
import py3dtiles.points.task.pnts_writer as writer
import math
from laspy.file import File
import numpy as np
from octtree import oct_block
#from octtreev2 import node
import pntsoutput as pnts
import progress as prog
import time
import globalV
from guppy import hpy
# SINGLE FILE SUPPORT ONLY


folder = r"C:/Users/Ajay/Desktop/output"
fraction = 1
stop_threads = False


def place(root, pointInfo):
    root.addPoint(pointInfo)

# !! USE EXECUTOR.MAP


def applyTransform(point, scale, offset):
    x, y, z = point
    x = x * scale[0] + offset[0]
    y = y * scale[1] + offset[1]
    z = z * scale[2] + offset[2]

    print(x, y, z)
    # return zip(x, y, z)


def initialisePoints(f):
    import os

    if (os.path.exists("output/tmp/transformed") == False):
        os.mkdir("output/tmp/transformed")

    file_points = f.get_points()['point']
    # file_points = all_file_points[0:(len(all_file_points)) // fraction]

    if (fraction > 1):
        print("Fraction less than 100 (Partial Export)")

    count = len(file_points['X'] // fraction)
    _1M = min(count, 1000000)
    steps = math.ceil(count / _1M)
    portions = [(i * _1M, min(count, (i + 1) * _1M)) for i in range(steps)]

    X = file_points['X']
    Y = file_points['Y']
    Z = file_points['Z']
    lenP = len(file_points)

    start = time.time()

    for i, portion in enumerate(portions):
        if (os.path.exists("output/tmp/transformed/" + str(len(f.filename)) + "_port_" + str(i) + ".transformed") == False):
            point_count = portion[1] - portion[0]
            step = min(point_count, max((point_count) // 10, 100000))
            indices = [i for i in range(math.ceil((point_count) / step))]
            write = open("output/tmp/transformed/" + str(len(f.filename)) + "_port_" + str(i) + ".transformed", "wb")

            for index in indices:
                start_offset = portion[0] + index * step
                num = min(step, portion[1] - start_offset)

                # NEED A SCALED OFFSET TOO
                x = X[start_offset:start_offset + num] * f.header.scale[0] + f.header.offset[0]
                y = Y[start_offset:start_offset + num] * f.header.scale[1] + f.header.offset[1]
                z = Z[start_offset:start_offset + num] * f.header.scale[2] + f.header.offset[2]

                # saved.append([x, y, z])
                #!! NOT CONFIRMED IF THIS REALLY OUTPUTS ALL THE DATA ::
                write.write(np.vstack((x, y, z)).transpose().tobytes())

            write.close()
            prog.printProgressBar(i, len(portions), 'Transforming Coordinates', '%', length=100)
            end = time.time()
            print("Time to Transform " + str(end - start))
        else:
            print("Transformed Coordinates are Cached, no transformation required for : " + str(len(f.filename)) + "_port_" + str(i) + ".transformed" + " (100%)")
            os.system("cls")

    return (portions, file_points)


done = 0


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

    data['geometricError'] = root.computeApproximateGeometricError()

    data['root'] = root.toJson()

    with open('output/tileset.json', 'w') as outfile:
        json.dump(data, outfile)


def moveTilesAndTileset(to):
    import os
    import shutil
    for f in os.listdir("output/"):
        if (f.endswith(".json") or f.endswith(".pnts")):
            # os.rename("output/" + f, r"C:/Users/Ajay/Desktop/Job/3D-TileSet-Viewer/public/test/" + f)
            # shutil.move("output/" + f, r"C:/Users/Ajay/Desktop/Job/3D-TileSet-Viewer/public/test/" + f)
            os.replace("output/" + f, r"C:/Users/Ajay/Desktop/Job/3D-TileSet-Viewer/public/test/" + f)


def exportToXYZ(points):
    import os
    with open("output/root.xyz", "w") as writer:
        for pnt in points:
            p = pnt
            if (p['x'] and p['y'] and p['z']):
                writer.write(str(p['x']) + " " + str(p['y']) + " " + str(p['z']) + "\n")


def compute_spacing(aabb):
    return float(np.linalg.norm(aabb[1] - aabb[0]) / 125)


def initialisePointsFixed(filename):
    data = reader.init([filename], None, None, None, fraction=100)
    totalCoords = []

    print("TOTAL : {}".format(data['point_count']))
    print()
    rotation_matrix = None

    for portionData in data['portions']:
        (filename, portion) = portionData

        root_aabb = data['aabb'] - data['avg_min']

        base_spacing = compute_spacing(root_aabb)
        if base_spacing > 10:
            root_scale = np.array([0.01, 0.01, 0.01])
        elif base_spacing > 1:
            root_scale = np.array([0.1, 0.1, 0.1])
        else:
            root_scale = np.array([1, 1, 1])

        root_aabb = root_aabb * root_scale
        root_spacing = compute_spacing(root_aabb)

        offset_scale = (-data['avg_min'], root_scale, rotation_matrix[:3, :3].T if rotation_matrix is not None else None, data['color_scale'])

        print(offset_scale)

        coords, colors = reader.runSingle(filename, portion, offset_scale)

        for (i, p) in enumerate(coords):

            point = {
                'x': p[0],
                'y': p[1],
                'z': p[2],
                'r': colors[i][0],
                'g': colors[i][1],
                'b': colors[i][2],
            }
            totalCoords.append(point)
            prog.printProgressBar(i, len(coords), 'Loading Data')

        return (totalCoords, root_aabb, root_spacing)


def oldSolve(root_oct):
    (portions, file_points) = initialisePoints(f)

    start_time = time.time()

    estimated_time = 0

    for (i, portion) in enumerate(portions):

        if (i == 6):
            h = hpy()
            print(h.heap())

        start_time = time.time()
        dt = np.dtype([('x', float), ('y', float), ('z', float)])
        read = open("output/tmp/transformed/" + str(len(f.filename)) + "_port_" + str(i) + ".transformed", "rb")
        arrayRead = np.frombuffer(read.read(), dtype=dt)

        for c, coord in enumerate(arrayRead):

            place(root_oct, {
                'x': coord[0],
                'y': coord[1],
                'z': coord[2],

            })

            if (c % 10000 == 0):
                prog.printProgressBar(c, len(arrayRead), 'Generating Portion ' + str(i) + "/" + str(len(portions)), 'Estimated : ' + str(estimated_time), length=50)

        print()
        end_time = time.time()
        estimated_time = (end_time - start_time) * (len(portions) - i)


def loadFile(file):

    startFullTime = time.time()

    clearTemps()

    (allPoints, rootBounds, spacing) = initialisePointsFixed(file)

    # root_oct = node(
    #     {
    #         'min': rootBounds[0],
    #         'max': rootBounds[1]
    #     },
    #     0,
    #     [],
    #     []
    # )

    time.sleep(10)
    root_oct = oct_block(
        None,
        {
            'min': rootBounds[0],
            'max': rootBounds[1]
        },
        [],
        [],
        level=0,
        id="root"
    )

    #print("Bounds : " + str(f.header.get_min()) + " - > " + str(f.header.get_max()))

    count = 0

    for p in allPoints:
        count += 1
        place(root_oct, p)
        prog.printProgressBar(count, len(allPoints), 'Processing Octree')

    print()
    print("COMPLETED {}".format(count))
    print()

    import os
    import linecache

    root_oct.outputToPnts()

    generateTileset(root_oct)

    moveTilesAndTileset("")


# TEST WRITER
if __name__ == '__main__':
    import sys
    print("Loading File : " + sys.argv[1])
    loadFile(sys.argv[1])
# r"C:/Users/Ajay/Desktop/py3dTiles Custom/py3dtiles_src/tests/ripple.las"
# r"C:/Users/Ajay/Desktop/towerComplete.las"


#
#  dt = np.dtype([('x', float), ('y', float), ('z', float)])
#     read = open("output/tmp/transformed/" + str(len(f.filename)) + "_port_" + str(0) + ".transformed", "rb")
#     arrayRead = np.frombuffer(read.read(), dtype=dt)

#     import pntsoutput

#     X = arrayRead[0:500]['x']
#     Y = arrayRead[0:500]['y']
#     Z = arrayRead[0:500]['z']

#     points = []

#     for i in range(0, len(X)):
#         points.append(X[i])
#         points.append(Y[i])
#         points.append(Z[i])

#     pntsoutput.outputToFile("test", points, "output")

#     print("COMPLTED TEST")
#     time.sleep(5)
