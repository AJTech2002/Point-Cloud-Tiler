import sys
import os

# TODO: Doesn't include threading right now


class nodestore:
    def __init__(self, cacheSize, queue=None):
        self.queue = queue
        self.cacheSize = cacheSize
        self.nodeDict = {}

    def registerNode(self, nodeId):
        self.nodeDict[nodeId] = {
            'children': [],
            'totalPoints': 0,
            'path': 'output/tmp/{}.tmp'.format(nodeId)
        }

    def addPoint(self, nodeId, point):
        if (nodeId in self.nodeDict):
            self.nodeDict[nodeId]['children'].append(point)
            self.nodeDict[nodeId]['totalPoints'] += 1

            # The amount of points in memory has exceeded its limit, so push to write to file
            if (len(self.nodeDict[nodeId]['children']) >= self.cacheSize):
                self.convertToFileStream(nodeId)
                self.nodeDict[nodeId]['children'] = []

    def returnPointCount(self, nodeId):
        return self.nodeDict[nodeId]['totalPoints']

    def returnRealPointCount(self, nodeId):
        return len(self.nodeDict[nodeId]['children'])

    def returnPointIterator(self, nodeId):
        if (nodeId in self.nodeDict):
            totalPoints = self.nodeDict[nodeId]['children']
            if (os.path.exists(self.nodeDict[nodeId]['path'])):
                with open(self.nodeDict[nodeId]['path'], "r") as f:
                    for line in f.readlines():
                        coords = line.replace('\n', '').split(',')
                        x = float(coords[0])
                        y = float(coords[1])
                        z = float(coords[2])
                        r = float(coords[3])
                        g = float(coords[4])
                        b = float(coords[5])

                        totalPoints.append((x,y,z,r,g,b))
                        # totalPoints.append(coords)

        if (self.nodeDict[nodeId]['totalPoints'] != len(totalPoints)):
            print("Actual {} vs Given {}".format(self.nodeDict[nodeId]['totalPoints'], len(totalPoints)))
        return totalPoints

    def deleteNodeInfo(self, nodeId):
        if (nodeId in self.nodeDict):
            if (os.path.exists(self.nodeDict[nodeId]['path'])):
                os.remove(self.nodeDict[nodeId]['path'])
            self.nodeDict[nodeId]['totalPoints'] = 0
            self.nodeDict[nodeId]['children'] = []
            del self.nodeDict[nodeId]

    def convertToFileStream(self, nodeId):
        with open(self.nodeDict[nodeId]['path'], "a") as f:
            points = self.nodeDict[nodeId]['children']

            lines = []

            for (i, p) in enumerate(points):
                x, y, z, r, g, b = p
                if (i == 0):
                    pointStr = "{},{},{},{},{},{}\n".format(x, y, z, r, g, b)
                else:
                    pointStr = "{},{},{},{},{},{}\n".format(x, y, z, r, g, b)

                f.write(pointStr)
                os.fsync(f)
            return True

        return False
