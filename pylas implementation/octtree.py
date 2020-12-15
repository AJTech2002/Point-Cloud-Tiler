# TILE SET REF : https://docs.opengeospatial.org/cs/18-053r2/18-053r2.html#56
# B3DM & PNTS REF : https://docs.opengeospatial.org/cs/18-053r2/18-053r2.html#199
from laspy.file import File
import numpy as np
import pntsoutput as pnts
import sys
import os
import linecache
from multiprocessing import Pool, Queue, Process, Manager
import globalV
from functools import partial
globalLimit = 50000
globalTileCount = 0
globalChildrenCount = 0
gC = 0
errored = []


class oct_block:
    def __init__(self, parent, bounds, childrenBlocks=[], childrenPoints=[], level=0, id="root", rtc=None):
        self.parent = parent
        self.childrenBlocks = childrenBlocks
        self.childrenPoints = childrenPoints
        self.count = 0
        self.density = 0
        self.bounds = bounds
        self.level = level
        self.id = id
        self.path = "output/tmp/" + self.id + ".tmp"
        self.rtc = rtc

    def createTemp(self):
        self.childrenPoints = []
        # self.fWrite.close()

    def appendPoint(self, child, writer):
        self.count += 1

        self.childrenPoints.append(child)

        #globalLimit // 10
        # if (len(self.childrenPoints) > 0 or self.count >= globalLimit - 2):
        #     lines = []
        #     for child in self.childrenPoints:
        #         lines.append(str(child['x']) + "," + str(child['y']) + "," + str(child['z']) + "," + str(
        #             child['r']) + "," + str(child['g']) + "," + str(child['b']) + "\n")
        #     writer.writelines(lines)

        #     self.childrenPoints = []
        #writer.write(str(child['x']) + "," + str(child['y']) + "," + str(child['z']) + "\n")

    def getCurrentPointCount(self):
        # return len(linecache.getlines(self.path))
        return self.count

    def getRealPointCount(self):
        return len(self.childrenPoints)
        # if (os.path.exists(self.path)):
        #     return len(linecache.getlines(self.path)) - 1
        # else:
        #     return 0

    def cleanup(self, deep=False):
        if (self.getRealPointCount() < 1 or deep):
            if (os.path.exists(self.path)):
                os.remove(self.path)

        for block in self.childrenBlocks:
            block.cleanup(deep)

    # def getPointIterator(self):
    #    return linecache.getlines(self.path)

    def convertStringToPoint(self, strV=""):
        # print(strV)
        coords = strV.replace('\n', '').split(',')

        return {
            'x': float(coords[0]),
            'y': float(coords[1]),
            'z': float(coords[2]),
            'r': float(coords[3]),
            'g': float(coords[4]),
            'b': float(coords[5])
        }

    def split(self, writer):

        global globalTileCount

        #print("COUNT : " + str(self.count) + " FINAL : " + str(len(self.getPointIterator())))

        half_x = (self.bounds['max'][0] - self.bounds['min'][0]) / 2
        half_y = (self.bounds['max'][1] - self.bounds['min'][1]) / 2
        half_z = (self.bounds['max'][2] - self.bounds['min'][2]) / 2

        count = -1

        for x in range(0, 2):
            for y in range(0, 2):
                for z in range(0, 2):
                    count = count + 1
                    newBounds = {
                        'min': [self.bounds['min'][0] + half_x * x, self.bounds['min'][1] + half_y * y, self.bounds['min'][2] + half_z * z],
                        'max': [self.bounds['min'][0] + half_x * x + half_x, self.bounds['min'][1] + half_y * y + half_y, self.bounds['min'][2] + half_z * z + half_z]
                    }

                    child_oct = oct_block(
                        # No parent
                        self,
                        # Bounds
                        newBounds,
                        # No existing points
                        [],
                        # No existing block children
                        [],
                        self.level + 1,
                        "root" + str(globalTileCount)
                    )

                    globalTileCount += 1
                    child_oct.createTemp()

                    self.childrenBlocks.append(child_oct)

        #self.count -= len(self.getPointIterator())

        #print("C " + str(self.count) + " v " + str(len(self.getPointIterator())))

        for p in self.childrenPoints:
            #point = self.convertStringToPoint(p)
            self.placeInChild(p)

        # Ensure clear
        self.childrenPoints = []

    def pointIsInBounds(self, point):
        return (
            (float(point['x']) >= float(self.bounds['min'][0])
             and float(point['x']) <= float(self.bounds['max'][0]))
            and (float(point['y']) >= float(self.bounds['min'][1]) and float(point['y']) <= float(self.bounds['max'][1]))
            and (float(point['z']) >= float(self.bounds['min'][2]) and float(point['z']) <= float(self.bounds['max'][2]))
        )

    def dist(self, a, b):
        import math
        return math.sqrt((math.pow(a['x'] - b['x'], 2)) + (math.pow(a['y'] - b['y'], 2)) + (math.pow(a['z'] - b['z'], 2)))

    def computeAverageGeometricError(self, detail):

        avgError = 0
        count = 0
        for (i, p) in enumerate(self.childrenPoints):
            if (i > detail):
                break
            count += 1
            point = p
            if (i == 0):
                continue
            lastPoint = linecache.getlines(self.path)[i - 1]
            avgError += self.dist(point, lastPoint)

        return (avgError / count)

    def computeApproximateGeometricError(self, pointScale=0.001):
        x = (self.bounds['max'][0] - self.bounds['min'][0])
        y = (self.bounds['max'][1] - self.bounds['min'][1])
        z = (self.bounds['max'][2] - self.bounds['min'][2])

        return (x * y * z) / max((self.density * pointScale), 1)

    # Should Split Logic or Should place in Child or Simply add to the block

    def addPoint(self, point):
        self.density += 1
        didSplit = False
        # with open(self.path, "a") as writer:
        if (self.getCurrentPointCount() > globalLimit or len(self.childrenBlocks) != 0):
            if (len(self.childrenBlocks) == 0):
                self.split(None)
                didSplit = True
            else:
                self.placeInChild(point)
                return
        else:
            self.appendPoint(point, None)
            return

       # if (didSplit):
        #    os.remove(self.path)

    # Recursively place in child

    def search(self, point, blocks):

        if (len(self.childrenBlocks) == 0):
            return self

        for block in blocks:
            if (block.pointIsInBounds(point)):
                # block.addPoint(point, q)
                return block.search(point, block.childrenBlocks)

        return None

    def placeInChild(self, point):
        global gC
        foundHome = False
        for block in self.childrenBlocks:
            if (block.pointIsInBounds(point)):
                block.addPoint(point)
                foundHome = True
                break

        if (foundHome == False):
            # print("Errors in bounds {} at : {}".format(len(errored), (str(
            #    point['x']) + "," + str(point['y']) + "," + str(point['z']))))
            gC += 1
            errored.append(point)

    def isChildrenHolder(self):
        return (childrenBlocks and len(self.childrenBlocks) > 0)

    def exportToXYZ(self, points):
        import os
        with open("output/{}.xyz".format(self.id), "w") as writer:
            for pnt in points:
                x = pnt['x']
                y = pnt['y']
                z = pnt['z']
                writer.write(str(x) + " " +
                             str(y) + " " + str(z) + " " + str(pnt['r']) + " " + str(pnt['g']) + " " + str(pnt['b']) + "\n")

    def outputToPnts(self):
        import py3dtiles.points.task.pnts_writer as writer

        if (self.id == "root"):
            totalPoints = []
            totalColors = []
            X = []
            Y = []
            Z = []
            for pnt in errored:
                p = pnt
                if (p['x'] and p['y'] and p['z']):
                    # coord = np.vstack((p['x'],p['y'],p['z'])).transpose()
                    totalPoints.append(p['x'])
                    totalPoints.append(p['y'])
                    totalPoints.append(p['z'])
                    totalColors.append(p['r'])
                    totalColors.append(p['g'])
                    totalColors.append(p['b'])

            arr = np.concatenate(
                (np.array(totalPoints, dtype=np.float32).view(np.uint8).ravel(), np.array(totalColors, dtype=np.uint8).ravel()))
            writer.points_to_pnts(
                'errored', arr, "output", True)

        if (len(self.childrenBlocks) == 0):
            totalPoints = []
            totalColors = []
            X = []
            Y = []
            Z = []
            for pnt in self.childrenPoints:
                p = pnt
                if (p['x'] and p['y'] and p['z']):
                    # coord = np.vstack((p['x'],p['y'],p['z'])).transpose()

                    totalPoints.append(p['x'])
                    totalPoints.append(p['y'])
                    totalPoints.append(p['z'])
                    totalColors.append(p['r'])
                    totalColors.append(p['g'])
                    totalColors.append(p['b'])

            # np.array(totalPoints)
            # np.array(totalPoints).astype(np.float32)

            arr = np.concatenate((np.array(totalPoints, dtype=np.float32).view(
                np.uint8), np.array(totalColors, dtype=np.uint8)))

            writer.points_to_pnts('tile-' + self.id, arr,
                                  "output", True, self.rtc)
            self.exportToXYZ(self.childrenPoints)
            # pnts.outputToFile('tile-' + self.id, totalPoints, "output")

        for b in self.childrenBlocks:
            b.outputToPnts()

    def deepSearchPoint(self, point, startTime):

        if (len(self.childrenBlocks) == 0):
            import time
            print("[" + str(self.level) + "]" + "Deep Search Time Elapsed : " +
                  str(time.time() - startTime) + "\n")

        for b in self.childrenBlocks:
            if (b.pointIsInBounds(point)):
                b.deepSearchPoint(point, startTime)

    def print(self):
        global globalChildrenCount

        print((" " * self.level * 2) + "Block : " +
              str(self.bounds['min']) + " : " + str(self.bounds['max']))
        for b in self.childrenBlocks:
            b.print()

        if (len(self.childrenBlocks) == 0):
            print((" " * self.level * 2) + "Children : " +
                  str(self.getRealPointCount()))
            globalChildrenCount += self.getRealPointCount()
            # for p in self.childrenPoints:

        if (self.id == "root"):
            print("FINAL CHILDREN POINT COUNT {} vs {}".format(
                str(self.totalCount()[0]), str(self.totalCount()[1])))

    def boundingBox(self):
        xL = (self.bounds['max'][0] - self.bounds['min'][0]) / 2
        yL = (self.bounds['max'][1] - self.bounds['min'][1]) / 2
        zL = (self.bounds['max'][2] - self.bounds['min'][2]) / 2

        x = self.bounds['min'][0] + xL
        y = self.bounds['min'][1] + yL
        z = self.bounds['min'][2] + zL

        return [x, y, z, xL, yL, zL]

    def totalCount(self):
        count = self.count
        lineCount = self.getRealPointCount()
        for b in self.childrenBlocks:
            count += b.totalCount()[0]
            lineCount += b.totalCount()[1]

        return (count, lineCount)

    def toJson(self):
        global gC
        if (os.path.exists('output/' + 'tile-' + self.id + '.pnts') or len(self.childrenBlocks) > 0):
            data = {}
            data['refine'] = "REFINE" if (id == "root") else "ADD"
            arr = self.boundingBox()
            data['boundingVolume'] = {}
            data['boundingVolume']['box'] = [arr[0], arr[1],
                                             arr[2], arr[3], 0, 0, 0, arr[4], 0, 0, 0, arr[5]]

            data['geometricError'] = self.computeApproximateGeometricError() * \
                0.1
            import time

            # if (len(self.childrenPoints) > 0):
            #print("ERROR POINTS REMAINING")
            #   time.sleep(0.001)

            if (self.id == "root"):
                data['content'] = {}
                data['content']['uri'] = 'errored.pnts'

            if (len(self.childrenBlocks) == 0):
                data['content'] = {}
                data['content']['uri'] = 'tile-' + self.id + '.pnts'

            else:

                arr = []
                for c in self.childrenBlocks:
                    jsonF = c.toJson()
                    if (jsonF != None):
                        arr.append(jsonF)
                if (len(arr) > 0):
                    data['children'] = arr

            return data
        return None
    # ! Important to convert points to numpy transposed format [found in las_reader]
