# This will serve as a general oct-tree algorithm decoupled from Point Cloud Logic
# Any flushing and caching of files for oct-tree can be done externally
# Provides callbacks

import numpy as np
import mmap
import linecache
import os


blocks = 0


splitSize = 500
globalDepth = 0


class node:

    def __init__(self, bounds, depth=0, children=[], points=[]):
        global blocks

        self.block = blocks  # ID Assignment
        self.bounds = bounds
        self.children = children
        self.points = points
        self.density = 0
        self.pointCount = len(points)
        self.id = str(self.block)
        self.path = "output/tmp/" + self.id + ".tmp"
        self.writer = open(self.path, mode="a")
        self.depth = depth
        blocks += 1

    def cachePoints(self):
        lines = []
        for child in self.points:
            lines.append(str(child['x']) + "," + str(child['y']) + "," + str(child['z']) + "\n")
        self.writer.writelines(lines)

        self.points.clear()
        self.points = []

    def append(self, point):
        global splitSize
        self.pointCount += 1
        # self.points.append(point)

        # if (len(self.points) >= (2000)):
        #    self.cachePoints()
        child = point
        self.writer.write(str(child['x']) + "," + str(child['y']) + "," + str(child['z']) + "\n")

    def convertStringToPoint(self, strV=""):
        # This should be stored as binary (string operations are slow)
        coords = strV.replace('\n', '').split(',')

        return {
            'x': float(coords[0]),
            'y': float(coords[1]),
            'z': float(coords[2])
        }

    def getPointIterator(self):
        if (os.path.exists(self.path)):
            return linecache.getlines(self.path)
        else:
            print("COULDNF")

            return []

    def clear(self):

        # FORCE CACHE
        # self.cachePoints()

        # self.points.clear()
        self.pointCount = 0
        #self.points = []
        # self.writer.close()

    def split(self):
        global globalDepth

        half_x = (self.bounds['max'][0] - self.bounds['min'][0]) / 2
        half_y = (self.bounds['max'][1] - self.bounds['min'][1]) / 2
        half_z = (self.bounds['max'][2] - self.bounds['min'][2]) / 2
        #print("SPLIT {}".format(self.id))
        for x in range(0, 2):
            for y in range(0, 2):
                for z in range(0, 2):

                    newBounds = {
                        'min': [self.bounds['min'][0] + half_x * x, self.bounds['min'][1] + half_y * y, self.bounds['min'][2] + half_z * z],
                        'max': [self.bounds['min'][0] + half_x * x + half_x, self.bounds['min'][1] + half_y * y + half_y, self.bounds['min'][2] + half_z * z + half_z]
                    }
                    child_oct = node(newBounds, self.depth + 1, [], [])
                    self.children.append(child_oct)

        if (self.depth + 1 > globalDepth):
            globalDepth = self.depth + 1

        # for p in self.points:
        #    self.place(p)

        for p in self.getPointIterator():
            pnt = self.convertStringToPoint(p)
            self.place(pnt)

        self.clear()

    def place(self, point):
        for block in self.children:
            if (block.pointIsInBounds(point)):
                block.addPoint(point)
                foundHome = True
                return
        assert("Point isn't being placed")

    def deepPointCount(self):
        count = self.points

    def addPoint(self, point):
        global globalDepth
        global splitSize
        self.density += 1

        # if (self.depth < globalDepth):
        #     if (len(self.points) > 0):
        #         self.cachePoints()

        if (self.pointCount >= splitSize or len(self.children) > 0):
            if (len(self.children) == 0):
                self.split()
            else:
                self.place(point)
        else:
            self.append(point)

    def pointIsInBounds(self, point):
        return (
            (point['x'] >= self.bounds['min'][0] and point['x'] <= self.bounds['max'][0])
            and (point['y'] >= self.bounds['min'][1] and point['y'] <= self.bounds['max'][1])
            and (point['z'] >= self.bounds['min'][2] and point['z'] <= self.bounds['max'][2])
        )

    def outputToPnts(self):

        import py3dtiles.points.task.pnts_writer as writer
        if (len(self.children) == 0):

            totalPoints = []

            for pnt in self.points:
                p = pnt
                if (p['x'] and p['y'] and p['z']):
                    totalPoints.append(p['x'])
                    totalPoints.append(p['y'])
                    totalPoints.append(p['z'])

            for pnt in self.getPointIterator():

                p = self.convertStringToPoint(pnt)
                if (p['x'] and p['y'] and p['z']):
                    totalPoints.append(p['x'])
                    totalPoints.append(p['y'])
                    totalPoints.append(p['z'])

            writer.points_to_pnts('tile-' + self.id, np.array(totalPoints, dtype=np.float32).view(np.uint8), "output", False)

        for b in self.children:
            b.outputToPnts()

    def computeApproximateGeometricError(self, pointScale=0.001):
        x = (self.bounds['max'][0] - self.bounds['min'][0])
        y = (self.bounds['max'][1] - self.bounds['min'][1])
        z = (self.bounds['max'][2] - self.bounds['min'][2])
        return (x * y * z) / max((self.density * pointScale), 1)

    def boundingBox(self):
        xL = (self.bounds['max'][0] - self.bounds['min'][0]) / 2
        yL = (self.bounds['max'][1] - self.bounds['min'][1]) / 2
        zL = (self.bounds['max'][2] - self.bounds['min'][2]) / 2

        x = self.bounds['min'][0] + xL
        y = self.bounds['min'][1] + yL
        z = self.bounds['min'][2] + zL

        return [x, y, z, xL, yL, zL]

    def toJson(self):
        import os
        if (os.path.exists('output/' + 'tile-' + self.id + '.pnts') or len(self.children) > 0):
            data = {}
            data['refine'] = "REFINE" if (id == "root") else "ADD"
            arr = self.boundingBox()
            data['boundingVolume'] = {}
            data['boundingVolume']['box'] = [arr[0], arr[1], arr[2], arr[3], 0, 0, 0, arr[4], 0, 0, 0, arr[5]]

            data['geometricError'] = self.computeApproximateGeometricError()
            import time

            if (len(self.children) == 0):
                data['content'] = {}
                data['content']['uri'] = 'tile-' + self.id + '.pnts'

            else:
                arr = []
                for c in self.children:
                    jsonF = c.toJson()
                    if (jsonF != None):
                        arr.append(jsonF)
                if (len(arr) > 0):
                    data['children'] = arr

            return data
        return None
