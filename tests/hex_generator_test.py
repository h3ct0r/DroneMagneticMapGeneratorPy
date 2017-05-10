import math

from shapely import affinity
from shapely.geometry import *
import numpy as np
import pygame


class HexagonCover(object):

    def __init__(self, c, r, w, angle=90):
        if r < w:
            raise ValueError('Radius cannot be smaller than the lawnmower width')

        self.center = c
        self.radius = r
        self.lawnmower_width = w

        self.vertices = list(self.calcVertices())
        self.lawnmower_path = self.calcLawnmower(angle)
        pass

    def getCenter(self):
        return self.center[0], self.center[1]

    def getLawnmower(self):
        return self.lawnmower_path

    def getVertices(self):
        return self.vertices

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

        return path

def minimum_bounding_rectangle(hull_points):
    """
    Find the smallest bounding rectangle for a set of points.
    Returns a set of points representing the corners of the bounding box.
    From:
    http://stackoverflow.com/questions/13542855/python-help-to-implement-an-algorithm-to-find-the-minimum-area-rectangle-for-gi

    :param points: an nx2 matrix of coordinates
    :rval: an nx2 matrix of coordinates
    """
    from scipy.ndimage.interpolation import rotate
    pi2 = np.pi/2.

    hull_points = np.asarray(hull_points)

    # calculate edge angles
    edges = np.zeros((len(hull_points)-1, 2))
    edges = hull_points[1:] - hull_points[:-1]

    angles = np.zeros((len(edges)))
    angles = np.arctan2(edges[:, 1], edges[:, 0])

    angles = np.abs(np.mod(angles, pi2))
    angles = np.unique(angles)

    # find rotation matrices
    rotations = np.vstack([
        np.cos(angles),
        np.cos(angles-pi2),
        np.cos(angles+pi2),
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

def point_inside_polygon(x,y,poly):

    n = len(poly)
    inside =False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

if __name__ == "__main__":

    r = 40
    l_width = 10

    # big polygon
    p_vert = [(300, 100), (700, 110), (770, 400), (500, 500), (200, 400), (300, 100)]
    poly = Polygon(p_vert)
    chull = list(poly.convex_hull.exterior.coords)

    # get the minimum bounding box of convex hull
    min_bbox = minimum_bounding_rectangle(chull)
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

    hex_w = 2 * r  # hex width
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

        for i in xrange((hh / 2) + 1):
            x = base_x + ((hex_w * 2) * (i))
            y = starty + ((hex_h / 2) * (j))
            p = Point(x, y)
            p = affinity.rotate(p, degs, origin=poly_box.centroid, use_radians=False)
            if poly.contains(p) or poly.intersects(p):
                hex_positions.append([p.coords[0][0], p.coords[0][1]])

    print 'Hexagon positions:', len(hex_positions), hex_positions
    draw_points = hex_positions

    h_list = []
    for center in hex_positions:
        h = HexagonCover(center, r, l_width)
        h_list.append(h)

    #print h_list

    # h = HexagonCover(c, r, l_width)
    # print 'vertices:', h.getVertices()

    # draw_points = h.getLawnmower()
    # print 'lawnmower:', draw_points

    # DRAWING ROUTINES! ----------- ---------- ------------

    pygame.init()
    screen = pygame.display.set_mode( (1500, 800) )

    is_loop_active = True

    BLACK = (0,   0,   0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255,   0)
    RED = (255,   0,   0)
    BLUE = (0,  60,   255)
    YELLOW = (255, 255,   0)

    while is_loop_active:

        #is_loop_active = False

        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_loop_active = False

        for i in xrange(len(p_vert)):
            pos_index = p_vert[i]
            x1 = int(pos_index[0])
            y1 = int(pos_index[1])

            if i+1 < len(p_vert):
                next_index = p_vert[i + 1]
                x2 = int(next_index[0])
                y2 = int(next_index[1])

                pygame.draw.line(screen, WHITE, [x2, y2], [x1, y1])
            pygame.draw.circle(screen, WHITE, [x1, y1], 2)

        for i in xrange(len(draw_points)):
            pos_index = draw_points[i]
            x1 = int(pos_index[0])
            y1 = int(pos_index[1])

            if i+1 < len(draw_points):
                next_index = draw_points[i + 1]
                x2 = int(next_index[0])
                y2 = int(next_index[1])

                pygame.draw.line(screen, WHITE, [x2, y2], [x1, y1])
            pygame.draw.circle(screen, WHITE, [x1, y1], 2)

        for i in xrange(len(box_coords)):
            pos_index = box_coords[i]
            x1 = int(pos_index[0])
            y1 = int(pos_index[1])

            if i+1 < len(box_coords):
                next_index = box_coords[i + 1]
                x2 = int(next_index[0])
                y2 = int(next_index[1])

                pygame.draw.line(screen, BLUE, [x2, y2], [x1, y1])
            pygame.draw.circle(screen, BLUE, [x1, y1], 2)

        for h in h_list:
            pygame.draw.polygon(screen, YELLOW, h.getVertices(), 2)
            pygame.draw.polygon(screen, YELLOW, h.getLawnmower(), 2)

        pygame.display.flip()
