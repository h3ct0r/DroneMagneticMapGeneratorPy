from tvtk.tools import visual
from shapely.geometry import *
from shapely import affinity
import math_helper

__author__ = 'Hector Azpurua'


class Hexagon(object):

    ROTATE_ANGLES = {
        1: 0,
        2: 60,
        3: 120,
        4: 180,
        5: 240,
        6: 300,
    }

    def __init__(self, internal_points, external_points=None, debug=False):
        self.internal_points = internal_points
        self.external_points = external_points

        if external_points is not None:
            self.external_polygon = Polygon(external_points)
        else:
            self.external_polygon = None

        self.original_polygon = Polygon(internal_points)
        self.polygon = Polygon(internal_points)
        self.rotation_pos = 0
        pass

    def rotate_polygon(self, rotation_pos):
        if rotation_pos not in Hexagon.ROTATE_ANGLES.keys():
            print "Invalid rotation angle", rotation_pos
            return

        self.rotation_pos = rotation_pos
        self.polygon = affinity.rotate(self.original_polygon, Hexagon.ROTATE_ANGLES[rotation_pos])
        pass

    def get_start_end_points(self):
        start_pt = self.polygon.exterior.coords[0]
        end_pt = self.polygon.exterior.coords[-2]
        return start_pt, end_pt

    def extract_poly_coords(self, geom):
        if geom.type == 'Polygon':
            exterior_coords = geom.exterior.coords[:]
            interior_coords = []
            for i in geom.interiors:
                interior_coords += i.coords[:]
        elif geom.type == 'MultiPolygon':
            exterior_coords = []
            interior_coords = []
            for part in geom:
                epc = self.extract_poly_coords(part)  # Recursive call
                exterior_coords += epc['exterior_coords']
                interior_coords += epc['interior_coords']
        else:
            raise ValueError('Unhandled geometry type: ' + repr(geom.type))
        return {'exterior_coords': exterior_coords,
                'interior_coords': interior_coords}

    def get_path_points(self):
        return self.extract_poly_coords(self.polygon)['exterior_coords'][:-2]

    def get_rotation(self):
        return self.rotation_pos, Hexagon.ROTATE_ANGLES[self.rotation_pos]

    def get_polygon(self):
        return self.polygon

    def get_centroid(self):
        if self.external_polygon is not None:
            return int(self.external_polygon.centroid.x) - 10, int(self.external_polygon.centroid.y) - 2
        else:
            return int(self.polygon.centroid.x) - 10, int(self.polygon.centroid.y) - 2

    def get_dist(self, next_hex):
        p1 = self.get_path_points()[-2]
        p2 = next_hex.get_path_points()[0]

        d, theta = math_helper.points_to_vector(p1, p2)
        return d



