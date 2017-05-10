from tvtk.tools import visual
from shapely.geometry import *
import subprocess
from hexagon import Hexagon
import math_helper
import re
import numpy as np
from scipy.spatial import distance

__author__ = 'Hector Azpurua'


class RobotBall(object):

    STATUS_START = 'START'
    STATUS_END = 'END'
    STATUS_WAITING = 'WAITING'
    STATUS_DAMAGED = 'DAMAGED'
    STATUS_GOING_HOME = 'GOING_HOME'
    STATUS_GOING_TO_ROUTE = 'GOING_TO_ROUTE'
    STATUS_GOING_TO_NEXT_HEX = 'GOING_TO_NEXT_HEX'
    STATUS_ENDING = 'ENDING'

    def __init__(self, robot_id, hex_internal_list, hex_external_list, ball, hist_curve,
                 np_file='/tmp/magnetic_ground_truth.np', height=40, battery=99999, debug=True):
        self.robot_id = robot_id
        self.debug = debug
        self.status = 'GOING_TO_NEXT_HEX'
        self.hex_index = 0
        self.base_battery = battery
        self.battery = self.base_battery

        self.movement_mode = 0
        self.max_delta = 10
        self.step_p = 0.6  # 0.06
        self.ball = ball

        self.np_file = np_file
        np_mat = np.loadtxt(self.np_file)
        np_mat *= 255.0/np_mat.max()
        self.np_mat = np_mat

        self.height = height

        self.hex_external_list = hex_external_list
        self.hex_polygon = dict()

        for key in hex_internal_list.keys():
            hex_obj = Hexagon(hex_internal_list[key], external_points=self.hex_external_list[key])
            self.hex_polygon[key] = hex_obj

        self.hex_internal_list = hex_internal_list

        self.hist_curve = hist_curve
        self.last_position = [
            ball.y,
            ball.x,
            ball.z
        ]

        self.print_message("Starting pos: {0} {1} {2}".format(ball.x, ball.y, ball.z))

        self.home_position = self.last_position
        self.home_route = []
        self.return_to_route = []

        self.history = []
        self.wp_index = 0

        # Define first route to reach hexagon
        next_wp = self.hex_internal_list[self.hex_index][self.wp_index]
        go_next_wp = math_helper.get_line_points(self.last_position, next_wp, step=20)
        go_next_wp_3d = math_helper.get_3d_coverage_points(
            go_next_wp, self.height, self.np_file, np_mat=self.np_mat)
        self.next_hexagon_route = go_next_wp_3d
        pass

    def update_visit_point_list_using_self_hexagons(self):
        self.hex_internal_list = dict()
        for key in self.hex_polygon.keys():
            self.hex_internal_list[key] = math_helper.get_3d_coverage_points(
                 self.hex_polygon[key].get_path_points(), self.height, self.np_file)

        self.print_message("Hex internal list: {0}".format(self.hex_internal_list))

    def check_need_to_go_home(self):
        curr_wp = self.hex_internal_list[self.hex_index][self.wp_index]
        next_wp = None
        if self.wp_index + 1 < len(self.hex_internal_list[self.hex_index]):
            next_wp = self.hex_internal_list[self.hex_index][self.wp_index + 1]
        else:
            if self.hex_index + 1 < len(self.hex_internal_list):
                next_wp = self.hex_internal_list[self.hex_index + 1][0]

        curr_wp_2d = (curr_wp[0], curr_wp[1])
        home_2d = (self.home_position[0], self.home_position[1])
        self.print_message("curr_wp_2d {0}, home_2d {1}".format(curr_wp_2d, home_2d))
        go_home_route = math_helper.get_line_points(curr_wp_2d, home_2d, step=20)
        go_home_route_3d = math_helper.get_3d_coverage_points(
            go_home_route, self.height, self.np_file, np_mat=self.np_mat)

        if next_wp is None:
            self.status = RobotBall.STATUS_ENDING
            self.home_route = go_home_route_3d
            self.print_message("Ending!")
            return True

        next_wp_dst = distance.euclidean(curr_wp, next_wp)
        next_wp_2d = (next_wp[0], next_wp[1])

        home_dst = math_helper.get_distance_3d_path(go_home_route_3d)
        home_dst += home_dst * 0.1  # To address the error in the distance calculus

        go_home_next_wp_route = math_helper.get_line_points(next_wp_2d, home_2d, step=20)
        go_home_next_wp_route_3d = math_helper.get_3d_coverage_points(
            go_home_next_wp_route, self.height, self.np_file, np_mat=self.np_mat)
        home_next_wp_dst = math_helper.get_distance_3d_path(go_home_next_wp_route_3d)
        home_next_wp_dst += home_next_wp_dst * 0.1  # To address the error in the distance calculus

        if next_wp_dst + home_dst >= self.battery or next_wp_dst + home_next_wp_dst >= self.battery:
            self.status = RobotBall.STATUS_GOING_HOME
            self.home_route = go_home_route_3d
            self.return_to_route = go_home_route_3d[::-1]
            self.print_message("Going home!")
            return True

        return False

    def update_pos(self):
        self.print_message("Updating pos")

        if self.status == RobotBall.STATUS_END or self.status == RobotBall.STATUS_DAMAGED:
            self.print_message("End status!")
            return

        if self.battery <= 0:
            self.status = RobotBall.STATUS_END
            self.print_message("No battery!")
            return

        if self.status == RobotBall.STATUS_GOING_HOME or self.status == RobotBall.STATUS_ENDING:
            curr_wp = self.home_route[0]
            self.print_message("Going to home!")
        elif self.status == RobotBall.STATUS_GOING_TO_NEXT_HEX:
            curr_wp = self.next_hexagon_route[0]
            self.print_message("Going to next hexagon!")
        elif self.status == RobotBall.STATUS_GOING_TO_ROUTE:
            curr_wp = self.return_to_route[0]
            self.print_message("Going to route!")
        else:
            self.print_message("Normal WP h_index {0} of {1} wp_index {2} of {3}".format(
                self.hex_index, len(self.hex_internal_list), self.wp_index,
                                    len(self.hex_internal_list[self.hex_index])))
            curr_wp = self.hex_internal_list[self.hex_index][self.wp_index]
            if self.check_need_to_go_home():
                self.print_message("Need to go home!")
                return

        ball_pos = self.ball.pos.tolist()

        if self.debug:
            self.print_message("Current wp: {0} {1}".format(self.wp_index, curr_wp))
            self.print_message("Ball pos: {0}".format(ball_pos))
            self.print_message("Current hexagon: {0} of {1}".format(self.hex_index, len(self.hex_internal_list)))

        py, px, pz = curr_wp
        bx, by, bz = ball_pos

        if self.last_position != ball_pos:
            arr = visual.vector(float(bx), float(by), float(bz))
            self.history.append(arr)

            if len(self.history) > 2:
                self.hist_curve.extend(self.history)
                self.history[:] = []

        self.last_position = ball_pos

        dx = px - bx
        dy = py - by
        dz = pz - bz

        if self.debug:
            self.print_message("dx:{0} dy:{1} dz:{2}".format(dx, dy, dz))

        if abs(dx) > self.max_delta or abs(dy) > self.max_delta or abs(dz) > self.max_delta:
            if self.movement_mode == 0:
                err = self.step_p

                self.ball.x += dx * err
                self.ball.y += dy * err
                self.ball.z += dz * err
            else:
                err = self.step_p
                lim = 10

                ddx = dx * err
                ddy = dy * err
                ddz = dz * err

                if abs(ddx) > lim:
                    if cmp(ddx, 0) < 0:
                        self.ball.x += (lim * -1)
                    else:
                        self.ball.x += lim
                else:
                    self.ball.x += ddx

                if abs(ddy) > lim:
                    if cmp(ddy, 0) < 0:
                        self.ball.y += (lim * -1)
                    else:
                        self.ball.y += lim
                else:
                    self.ball.y += ddy

                if abs(ddz) > lim:
                    if cmp(ddz, 0) < 0:
                        self.ball.z += (lim * -1)
                    else:
                        self.ball.z += lim
                else:
                    self.ball.z += ddz
        else:
            if self.status == RobotBall.STATUS_GOING_HOME:
                if len(self.home_route) > 1:
                    self.home_route.pop(0)
                else:
                    self.status = RobotBall.STATUS_GOING_TO_ROUTE
                    self.battery = self.base_battery
                    self.print_message("Battery reloaded: {0}".format(self.battery))
            elif self.status == RobotBall.STATUS_GOING_TO_ROUTE:
                if len(self.return_to_route) > 1:
                    self.return_to_route.pop(0)
                else:
                    self.status = RobotBall.STATUS_START
                    self.print_message("Starting route again...")
            elif self.status == RobotBall.STATUS_GOING_TO_NEXT_HEX:
                if len(self.next_hexagon_route) > 1:
                    self.next_hexagon_route.pop(0)
                else:
                    self.status = RobotBall.STATUS_START
                    self.print_message("Starting new hex...")
            elif self.status == RobotBall.STATUS_ENDING:
                if len(self.home_route) > 1:
                    self.home_route.pop(0)
                else:
                    self.status = RobotBall.STATUS_END
                    self.print_message("Ended!")
            else:
                self.print_message("WP reached")
                if self.wp_index + 1 < len(self.hex_internal_list[self.hex_index]):
                    self.print_message("Added one to index {0} {1}".format(
                        self.wp_index+1, len(self.hex_internal_list[self.hex_index])))
                    self.wp_index += 1
                else:
                    self.wp_index = 0
                    if self.hex_index + 1 < len(self.hex_internal_list):
                        self.hex_index += 1

                        self.print_message("Increment index hexagon {0} of {1}".format(
                            self.hex_index, len(self.hex_internal_list) - 1))

                        self.status = RobotBall.STATUS_GOING_TO_NEXT_HEX
                        next_wp = self.hex_internal_list[self.hex_index][self.wp_index]
                        next_hex_route = math_helper.get_line_points(curr_wp, next_wp, step=20)
                        if len(next_hex_route) > 0:
                            go_hex_route = math_helper.get_3d_coverage_points(
                                next_hex_route, self.height, self.np_file, np_mat=self.np_mat)
                            self.next_hexagon_route = go_hex_route
                        else:
                            self.next_hexagon_route = [next_wp]
                        self.print_message("Hexagon route: {0}".format(self.next_hexagon_route))
                    else:
                        self.print_message("Ending")
                        self.hex_index = 0
                        self.status = RobotBall.STATUS_END

        battery_spent = distance.euclidean(self.last_position, self.ball.pos.tolist())

        # self.print_message("Compare pos: {0} of {1} is {2}".format(
        #                     self.last_position, self.ball.pos.tolist(), battery_spent))

        self.battery -= battery_spent
        self.print_message("Battery level {0} of {1}".format(
                            self.battery, self.base_battery))
        pass

    def optimize_hexagon_visit(self):
        # TODO: Fix this code and make it more readable and Object Oriented :(

        self.print_message("Optimizing hexagon angles...")

        f = open("/Users/h3ct0r/Sites/pointListOut.tsp", "w")
        for city_index, polygon in sorted(self.hex_polygon.items()): # hex_internal_list
            if self.debug:
                self.print_message("City index: {0} hex index: {0}".format(city_index, self.hex_index))
            point_list = polygon.get_path_points()

            if city_index < self.hex_index:
                continue

            hex_2d = [[x[0], x[1]] for x in point_list]

            hex_poly = Polygon(hex_2d).buffer(0)
            centroid = (int(hex_poly.centroid.x) - 10, int(hex_poly.centroid.y) - 2)

            f.write('%d,%d\n' % centroid)
        f.close()

        cmd = "python /Users/h3ct0r/PycharmProjects/hex_route_msc/tsp_hill_climbing.py -n 100000 " \
              "/Users/h3ct0r/Sites/pointListOut.tsp"
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = pipe.communicate()
        status = pipe.wait()

        if status:
            self.print_message("Solver failed; status: {0}".format(status))
            self.print_message("Error: {0}".format(error))
            exit(1)

        organized_coordinates = []
        solfile = '/Users/h3ct0r/Desktop/concorde/LINKERN/result'
        ins = open(solfile, "r")
        next(ins)
        for line in ins:
            node_number = line.split()
            organized_coordinates.append(int(node_number[0]))
        ins.close()

        if self.debug:
            self.print_message("Original TSP coords: {0}".format(organized_coordinates))

        while organized_coordinates[0] != 0:
            organized_coordinates.append(organized_coordinates.pop(0))

        if self.debug:
            self.print_message("Rotated TSP coords: {0} {1}".format(len(organized_coordinates), organized_coordinates))

        new_hex_polygon = dict()

        for i in xrange(self.hex_index):
            new_hex_polygon[i] = self.hex_polygon[i]

        for i in xrange(0, len(organized_coordinates)):
            index = i + self.hex_index
            new_hex_polygon[index] = self.hex_polygon[organized_coordinates[i] + self.hex_index]

        if self.debug:
            self.print_message("Old hex list: {0}, {1}".format(len(self.hex_polygon.keys()), self.hex_polygon))
            self.print_message("New hex list: {0}, {1}".format(len(new_hex_polygon), new_hex_polygon))

        self.hex_polygon = new_hex_polygon

        # Optimize angles!
        graph = dict()
        graph[str(0)] = {}
        counter = 0
        next_pos = str(0)

        for h in xrange(0, len(organized_coordinates)):
            if h + 1 < len(organized_coordinates):
                old_pos = str(h)
                next_pos = str(h + 1)

                if h == 0:
                    for elem in Hexagon.ROTATE_ANGLES.keys():
                        for elem3 in Hexagon.ROTATE_ANGLES.keys():
                            key = str(h) + self.get_letter_from_number(elem) + next_pos + self.get_letter_from_number(elem3)

                            p1 = self.hex_polygon[int(old_pos)]
                            p1.rotate_polygon(elem)
                            p2 = self.hex_polygon[int(next_pos)]
                            p2.rotate_polygon(elem3)

                            graph[str(h)][key] = p1.get_dist(p2)  # self.distances_dict[elem][next_pos][elem3]
                        pass
                    pass
                else:
                    for elem in Hexagon.ROTATE_ANGLES.keys():
                        for elem3 in Hexagon.ROTATE_ANGLES.keys():
                            old_key = str(h - 1) + self.get_letter_from_number(elem) + old_pos + self.get_letter_from_number(elem3)
                            graph[old_key] = {}

                            for elem4 in Hexagon.ROTATE_ANGLES.keys():
                                new_key = str(h) + self.get_letter_from_number(elem3) + next_pos + self.get_letter_from_number(elem4)

                                p1 = self.hex_polygon[int(old_pos)]
                                p1.rotate_polygon(elem3)
                                p2 = self.hex_polygon[int(next_pos)]
                                p2.rotate_polygon(elem4)

                                graph[old_key][new_key] = p1.get_dist(p2)

                                # graph[old_key][new_key] = 2  # self.distances_dict[elem3][next_pos][elem4]
                            pass
                        pass
                    pass
            else:
                graph[str(h)] = {}
                if next_pos and next_pos != "0":
                    for elem in Hexagon.ROTATE_ANGLES.keys():
                        for elem3 in Hexagon.ROTATE_ANGLES.keys():
                            old_key = str(h - 1) + self.get_letter_from_number(elem) + next_pos + self.get_letter_from_number(elem3)
                            graph[old_key] = {}

                            p1 = self.hex_polygon[h-1]
                            p1.rotate_polygon(elem)
                            p2 = self.hex_polygon[int(next_pos)]
                            p2.rotate_polygon(elem3)

                            graph[old_key][str(h)] = p1.get_dist(p2)

                            # graph[old_key][str(h)] = 3  # self.distances_dict[elem][next_pos][elem3]
                        pass
                    pass
            pass

            counter += 1
        pass

        # if self.debug:
        #     self.print_message("Graph: {0}".format(graph))
        #     self.print_message("Graph keys: {0} {1}".format(len(graph.keys()), graph.keys()))
        #     self.print_message("Shortest path between: {0} and {1}".format(0, len(organized_coordinates)-1))

        path = math_helper.shortest_path(graph, '0', str(len(organized_coordinates)-1))
        sort_path = []
        for i in path:
            sort_path.append(i)

        if self.debug:
            self.print_message("Shortest path: {0}".format(sort_path))

        angles_calculated = []
        sub_array = sort_path[1:-1]

        for h in range(len(sub_array)):
            node = sub_array[h]
            res_re = re.findall(r'[a-z]', node)
            if h == 0:
                # self.print_message("res_re[0] {0} res_re[1] {1}".format(res_re[0], res_re[1]))
                angles_calculated.append(res_re[0])
                angles_calculated.append(res_re[1])
            else:
                # self.print_message("res_re[1] {0}".format(res_re[1]))
                angles_calculated.append(res_re[1])

        if len(angles_calculated) <= 0:
            angles_calculated.append("a")

        if self.debug:
            self.print_message("Angles calculated: {0}".format(angles_calculated))

        for i in xrange(len(angles_calculated)):
            chr_angle = angles_calculated[i]
            int_angle = self.get_number_from_letter(chr_angle)

            hexagon = self.hex_polygon[i + self.hex_index]
            hexagon.rotate_polygon(int_angle)
            pass

        self.update_visit_point_list_using_self_hexagons()

        self.print_message("Optimization done!")
        pass

    @staticmethod
    def get_letter_from_number(num):
        ascii_offset = 96
        return chr(int(num) + ascii_offset)

    @staticmethod
    def get_number_from_letter(char):
        ascii_offset = 96
        return ord(char) - ascii_offset

    def print_message(self, msg):
        print "ID:" + str(self.robot_id) + "/" + self.status + ")", msg

    def add_hex_list(self, new_hex_list):
        starting_index = len(self.hex_polygon.keys())

        self.print_message("Adding new {0} hexagons to the original {1} ones".format(
            len(new_hex_list), len(self.hex_polygon)))

        for i in xrange(len(new_hex_list)):
            self.hex_polygon[starting_index] = new_hex_list[i]
            starting_index += 1

        self.print_message("Totalling {0} hexagons".format(len(self.hex_polygon)))
        self.update_visit_point_list_using_self_hexagons()
        self.optimize_hexagon_visit()

    def get_all_hexagon_centroid(self):
        centroid_list = []
        for i in xrange(len(self.hex_polygon)):
            centroid_list.append(self.get_hexagon_centroid(i))
        return centroid_list

    def get_current_hexagon_centroid(self):
        return self.get_hexagon_centroid(self.hex_index)

    def get_hexagon_centroid(self, index):
        h = self.hex_polygon[index]
        return h.get_centroid()

    def get_pos(self):
        return self.ball.x, self.ball.y, self.ball.z

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status

    def get_id(self):
        return self.robot_id

    def get_hex_list(self):
        return self.hex_polygon

    def get_hex_index(self):
        return self.hex_index

    def __str__(self):
        return self.robot_id + "/" + self.status

    def __repr__(self):
        return self.robot_id + "/" + self.status
pass
