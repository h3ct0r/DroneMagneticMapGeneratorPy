from shapely import affinity
from shapely.geometry import *
import sim.tsp_solver

from scipy.spatial import distance
import networkx as nx

import math_helper


class CoverPolygon(object):
    def __init__(self, vertices, lawnmower_width, angle, meter_pixel_ratio=1.0, spacement_mode='Normal',
                 point_spacement=1.0, path_with_minimized_points=False):

        self.poly_obj = Polygon(vertices)
        self.vertices = list(self.poly_obj.convex_hull.exterior.coords)

        self.path_with_minimized_points = path_with_minimized_points
        self.theta = angle
        self.spacement_mode = spacement_mode  # 'Spaced'
        self.lawnmower_width = lawnmower_width * meter_pixel_ratio
        self.point_spacement = point_spacement * meter_pixel_ratio
        self.lawnmower_path = list(self.calc_lawnmower())
        pass

    def get_lawnmower(self):
        return self.lawnmower_path

    def get_vertices(self):
        return self.vertices

    def gen_spaced_path(self, path):
        '''
        Get a sparced path to avoid visiting waypoints that are too close
        :param path:
        :return:
        '''

        neighbors = []
        for i in xrange(len(path)):
            for j in xrange(len(path)):
                if i == j:
                    continue

                p1 = path[i]
                p2 = path[j]
                d = distance.euclidean(p1, p2)
                if d < self.lawnmower_width + (self.lawnmower_width * 0.5):
                    neighbors.append((i, j))

        print 'neighbors:', neighbors

        G = nx.Graph()
        G.add_edges_from(neighbors)
        g_elements = nx.coloring.greedy_color(G, strategy=nx.coloring.strategy_saturation_largest_first)
        label_list = list(set(g_elements.values()))

        print 'label_list:', label_list

        elem_label = {}

        for i in xrange(len(g_elements)):
            label = g_elements[i]
            if label not in elem_label:
                elem_label[label] = []

            elem_label[label].append(i)
        pos = nx.spring_layout(G)

        sparced_path = []
        is_every_label_sparced = False
        while not is_every_label_sparced:
            print 'Generating...'

            for k in elem_label.keys():
                coords = [path[i] for i in elem_label[k]]
                solver = sim.tsp_solver.TspSolver(coords)
                tour = [coords[i] for i in solver.get_tour()]

                if len(sparced_path) > 0:
                    p = sparced_path[-1]
                    counter = 0
                    while distance.euclidean(p, tour[0]) < self.lawnmower_width + (self.lawnmower_width * 0.5) \
                            and counter < 3:
                        tour = [coords[i] for i in solver.get_tour()]
                        counter += 1

                    if counter >= 3:
                        print 'Repeat sparced path generation...'
                        sparced_path = []
                        break

                    tour = [coords[i] for i in solver.get_tour()]

                sparced_path += tour
            is_every_label_sparced = True

        return sparced_path

    def calc_lawnmower(self):
        rotate_angle = self.theta - 360

        r_poly_obj = affinity.rotate(self.poly_obj, rotate_angle)
        r_vertexes = list(r_poly_obj.exterior.coords)

        # max and min horizontal/vertical values
        maxx = int(max([v[0] for v in r_vertexes]) + 1)
        minx = int(min([v[0] for v in r_vertexes]) - 1)
        maxy = int(max([v[1] for v in r_vertexes]) + 1)
        miny = int(min([v[1] for v in r_vertexes]) - 1)

        print maxy, miny

        # distance of the upper point to the lower point of the figure to calculate how many
        # coverage lines do we need
        d = maxy - miny
        seg_n = int(d / self.lawnmower_width)

        print d, seg_n

        line_pts = [miny + (self.lawnmower_width * (i + 1)) for i in xrange(seg_n)]
        print line_pts

        # generate the lawnmower path
        path = []
        i = 0
        while i < seg_n:
            p = [line_pts[i]]
            if i + 1 < seg_n:
                p.append(line_pts[i + 1])
                i += 2
            else:
                i += 1

            for j in xrange(len(p)):
                intersect_obj = r_poly_obj.intersection(
                    LineString([(minx - 10, p[j]), (maxx + 10, p[j])])
                    )

                if not intersect_obj.is_empty:
                    inter = list(
                        r_poly_obj.intersection(
                            LineString([(maxx, p[j]), (minx, p[j])])
                            ).coords
                        )

                    if not self.path_with_minimized_points:
                        inter = math_helper.get_line_points(inter[0], inter[1], self.point_spacement)
                    else:
                        inter_tmp = [inter[0], inter[1]]
                        inter = inter_tmp

                    if (i + j) % 2 == 0:
                        inter.reverse()

                    path.extend(inter)

        if self.spacement_mode == 'Spaced':
            path = self.gen_spaced_path(path)

        # rotate the lawnmower path to the original angle
        lawn_path = LineString(path)
        lawn_path = affinity.rotate(lawn_path, rotate_angle * -1)

        # generate new polygon with the convex hull
        end_poly = Polygon(lawn_path.coords)
        c_hull = list(end_poly.convex_hull.exterior.coords)
        end_poly = Polygon(c_hull)

        # calculate centroids
        c1 = list(end_poly.centroid.coords)
        c2 = list(self.poly_obj.centroid.coords)

        # then translate the rotated figure to the original one
        lawn_path = affinity.translate(lawn_path, xoff=c2[0][0] - c1[0][0], yoff=c2[0][1] - c1[0][1])

        return list(lawn_path.coords)