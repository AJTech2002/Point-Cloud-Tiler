import os


globalTileCount = 0


class node:

    def __init__(self, bounds, id, spacing, limit, store):
        global globalTileCount
        id = globalTileCount
        globalTileCount += 1
        self.id = id
        self.density = 0
        self.strId = str(id)

        store.registerNode(self.strId)

        self.bounds = bounds
        self.spacing = spacing
        self.hasSubdivided = False
        self.children = []
        self.limit = limit
        self.store = store

    def dist(self, a, b):
        import math
        return math.sqrt((math.pow(a['x'] - b['x'], 2)) + (math.pow(a['y'] - b['y'], 2)) + (math.pow(a['z'] - b['z'], 2)))

    def computeApproximateGeometricError(self, pointScale=0.001):
        x = (self.bounds['max'][0] - self.bounds['min'][0])
        y = (self.bounds['max'][1] - self.bounds['min'][1])
        z = (self.bounds['max'][2] - self.bounds['min'][2])

        return (x * y * z) / max((self.density * pointScale), 1)

    def split(self):

        global globalTileCount

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

                    child_oct = node(newBounds, globalTileCount, self.spacing, self.limit, self.store)

                    self.children.append(child_oct)

        self.hasSubdivided = True

        # MIGRATION
        for p in self.store.returnPointIterator(self.strId):
            self.placeInChildren(p)

        self.store.deleteNodeInfo(self.strId)

    def place(self, point):
        if (self.hasSubdivided):
            print("ADDED AFTER TF")
        self.store.addPoint(self.strId, point)

    def placeInChildren(self, point):
        for b in self.children:
            if (b.pointIsInBounds(point)):
                b.addPoint(point)
                return

        print("ERROR")

    def pointIsInBounds(self, point):
        if (point):
            try:
                (x, y, z, r, g, b) = point
                return (
                    (float(x) >= float(self.bounds['min'][0] - self.spacing)
                     and float(x) <= float(self.bounds['max'][0] + self.spacing))
                    and (float(y) >= float(self.bounds['min'][1] - self.spacing) and float(y) <= float(self.bounds['max'][1] + self.spacing))
                    and (float(z) >= float(self.bounds['min'][2] - self.spacing) and float(z) <= float(self.bounds['max'][2] + self.spacing))
                )
            except:
                return False
        return False

    def addPoint(self, point):

        self.density += 1

        if self.hasSubdivided:
            self.placeInChildren(point)
            return
        elif (self.store.returnPointCount(self.strId) >= self.limit):
            self.place(point)
            self.split()
            return
        else:
            self.place(point)
            return
