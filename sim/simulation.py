import json
import re
import subprocess
import time
from math import degrees

from shapely import affinity
from shapely.geometry import *

import config
import math_helper

__author__ = 'Hector Azpurua'

class Sim(object):

    robot_colors = {
        'a': (102, 0, 0),
        'b': (76, 153, 0),
        'c': (0, 102, 204),
        'd': (255, 102, 102),
        'e': (255, 153, 51),
        'f': (255, 102, 255),
        'g': (160, 160, 160),
        'h': (51, 0, 102),
        'i': (135, 104, 106),
        'j': (0, 200, 20),
        'k': (205, 17, 240),
        'l': (100, 100, 100),
        'm': (255, 0, 0),
        'n': (0, 255, 0)
    }

    color_key = (127, 33, 33)

    black = (0, 0, 0)
    white = (255, 255, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)
    blue = (0, 60, 255)
    yellow = (255, 255, 0)
    light_blue = (0, 128, 255)

    rot_angle_dict = {
        "1": 30,
        "2": 90,
        "3": 150,
        "4": 210,
        "5": 270,
        "6": 330
    }

    hex_angle_dict = {
        "a": 0,
        "b": 60,
        "c": 120,
        "d": 180,
        "e": 240,
        "f": 300,
    }

    rot_angle_list = ["1", "2", "3", "4", "5", "6"]
    hex_angle_list = ["a", "b", "c", "d", "e", "f"]

    def __init__(self):
        self.start_date = int(time.time())
        self.simulation_done = False
        self.continue_simulation = False
        self.user_preference_file = config.USER_PREFERENCE_FILE
        self.number_of_robots = config.NUMBER_OF_ROBOTS
        self.battery_autonomy = config.BATTERY_AUTONOMY
        self.line_width = config.LINE_WIDTH
        self.debug = config.DEBUG

        self.radius = config.RADIUS
        self.hexes_wide = config.HEXES_WIDE
        self.hexes_high = config.HEXES_HIGH
        self.number_of_robots = config.NUMBER_OF_ROBOTS
        self.half_radius = config.HALF_RADIUS
        self.half_hex_height = config.HALF_HEX_HEIGHT

        self.hex_list = []
        self.hex_intersection = []
        self.robot_paths = {}
        self.robot_path_angles = {}
        self.obstacles_hexagon = set([])

        self.battery_autonomy = config.BATTERY_AUTONOMY
        self.line_width = config.LINE_WIDTH

        self.point_list = []
        self.hex_intersection = []
        self.adjacency_dict = {}

        self.trajectory_start_pt = (0, 0)

        self.robot_waypoints_json = None

        self.robot_waypoints = dict()
        self.robot_waypoints['robots'] = {}
        self.robot_waypoints['robots_centroids'] = {}
        self.robot_waypoints['point_inside_hex'] = {}
        self.robot_waypoints['border_hex'] = {}

        self.generated_leaflet_pos = [(281, 138), (310, 155), (319, 172), (261, 138), (256, 147), (315, 181),
                                      (310, 190), (250, 155), (245, 163), (305, 198), (300, 207), (240, 172),
                                      (249, 189), (280, 207), (260, 207), (259, 206)]
        self.generated_leaflet_pos_battery = 0

        self.redraw = False

        self.hex_list = math_helper.get_hex_point_list(self.hexes_wide, self.hexes_high,
                                                       self.radius, self.half_hex_height, config.THETA)
        self.distances_dict = {}
        self.poly_union = None

        self.user_selected_angle = 0
        self.user_selected_algo = 2
        self.user_selected_algo_description = ['ksplit', 'GA', 'Kmeans', 'Division']
        self.is_remove_mode_active = False
        self.obstacles_hexagon = set([])
        self.hex_intersection_map = {}

        self.robot_base_height = config.ROBOT_BASE_HEIGHT

    def update_points(self, p):
        self.point_list = p

    def do_simulation(self):

        print "self.hex_list", self.hex_list
        print "self.point_list", self.point_list

        self.hex_intersection = []
        counter = 1
        if len(self.point_list) > 1 and self.point_list[0] == self.point_list[-1]:
            border_polygon = Polygon(self.point_list)
            for i in xrange(len(self.hex_list)):
                if i in self.obstacles_hexagon:
                    continue

                hex_poly = self.hex_list[i]
                if hex_poly.within(border_polygon) or hex_poly.intersects(border_polygon):
                    self.hex_intersection.append(i)
                    self.hex_intersection_map[i] = counter
                    counter += 1

        print "self.hex_intersection", self.hex_intersection
        if len(self.hex_intersection) <= 0:
            print "Cannot continue, there is no hex intersections..."
            return

        if self.user_selected_angle == 0:
            Sim.hex_angle_dict = {
                "a": 0,
                "b": 60,
                "c": 120,
                "d": 180,
                "e": 240,
                "f": 300,
            }
        else:
            Sim.hex_angle_dict = {
                "a": 0,
                "b": 60,
                "c": 120,
                "d": 180,
                "e": 240,
                "f": 300,
                "g": 45,
                "h": 90,
                "i": 135,
                "j": 180,
                "k": 225,
                "l": 270,
                "m": 315,
                "n": 360
            }

        self.adjacency_dict = {}
        adjacency_dict_1_to_n = {}
        adjacency_dict_0_to_n = {}

        for i in self.hex_intersection:
            self.adjacency_dict[i] = []
            adjacency_dict_1_to_n[self.hex_intersection_map[i]] = []
            adjacency_dict_0_to_n[self.hex_intersection_map[i] - 1] = []
            poly_a = self.hex_list[i]
            for j in self.hex_intersection:
                if i == j:
                    continue
                poly_b = self.hex_list[j]

                if int(poly_a.distance(poly_b)) <= 1:
                    self.adjacency_dict[i].append(j)
                    adjacency_dict_1_to_n[self.hex_intersection_map[i]].append(self.hex_intersection_map[j])
                    adjacency_dict_0_to_n[self.hex_intersection_map[i] - 1].append(self.hex_intersection_map[j] - 1)

        print "Hex intersected :", len(self.hex_intersection), self.hex_intersection

        # Positions starting with 0 to n
        hex_positions = dict()
        hex_positions[str(0)] = self.trajectory_start_pt
        for index in self.hex_intersection:
            hex_poly = self.hex_list[index]
            center = (int(hex_poly.centroid.x), int(hex_poly.centroid.y))
            hex_positions[str(self.hex_intersection_map[index])] = center
            print self.hex_intersection_map[index], center

        print adjacency_dict_0_to_n
        print hex_positions

        self.start_date = int(time.time())

        ga_object = dict()
        ga_object['distances'] = hex_positions
        ga_object['adjacency'] = adjacency_dict_0_to_n
        ga_object['start_point'] = '0'

        json_ga_object = json.dumps(ga_object)
        print json_ga_object

        f = open('/tmp/adjacency_list.gamtsp', "w")
        f.write(str(json_ga_object))
        f.close()

        # K-MEANS
        p = subprocess.Popen(["python",
                              "/Users/h3ct0r/PycharmProjects/route_map/sim/tests/kmeans_toursplit_textmode.py",
                              "/tmp/adjacency_list.gamtsp", str(self.number_of_robots),
                              "/tmp/sol.mtsp"], stdout=subprocess.PIPE)

        out, err = p.communicate()
        out_split = out.split()
        print "RESULT", out_split

        self.robot_paths = {}
        robot_paths_array = []
        ins = open('/tmp/sol.mtsp', "r")
        for line in ins:
            elements = line.split()
            robot_paths_array = list(elements)
            print "elements:", elements
            actual_robot_letter = ''
            for elem in elements:
                if elem != '0':  # Start point
                    if math_helper.is_number(elem):
                        self.robot_paths[actual_robot_letter].append(elem)
                    else:
                        actual_robot_letter = elem
                        self.robot_paths[actual_robot_letter] = []

        ins.close()

        print "Robot trajectories:", self.robot_paths
        print "hex_list", len(self.hex_list)
        print "hex_intersection", self.hex_intersection
        print "number of robots", self.number_of_robots

        # Calculate the coverage points

        coverage_path_points = "["
        for i in xrange(len(self.hex_list[self.hexes_high + 1].exterior.coords)):
            point = self.hex_list[self.hexes_high + 1].exterior.coords[i]
            coverage_path_points += "[" + str(int(point[0])) + "," + str(int(point[1])) + "]"
            if i < len(self.hex_list[self.hexes_high + 1].exterior.coords) - 1:
                coverage_path_points += ","
        coverage_path_points += "]"

        print "coverage_path_points", coverage_path_points

        p = subprocess.Popen(["python",
                              "/Users/h3ct0r/PycharmProjects/route_map/sim/tests/coverage_path_verticalseg.py",
                              coverage_path_points,
                              str(self.line_width)], stdout=subprocess.PIPE)

        out, err = p.communicate()
        out_split = out.split()
        print "RESULT", out_split

        self.generated_leaflet_pos = []
        ins = open('/tmp/hex_coords_more_resolution_calculated.txt', "r")
        for line in ins:
            elements = line.split()
            self.generated_leaflet_pos.append((int(elements[0]), int(elements[1])))

        ins.close()

        print "self.generated_leaflet_pos len:", len(self.generated_leaflet_pos)

        self.generated_leaflet_pos_battery = 0
        for i in xrange(1, len(self.generated_leaflet_pos)):
            pos = self.generated_leaflet_pos[i]
            pos2 = self.generated_leaflet_pos[i - 1]
            d, theta = math_helper.points_to_vector(pos, pos2)
            self.generated_leaflet_pos_battery += d
            pass

        print "self.generated_leaflet_pos_battery:", self.generated_leaflet_pos_battery

        self.robot_waypoints = dict()
        self.robot_waypoints['robots'] = {}
        self.robot_waypoints['robots_centroids'] = {}
        self.robot_waypoints['point_inside_hex'] = {}
        self.robot_waypoints['border_hex'] = {}

        self.robot_path_angles = {}
        for key_robot, value in self.robot_paths.items():

            print "value", value

            list_hex_pos = ["-1"]
            counter = 10

            for i in range(len(value)):
                poly_a = self.hex_list[self.hex_intersection[int(value[i]) - 1]]

                if i + 1 < len(value):
                    poly_b = self.hex_list[self.hex_intersection[int(value[i + 1]) - 1]]

                    d, theta = math_helper.points_to_vector(
                        (poly_a.centroid.x, poly_a.centroid.y), (poly_b.centroid.x, poly_b.centroid.y))
                    degrees_theta = degrees(theta)
                    if degrees_theta < 0:
                        degrees_theta += 360

                    # Test all the possibilities in this angle and distance
                    print "Generating combinations, long hexagon"

                    cx1 = int(poly_a.centroid.x)
                    cy1 = int(poly_a.centroid.y)

                    cover_poly1 = Polygon(self.generated_leaflet_pos).buffer(0)
                    cover_center1 = (int(cover_poly1.centroid.x) - 10, int(cover_poly1.centroid.y) - 2)

                    cover_poly1 = Polygon(self.generated_leaflet_pos)
                    cover_poly1 = affinity.translate(cover_poly1, cx1 - cover_center1[0], cy1 - cover_center1[1])

                    cx2 = int(poly_b.centroid.x)
                    cy2 = int(poly_b.centroid.y)

                    cover_poly2 = Polygon(self.generated_leaflet_pos).buffer(0)
                    cover_center2 = (int(cover_poly2.centroid.x) - 10, int(cover_poly2.centroid.y) - 2)

                    cover_poly2 = Polygon(self.generated_leaflet_pos)
                    cover_poly2 = affinity.translate(cover_poly2, cx2 - cover_center2[0], cy2 - cover_center2[1])

                    for i1 in self.hex_angle_list:
                        angle1 = self.hex_angle_dict[i1]
                        poly_rotated1 = affinity.rotate(cover_poly1, angle1)
                        for i2 in self.hex_angle_list:
                            angle2 = self.hex_angle_dict[i2]
                            poly_rotated2 = affinity.rotate(cover_poly2, angle2)

                            d, theta = math_helper.points_to_vector(
                                poly_rotated1.exterior.coords[-2], poly_rotated2.exterior.coords[0])
                            if i1 not in self.distances_dict:
                                self.distances_dict[i1] = {}

                            if str(counter) not in self.distances_dict[i1]:
                                self.distances_dict[i1][str(counter)] = {}

                            self.distances_dict[i1][str(counter)][i2] = d
                            pass

                    list_hex_pos.append(str(counter))
                    counter += 1
                    pass

            graph = dict()
            graph[str(0)] = {}
            counter = 0
            next_pos = str(0)

            print "list_hex_pos", list_hex_pos
            print "distances_dict", self.distances_dict

            for h in range(len(list_hex_pos)):

                if h + 1 < len(list_hex_pos):
                    old_pos = str(list_hex_pos[h])
                    next_pos = str(list_hex_pos[h + 1])

                    if h == 0:
                        for elem in self.hex_angle_list:
                            for elem3 in self.hex_angle_list:
                                key = str(h) + str(elem) + next_pos + str(elem3)
                                graph[str(h)][key] = self.distances_dict[elem][next_pos][elem3]
                            pass
                        pass
                    else:
                        for elem in self.hex_angle_list:
                            for elem3 in self.hex_angle_list:
                                old_key = str(h - 1) + str(elem) + old_pos + str(elem3)
                                graph[old_key] = {}

                                for elem4 in self.hex_angle_list:
                                    new_key = str(h) + str(elem3) + next_pos + str(elem4)
                                    graph[old_key][new_key] = self.distances_dict[elem3][next_pos][elem4]
                                pass
                            pass
                        pass
                else:
                    graph[str(h)] = {}
                    if next_pos and next_pos != "0":

                        for elem in self.hex_angle_list:
                            for elem3 in self.hex_angle_list:
                                old_key = str(h - 1) + str(elem) + next_pos + str(elem3)
                                graph[old_key] = {}
                                graph[old_key][str(h)] = self.distances_dict[elem][next_pos][elem3]
                            pass
                        pass
                pass

                counter += 1
            pass

            print list_hex_pos
            print 0, str(len(list_hex_pos)-1)
            print "graph:", graph
            print "graph keys length:", len(graph.keys()), graph.keys()
            print "hex_angle_list size:", len(self.hex_angle_list)

            print "shortest_path", '0', str(len(list_hex_pos)-1)
            path = math_helper.shortest_path(graph, '0', str(len(list_hex_pos)-1))
            sort_path = []
            for i in path:
                sort_path.append(i)

            print "key", key_robot, sort_path

            angles_calculated = []

            # Use the user defined angle variable to draw the angle of the hexagons
            if self.user_selected_angle == 0:
                sub_array = sort_path[1:-1]
                for h in range(len(sub_array)):
                    node = sub_array[h]
                    res_re = re.findall(r'[a-z]', node)
                    if h == 0:
                            print "res_re[0] res_re[1]", res_re[0], res_re[1]
                            angles_calculated.append(res_re[0])
                            angles_calculated.append(res_re[1])
                    else:
                            print "res_re[1]", res_re[1]
                            angles_calculated.append(res_re[1])

                if len(angles_calculated) <= 0:
                    angles_calculated.append("a")
            else:
                for i in xrange(len(self.hex_intersection)):
                    if self.user_selected_angle == 1:
                        angles_calculated.append("a")
                    elif self.user_selected_angle == 2:
                        angles_calculated.append("b")
                    elif self.user_selected_angle == 3:
                        angles_calculated.append("c")
                    elif self.user_selected_angle == 4:
                        angles_calculated.append("d")
                    elif self.user_selected_angle == 5:
                        angles_calculated.append("e")
                    else:
                        angles_calculated.append("f")

            print "key", key_robot, "angles calculated:", angles_calculated
            print "key", key_robot, "angles len:", len(angles_calculated)
            print "key", key_robot, "points len:", len(value)

            self.robot_path_angles[key_robot] = angles_calculated

            # Create the way point list to generate the animation
            self.robot_waypoints['robots'][key_robot] = []
            self.robot_waypoints['point_inside_hex'][key_robot] = dict()
            self.robot_waypoints['border_hex'][key_robot] = dict()
            self.robot_waypoints['robots_centroids'][key_robot] = []

            path_list = self.robot_paths[key_robot]

            print "path_list", path_list

            for path_index in range(len(path_list)):
                hex_poly = self.hex_list[self.hex_intersection[int(path_list[path_index]) - 1]]
                cx = int(hex_poly.centroid.x)
                cy = int(hex_poly.centroid.y)
                if len(angles_calculated) <= 0:
                    hex_line_angle = 0
                else:
                    hex_line_angle = Sim.hex_angle_dict[angles_calculated[path_index]]

                cover_center = (int(self.hex_list[self.hexes_high + 1].centroid.x) - 0,
                                int(self.hex_list[self.hexes_high + 1].centroid.y) - 0)

                cover_poly = Polygon(self.generated_leaflet_pos)
                cover_poly = affinity.translate(cover_poly, cx - cover_center[0], cy - cover_center[1])
                cover_poly = affinity.rotate(cover_poly, hex_line_angle)

                int_pos_list = []
                for pos in cover_poly.exterior.coords[0:-2]:
                    int_pos = (int(pos[0]), int(pos[1]))
                    int_pos_list.append(int_pos)

                cover_hex_list = []
                for pos in hex_poly.exterior.coords:
                    int_pos = (int(pos[0]), int(pos[1]))
                    cover_hex_list.append(int_pos)

                self.robot_waypoints['robots'][key_robot].extend(int_pos_list)
                self.robot_waypoints['point_inside_hex'][key_robot][path_index] = list(int_pos_list)
                self.robot_waypoints['border_hex'][key_robot][path_index] = cover_hex_list
                self.robot_waypoints['robots_centroids'][key_robot].append((cx, cy))

            self.robot_waypoints['robots'][key_robot].append(self.trajectory_start_pt)

            print "key_robot:", key_robot, self.robot_waypoints['robots'][key_robot]
        pass

        self.robot_waypoints['start_point'] = self.trajectory_start_pt
        self.robot_waypoints['points_per_hex'] = len(self.generated_leaflet_pos)
        self.robot_waypoints['battery_autonomy'] = self.battery_autonomy

        print "hex_positions", hex_positions
        print "robot_paths_array", robot_paths_array

        distances_hex_positions = {}

        for key, value in hex_positions.items():
            distances_hex_positions[key] = {}
            for key2, value2 in hex_positions.items():
                if key == key2:
                    distances_hex_positions[key][key2] = 0
                    continue
                d, theta = math_helper.points_to_vector(value, value2)
                distances_hex_positions[key][key2] = d

        self.continue_simulation = False
        pass
