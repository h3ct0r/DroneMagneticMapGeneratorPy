from shapely import affinity
from shapely.geometry import *
import sim.tsp_solver

from scipy.spatial import distance
import networkx as nx

import math_helper
import numpy as np
import math
from scipy.cluster.vq import *

import matplotlib.pyplot as plt
from hexagon_lawnmower import HexagonLawnmower
import warnings
import random
import time
from tsp_solver import TspSolver

class CoverHexagon(object):
    def __init__(self, vertices, hex_radius, lawnmower_width, angle, meter_pixel_ratio=1.0, robot_size=1):
        self.poly_obj = Polygon(vertices)
        self.vertices = list(self.poly_obj.convex_hull.exterior.coords)

        self.theta = angle
        self.robot_size = robot_size
        self.hex_radius = hex_radius * meter_pixel_ratio
        self.lawnmower_width = lawnmower_width * meter_pixel_ratio
        self.intersecting_hexes = []
        self.robot_hex_allocations = {}
        self.robot_hex_tour = {}

        self.get_intersecting_hexagons()
        pass

    def get_vertices(self):
        """
        Get the vertices of the region of interest polygon
        :return: 
        """
        return self.vertices

    def get_tours(self):
        """
        Get the computed tours
        :return: 
        """
        return self.robot_hex_tour

    @staticmethod
    def get_best_angles_for_path(h_tour):
        # optimize route angles
        print 'h_tour', h_tour
        G = nx.Graph()
        for i in xrange(len(h_tour) - 1):
            h1 = h_tour[i]
            h2 = h_tour[i + 1]

            comb1 = h1.getStartStopListForAllAngles()
            comb2 = h2.getStartStopListForAllAngles()

            for k1, v1 in comb1.items():
                for k2, v2 in comb2.items():
                    d = distance.euclidean(v1[1], v2[0])
                    G.add_edge(str(h1.getId()) + '|' + str(k1), str(h2.getId()) + '|' + str(k2), weight=d)

            if i == 0:
                h1 = h_tour[i]
                comb1 = h1.getStartStopListForAllAngles()
                for k1, v1 in comb1.items():
                    G.add_edge('start', str(h1.getId()) + '|' + str(k1), weight=0.0)

            if i == len(h_tour) - 2:
                h2 = h_tour[i + 1]
                comb2 = h2.getStartStopListForAllAngles()
                for k2, v2 in comb2.items():
                    G.add_edge(str(h2.getId()) + '|' + str(k2), 'end', weight=0.0)

        shortest_path = nx.shortest_path(G, source='start', target='end')
        shortest_path = shortest_path[1:-2]
        for e in shortest_path:
            k, a = e.split('|')
            h_tour[int(k)].setAngle(int(a))

        return h_tour
        pass

    def optimize_tours(self):
        """
        For every cluster in robot_hex_allocations
        perform a TSP solver to get the visiting sequence that minimize
        traveled distance
        :return: 
        """
        if len(self.robot_hex_allocations.keys()) <= 0:
            return None

        for k, v in self.robot_hex_allocations.items():
            print k, v

            hex_centroids = {}
            for h in v:
                hex_centroids[h.getCenter()] = h

            centroids = hex_centroids.keys()

            tsp = TspSolver(centroids, verbose=True, max_iterations=1000)
            tour = tsp.get_tour()
            self.robot_hex_tour[k] = [hex_centroids[centroids[i]] for i in tour]
            for i in xrange(len(self.robot_hex_tour[k])):
                self.robot_hex_tour[k][i].setId(i)

        if self.theta == -1:
            print 'Optimize route angles'

            for k in self.robot_hex_tour.keys():
                v = self.robot_hex_tour[k]
                self.robot_hex_tour[k] = self.get_best_angles_for_path(v)

        pass

    @staticmethod
    def minimum_bounding_rectangle(hull_points):
        """
        Find the smallest bounding rectangle for a set of points.
        Returns a set of points representing the corners of the bounding box.
        From:
        http://stackoverflow.com/questions/13542855/python-help-to-implement-an-algorithm-to-find-the-minimum-area-rectangle-for-gi

        :param points: an nx2 matrix of coordinates
        :rval: an nx2 matrix of coordinates
        """
        pi2 = np.pi / 2.

        hull_points = np.asarray(hull_points)

        # calculate edge angles
        #edges = np.zeros((len(hull_points) - 1, 2))
        edges = hull_points[1:] - hull_points[:-1]

        #angles = np.zeros((len(edges)))
        angles = np.arctan2(edges[:, 1], edges[:, 0])

        angles = np.abs(np.mod(angles, pi2))
        angles = np.unique(angles)

        # find rotation matrices
        rotations = np.vstack([
            np.cos(angles),
            np.cos(angles - pi2),
            np.cos(angles + pi2),
            np.cos(angles)]).T
        rotations = rotations.reshape((-1, 2, 2))

        # apply rotations to the hull
        rot_points = np.dot(rotations, hull_points.T)

        # find the bounding points
        min_x = np.nanmin(rot_points[:, 0], axis=1)
        max_x = np.nanmax(rot_points[:, 0], axis=1)
        min_y = np.nanmin(rot_points[:, 1], axis=1)
        max_y = np.nanmax(rot_points[:, 1], axis=1)

        # find the box with the best area
        areas = (max_x - min_x) * (max_y - min_y)
        best_idx = np.argmin(areas)

        # return the best box
        x1 = max_x[best_idx]
        x2 = min_x[best_idx]
        y1 = max_y[best_idx]
        y2 = min_y[best_idx]
        r = rotations[best_idx]

        rval = np.zeros((4, 2))
        rval[0] = np.dot([x1, y2], r)
        rval[1] = np.dot([x2, y2], r)
        rval[2] = np.dot([x2, y1], r)
        rval[3] = np.dot([x1, y1], r)

        return rval.tolist()

    def get_intersecting_hexagons(self):
        """
        Get a list of hexagon objects that intersect or 
        is inside the vertices of the region of interest polygon
        :return: 
        """
        print 'vertices', self.vertices
        chull = list(self.poly_obj.convex_hull.exterior.coords)

        # get the minimum bounding box of convex hull
        min_bbox = CoverHexagon.minimum_bounding_rectangle(chull)
        print 'min_bbox:', min_bbox

        # get the angle of the box
        dx = min_bbox[0][0] - min_bbox[1][0]
        dy = min_bbox[0][1] - min_bbox[1][1]
        rads = math.atan2(-dy, dx)
        rads %= 2 * math.pi
        degs = math.degrees(rads)
        print 'degrees rotated:', degs

        # generate a polygon object and
        # rotate to horizontal plane
        poly_box = Polygon(min_bbox)
        poly_box = affinity.rotate(poly_box, degs - 360)
        box_coords = list(poly_box.exterior.coords)
        print 'straight bbox coordinates:', box_coords

        # start point, upper left point
        ulp = box_coords[1]
        lrp = box_coords[3]

        startx = ulp[0] + 1
        starty = ulp[1] + 1

        hex_w = 2 * self.hex_radius  # hex width
        hex_w *= 0.75  # to bring toghether hexagons
        hex_h = (2 * hex_w) / math.sqrt(3)  # hex height

        print 'hex width:', hex_w
        print 'hex height:', hex_h

        hh = int(math.ceil((lrp[0] - ulp[0]) / hex_w))
        hv = int(math.ceil((lrp[1] - ulp[1]) / (hex_h / 2)))
        hv += 1

        print 'Number of hexes horizontal:', hh, 'vertical:', hv
        print 'Start coordinate:', (startx, starty)

        # calculate hexagons centroids inside the minimum bounding box
        base_x = startx
        hex_positions = []
        for j in xrange(hv):
            if j % 2 != 0:
                base_x = startx + hex_w
            else:
                base_x = startx

            for i in xrange(hh):
                x = base_x + ((hex_w * 2) * (i))
                y = starty + ((hex_h / 2) * (j))
                p = Point(x, y)
                p = affinity.rotate(p, degs, origin=poly_box.centroid, use_radians=False)
                h = HexagonLawnmower([p.coords[0][0], p.coords[0][1]], self.hex_radius, self.lawnmower_width,
                                     angle=self.theta)

                if self.poly_obj.contains(p) or self.poly_obj.intersects(p):
                    self.intersecting_hexes.append(h)

        print 'Hexagon intersecting_hexes:', len(self.intersecting_hexes), self.intersecting_hexes
        return self.intersecting_hexes

    def calculate_clusters(self):

        self.robot_hex_allocations = {}
        for i in xrange(self.robot_size):
            self.robot_hex_allocations[i] = []

        if self.robot_size <= 1:
            self.robot_hex_allocations[0] = self.intersecting_hexes
            return self.robot_hex_allocations

        if self.robot_size > len(self.intersecting_hexes):
            raise ValueError('The number of clusters must be more or equal to the number of cells')

        print 'len(self.intersecting_hexes)', len(self.intersecting_hexes)

        hex_centroids = {}
        for h in self.intersecting_hexes:

            hex_centroids[h.getCenter()] = h

        print 'hex_centroids', hex_centroids

        xy = np.asarray(hex_centroids.keys())
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
                    print 'data', data, 'cluster_size', self.robot_size
                    res, labels = kmeans2(data, self.robot_size, 90)
                    print 'labels', labels, 'res', res
                    continue_loop_kmeans = False
                except Warning:
                    print "Warning.."

        base_colors = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)) for i in xrange(self.robot_size)]
        colors = [base_colors[i] for i in labels]

        # plot colored points and mark centroids as (X)
        plt.scatter(xy[:, 0], xy[:, 1], c=colors)
        plt.scatter(res[:, 0], res[:, 1], marker='o', s=500, linewidths=2, c='none')
        plt.scatter(res[:, 0], res[:, 1], marker='x', s=500, linewidths=2)
        plt.savefig('/tmp/kmeans_' + str(time.time()) + ".png")
        plt.clf()

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

            clustered_hexobj = []
            for point in contours[:, 0:3]:
                idx = point[0]
                idy = point[1]

                h_polygon_obj = hex_centroids[(idx, idy)]
                clustered_hexobj.append(h_polygon_obj)

            self.robot_hex_allocations[i] = clustered_hexobj

        return self.robot_hex_allocations

if __name__ == "__main__":
    vertex_l = [(454.0, 207.0), (350.0, 208.0), (325.0, 309.0), (475.0, 362.0), (454.0, 207.0)]
    hex_radius = 40
    lawnmower_w = 10
    angle = -1

    ch = CoverHexagon(vertex_l, hex_radius, lawnmower_w, angle, robot_size=2)
    ch.get_intersecting_hexagons()
    ch.calculate_clusters()
    ch.optimize_tours()
    print ch.get_tours()