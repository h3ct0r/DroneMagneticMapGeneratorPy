import math

from shapely import affinity
from shapely.geometry import *
import numpy as np


class HexagonLawnmower(object):

    def __init__(self, c, r, w, angle=90, valid_angles=None, id=-1):
        if r < w:
            raise ValueError('Radius cannot be smaller than the lawnmower width')

        self.id = id
        self.center = c
        self.radius = r
        self.lawnmower_width = w
        self.angle = angle

        self.vertices = list(self.calcVertices())
        self.polyObj = Polygon(self.vertices)
        self.lawnmower_path = self.calcLawnmower(self.angle)

        if valid_angles is None:
            self.valid_angles = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350]
        else:
            self.valid_angles = valid_angles

        pass

    def getId(self):
        return self.id

    def getAngle(self):
        return self.angle

    def getCenter(self):
        return self.center[0], self.center[1]

    def getPolyObj(self):
        return self.polyObj

    def getLawnmower(self):
        print 'h', self.getId(), self.getAngle()
        self.lawnmower_path = self.calcLawnmower(self.angle)
        return self.lawnmower_path

    def getVertices(self):
        return self.vertices

    def getStartStopListForAllAngles(self):
        res = {}
        for a in self.valid_angles:
            p = self.calcLawnmower(a)
            res[a] = ([p[0], p[-1]])

        return res

    def setAngle(self, a):
        self.angle = a

    def setId(self, id):
        self.id = id

    def calcVertices(self):
        x, y = self.getCenter()

        # angle from one point to the next
        tetha = math.pi / 3.0

        # generate all vertices
        for i in range(6):
            yield x + self.radius * math.cos(2 * math.pi * i / 6), y + self.radius * math.sin(2 * math.pi * i / 6)

    def calcLawnmower(self, angle):
        x, y = self.getCenter()

        # get the points forming a line intersecting the polygon
        l1 = self.vertices[3]
        l2 = self.vertices[0]

        # max and min vertical values for hexagon
        maxy = int(max([v[1] for v in self.vertices]) + 1)
        miny = int(min([v[1] for v in self.vertices]) - 1)

        # gen shapely poly
        h = Polygon(self.vertices)
        h = affinity.rotate(h, angle)

        # distance
        d = Point(l1).distance(Point(l2))
        seg_n = int(d / self.lawnmower_width)
        line_pts = [(l1[0] + (self.lawnmower_width * (i + 1)), l1[1]) for i in xrange(seg_n)]

        # gen path
        path = [l1]
        i = 0
        while i < seg_n:
            p = [line_pts[i]]
            if i + 1 < seg_n:
                p.append(line_pts[i + 1])
                i += 2
            else:
                i += 1

            for j in xrange(len(p)):
                inter_p = h.intersection(LineString([(p[j][0], maxy), (p[j][0], miny)]))
                inter_p = affinity.rotate(inter_p, -angle, origin=h.centroid)
                # todo: check this
                if not inter_p.is_empty:
                    inter = list(inter_p.coords)
                    if (i + j) % 2 == 0:
                        inter.reverse()

                    path.extend(inter)
        return path[1:]