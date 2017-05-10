import json
import sys
import time
import pylab
import subprocess
import numpy as np
from scipy.cluster.vq import *

import warnings

__author__ = 'Hector Azpurua'


class KmeansSegment(object):

    kmeans_color_array = [
        (0, 0, 1),
        (0, 1, 0),
        (1, 0, 0),
        (0, 1, 1),
        (1, 1, 0),
        (1, 0, 1),
        (1, 0, 1),
        (0, 0, 0),
        (0, 0.5, 0.5),
        (0.5, 1, 0.5)
    ]

    def __init__(self):
        pass

    def run_kmeans(xy, cluster_size=2):

        points_per_robot = []

        if len(xy) == 1 or (len(xy) == 2 and cluster_size == 1):
            points_per_robot.append([xy])
            return points_per_robot

        elif len(xy) == 2 and cluster_size == 2:
            points_per_robot.append([xy[0]])
            points_per_robot.append([xy[1]])
            return points_per_robot

        xy = np.asarray(xy)
        data = np.column_stack([xy])
        data = data.astype(np.float32)

        res = []
        labels = []

        # Apply Kmeans with user defined cluster size and run 90 times
        continue_loop_kmeans = True
        while continue_loop_kmeans:
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    print 'data', data, 'cluster_size', cluster_size
                    res, labels = kmeans2(data, cluster_size, 90)
                    continue_loop_kmeans = False
                except Warning:
                    print "Warning.."

        colors = ([KmeansSegment.kmeans_color_array[i] for i in labels])

        # plot colored points and mark centroids as (X)
        pylab.scatter(xy[:, 0], xy[:, 1], c=colors)
        pylab.scatter(res[:, 0], res[:, 1], marker='o', s=500, linewidths=2, c='none')
        pylab.scatter(res[:, 0], res[:, 1], marker='x', s=500, linewidths=2)
        pylab.savefig('/tmp/kmeans_'+str(time.time())+".png")
        pylab.clf()

        positions = []
        actual_pos = labels[0]
        positions.append(actual_pos)
        for i in labels:
            if actual_pos == i:
                continue
            else:
                if i not in positions:
                    actual_pos = i
                    positions.append(actual_pos)

        # Iterate the labels result from the kmeans
        for i in range(len(positions)):
            contours = []

            # Generate the contours of every cluster by number
            # Example: label 1, label 2, etc.
            for y in range(len(xy)):
                if labels[y] == i:
                    element = xy[y]
                    contours.append(element)

            contours = np.asarray(contours)

            clustered_points = []
            for point in contours[:, 0:3]:
                idx = point[0]
                idy = point[1]

                clustered_points.append((idx, idy))

            points_per_robot.append(clustered_points)

        return points_per_robot

    pass
