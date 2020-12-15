from liblas import file
import os

os.add_dll_directory(r'C:/OSGeo4W64/bin')


f = file.File(sys.argv[1], mode='r')

for p in f:
    print('X,Y,Z: ', p.x, p.y, p.z)
