import py3dtiles.points.task.las_reader as reader
import numpy as np


def compute_spacing(aabb):
    return float(np.linalg.norm(aabb[1] - aabb[0]) / 125)


def exportToXYZ(points):
    import os
    with open("output/root.xyz", "w") as writer:
        for pnt in points:
            p = pnt
            if (p['x'] and p['y'] and p['z']):
                writer.write(str(p['x']) + " " + str(p['y']) + " " + str(p['z']) + "\n")


data = reader.init(["C:/Users/Ajay/Desktop/ripple.las"], None, None, None, fraction=100)

totalCoords = []

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

    for p in coords:
        point = {
            'x': p[0],
            'y': p[1],
            'z': p[2]
        }
        totalCoords.append(point)

exportToXYZ(totalCoords)
