class oct_block:
    def __init__(self, parent, childrenBlocks, childrenPoints, bounds):
        self.parent = parent
        self.childrenBlocks = childrenBlocks
        self.childrenPoints = childrenPoints
        self.bounds = bounds

    def split(self):
        print(self)

    # Should Split Logic or Should place in Child or nada
    def getChildren(self, childrenPoints):
        print(self)

    def placeInChild(self, point):
        print(point)

    def isChildrenHolder(self):
        return (childrenBlocks and len(self.childrenBlocks) > 0)
