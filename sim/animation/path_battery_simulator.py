from shapely.geometry import *
from mayavi import mlab
from tvtk.tools import visual
import numpy as np
import time
import math_helper
from robot_ball import RobotBall

__author__ = 'Hector Azpurua'


class TimeAlive(object):

    def __init__(self, threshold=2):
        self.last_time = int(time.time())
        self.threshold = threshold
    pass

    def is_alive(self):
        actual_time = int(time.time())
        if actual_time - self.last_time >= self.threshold:
            return False
        else:
            return True

    def update_time(self):
        self.last_time = int(time.time())


class MasterCommand(object):

    def __init__(self, robot_list, debug=True):
        self.robot_list = robot_list
        self.robot_timealive = dict()

        for r in self.robot_list:
            self.robot_timealive[r.get_id()] = TimeAlive()
    pass

    def receive_keepalive(self, robot_id):
        robot = self.get_robot(robot_id)

        if robot is None:
            print "No robot found with id", robot_id
            return

        self.robot_timealive[robot.get_id()].update_time()
    pass

    def update_robot_list(self, robot_list):
        self.robot_list = robot_list

    def remove_robot(self, r_id):
        if r_id in self.robot_timealive:
            del self.robot_timealive[r_id]

        robot_index = None
        for i in xrange(len(self.robot_list)):
            if self.robot_list[i].get_id() == r_id:
                robot_index = i

        if robot_index is not None:
            print "Remove robot:", r_id, "index:", robot_index
            self.robot_list.pop(robot_index)

    def check_alive(self):
        dead_r = []
        alive_r = []

        for key, kalive in self.robot_timealive.items():
            r = self.get_robot(key)
            if kalive.is_alive():
                alive_r.append(key)
            else:
                if r.get_status() != RobotBall.STATUS_END:
                    dead_r.append(key)

        return dead_r, alive_r
    pass

    # def reallocate_path_of_robot(self, id):
    #     r = None
    #     remaining_hex = []
    #
    #     # get hexagons not completed by the robot ID1
    #     # get the remaining robots
    #     # if the remainig robots are 1
    #         # then add those paths to robot ID2
    #         # and rerun the TSP solver and angle optimization
    #     # if the remaining robots are > 1
    #         # allocate the remaining paths among the closer robots
    #         # and rerun the TSP solver and angle optimization
    #     # else
    #         # return path cannot be completed
    # pass

    def get_robot(self, robot_id):
        robot = None
        for r in self.robot_list:
            if r.get_id() == robot_id:
                robot = r
        return robot

    def reallocate_path_of_robot(self, robot_id):
        print "Reallocating", robot_id
        robot = self.get_robot(robot_id)

        if robot is None:
            print "No robot found with id", robot_id
            return

        r_hex = robot.get_hex_list()
        remaining_hex = []
        for i in xrange(robot.get_hex_index(), len(r_hex.keys())):
            remaining_hex.append(r_hex[i])

        print "Remaining hexes", len(remaining_hex)

        # Alive robots
        alive_robots = []
        for key, k_alive in self.robot_timealive.items():
            if k_alive.is_alive():
                alive_robots.append(key)

        if len(alive_robots) == 1:
            print "Allocating the paths of robot", robot_id, "to robot", alive_robots[0]

            alive_robot = self.get_robot(alive_robots[0])
            alive_robot.add_hex_list(remaining_hex)  # add and reorder the visit sequence of alive_robot hexagons
        elif len(alive_robots) > 1:
            print "Allocating the paths to the remaining robots", alive_robots

            robot_allocations = dict()
            for i in xrange(len(remaining_hex)):
                centroid_3d = remaining_hex[i].get_centroid()
                centroid = (int(centroid_3d[0]), int(centroid_3d[1]))

                closer_id = None
                closer_distance = 99999
                for r_id in alive_robots:
                    rx, ry, rz = self.get_robot(r_id).get_pos()
                    d, theta = math_helper.points_to_vector(centroid, (rx, ry))
                    print "Distance", d, "robot", r_id, "closer distance", closer_distance, "closer_id", closer_id
                    if d < closer_distance:
                        closer_distance = d
                        closer_id = r_id

                if closer_id not in robot_allocations:
                    robot_allocations[closer_id] = []

                print "Final Distance", d, "robot", r_id, "closer distance", closer_distance, "closer_id", closer_id
                print "\n"
                robot_allocations[closer_id].append(i)

            print "Robot allocations by closeness:", robot_allocations

            for key_robot, hex_indexes in robot_allocations.items():
                r = self.get_robot(key_robot)
                allocated_hexes = []
                for i in hex_indexes:
                    allocated_hexes.append(remaining_hex[i])

                r.add_hex_list(allocated_hexes)
            pass
        else:
            print "Cannot continue with allocations: No more active robots to allocate"
            return
    pass

    def rearrange_robot_paths(self):
        pass
pass


class PathBatterySimulator(object):

    color_codes = [
        (0.6, 0.0, 0.0),
        (0.4, 0.7, 0.0),
        (0.0, 0.4, 0.8),
        (1.0, 0.4, 0.4),
        (1.0, 0.6, 0.2),
        (1.0, 0.4, 1.0),
        (0.63, 0.63, 0.63),
        (0.2, 0.0, 0.4),
        (0.53, 0.41, 0.42),
        (0.0, 0.78, 0.08),
        (0.8, 0.07, 0.94),
        (0.39, 0.39, 0.39),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0)
    ]

    ball_radius = 5
    curve_radius = 4

    def __init__(self, hex_list, np_file='/tmp/magnetic_ground_truth.np', robot_height=40, width=800, height=600,
                 start_point=(0, 0, 0), message='experiment default message...', battery=99999):
        self.debug = False
        self.animator = None
        self.movement_mode = 0
        self.start_point = start_point
        self.robot_height = robot_height
        self.message = message

        self.start_time = int(time.time() * 1000)
        self.timestep = 0

        self.width = width
        self.height = height

        self.f = mlab.figure(size=(self.width, self.height))
        visual.set_viewer(self.f)

        v = mlab.view(270, 180)
        #print v

        engine = mlab.get_engine()
        self.s = engine.current_scene
        self.s.scene.interactor.add_observer('KeyPressEvent', self.keypress_callback)

        self.robots = []

        colors = list(PathBatterySimulator.color_codes)

        for key, local_hex_list in sorted(hex_list['internal_routes'].items()):
            color = colors.pop(0)

            ball = visual.sphere(color=color, radius=PathBatterySimulator.ball_radius)
            ball.x = self.start_point[0]
            ball.y = self.start_point[1]
            ball.z = self.start_point[2]

            r, g, b = color
            rt = r + (0.25 * (1 - r))
            gt = g + (0.25 * (1 - g))
            bt = b + (0.25 * (1 - b))
            curve_color = (rt, gt, bt)

            curve = visual.curve(color=curve_color, radius=PathBatterySimulator.curve_radius)

            r_ball = RobotBall(key, local_hex_list, hex_list['external_routes'][key], ball, curve, battery=battery)
            self.robots.append(r_ball)

        x = np.linspace(0, self.width, 1)
        y = np.linspace(0, self.height, 1)

        z = np.loadtxt(np_file)
        z *= 255.0/z.max()

        # HARDCODED
        # Todo: REMOVE THIS CODE ON THE FINAL RELEASE
        for xx in xrange(0, 200):
            for yy in xrange(400, 600):
                z[yy][xx] = 0

        mlab.surf(x, y, z)

        self.master_cmd = MasterCommand(self.robots)

        self.robot_pos = open('/tmp/robot_log.txt', 'a')

    pass

    def keypress_callback(self, vtk_obj, event):
        key_code = vtk_obj.GetKeyCode()
        classname = vtk_obj.GetClassName()

        ascii_offset = 96
        robot_id = chr(int(key_code) + ascii_offset)

        print classname, event, key_code

        robot = None
        for r in self.robots:
            if r.get_id() == robot_id:
                robot = r

        if robot is None:
            print "No robot found with id", robot_id
            return

        robot.set_status(RobotBall.STATUS_DAMAGED)
        print "Robot", robot_id, robot.get_status()

        pass

    def animate(self):
        print "Animating...\n"
        end_counter = 0

        self.timestep += 1

        for i in xrange(len(self.robots)):
            robot = self.robots[i]
            robot.update_pos()

            print robot.get_id(), robot.get_status()

            if robot.get_status() == RobotBall.STATUS_END or robot.get_status() == RobotBall.STATUS_DAMAGED:
                end_counter += 1
            else:
                self.master_cmd.receive_keepalive(robot.get_id())

                hex_centroids = robot.get_all_hexagon_centroid()
                centroids_no_space = str(hex_centroids).replace(" ", "")

                self.robot_pos.write("timestep:" + str(self.timestep) + " id:" + str(robot.get_id()) +
                                     " index:" + str(robot.get_hex_index()) + " centroids:" + centroids_no_space + "\n")

        dead_r, alive_r = self.master_cmd.check_alive()

        print "dead", dead_r, "alive", alive_r, "n robots", len(self.robots), "end_counter", end_counter

        if len(dead_r) > 0:
            print "dead", dead_r, "alive", alive_r

            for r_id in dead_r:
                self.master_cmd.reallocate_path_of_robot(r_id)
                robot_index = None
                for i in xrange(len(self.robots)):
                    if self.robots[i].get_id() == r_id:
                        robot_index = i

                if robot_index is not None:
                    print "Remove robot:", r_id, "index:", robot_index
                    self.robots.pop(robot_index)
                    self.master_cmd.remove_robot(r_id)
        else:
            if end_counter >= len(self.robots):
                print "Exiting path simulation..."

                # -------------------
                with open("/tmp/exp_results.txt", "a") as myfile:
                    end_time = int(time.time() * 1000) - self.start_time
                    myfile.write(self.message + " " + str(end_time))
                    myfile.write("\n")
                # -------------------

                self.animator.itimer.Stop()
                self.robot_pos.close()
                mlab.close(all=True)

    def start_animation(self):
        self.animator = visual.iterate(240, self.animate)
        visual.show()
        return self.animator

if __name__ == '__main__':

    print "Testing path simulator"

    point_list_3robots = {
        'external_routes': {
            'a': {
                0: [(620, 277), (600, 311), (560, 311), (540, 277), (560, 242), (600, 242), (620, 277)],
                1: [(680, 311), (660, 346), (620, 346), (600, 311), (620, 277), (660, 277), (680, 311)],
                2: [(740, 277), (720, 311), (680, 311), (660, 277), (680, 242), (720, 242), (740, 277)],
                3: [(800, 311), (780, 346), (740, 346), (720, 311), (740, 277), (780, 277), (800, 311)],
                4: [(740, 346), (720, 381), (680, 381), (660, 346), (680, 311), (720, 311), (740, 346)],
                5: [(800, 381), (780, 415), (740, 415), (720, 381), (740, 346), (780, 346), (800, 381)],
                6: [(740, 415), (720, 450), (680, 450), (660, 415), (680, 381), (720, 381), (740, 415)],
                7: [(680, 381), (660, 415), (620, 415), (600, 381), (620, 346), (660, 346), (680, 381)],
                8: [(680, 450), (660, 484), (620, 484), (600, 450), (620, 415), (660, 415), (680, 450)],
                9: [(620, 484), (600, 519), (560, 519), (540, 484), (560, 450), (600, 450), (620, 484)],
                10: [(620, 415), (600, 450), (560, 450), (540, 415), (560, 381), (600, 381), (620, 415)],
                11: [(560, 450), (540, 484), (500, 484), (480, 450), (500, 415), (540, 415), (560, 450)],
                12: [(560, 381), (540, 415), (500, 415), (480, 381), (500, 346), (540, 346), (560, 381)],
                13: [(620, 346), (600, 381), (560, 381), (540, 346), (560, 311), (600, 311), (620, 346)],
                14: [(560, 311), (540, 346), (500, 346), (480, 311), (500, 277), (540, 277), (560, 311)]
            }
        },
        'internal_routes': {
            'a': {
                0: [(560, 241, 216.13662511671038), (559, 242, 212.50220244073611), (548, 262, 158.17280366860302), (540, 276, 109.40112091197319), (540, 276, 109.40112091197319), (557, 266, 162.01508510293456), (575, 255, 202.46790867468923), (593, 245, 230.79013383667072), (599, 241, 231.72390135212493), (599, 241, 231.72390135212493), (609, 259, 202.69125781381547), (609, 259, 202.69125781381547), (592, 269, 184.32172452016755), (574, 279, 158.26637293056854), (556, 290, 126.98699330113079), (550, 293, 117.18761365374566), (550, 293, 117.18761365374566), (560, 311, 125.35795667882455), (560, 311, 125.35795667882455), (577, 301, 147.72333786105057), (595, 290, 166.29511573037269), (613, 280, 178.51627578300867), (618, 277, 181.19855231092328), (618, 277, 181.19855231092328), (606, 297, 173.31993616370588), (599, 311, 177.17424800844776)],
                1: [(600, 310, 177.16230629028334), (600, 311, 178.09971030900354), (612, 331, 208.21033258916478), (620, 345, 235.47201825493124), (620, 345, 235.47201825493124), (620, 325, 208.38835218257174), (620, 304, 182.97352991554473), (620, 283, 178.19913027991598), (620, 276, 182.06387614215586), (620, 276, 182.06387614215586), (640, 276, 181.55429861983967), (640, 276, 181.55429861983967), (640, 296, 178.3443677923878), (640, 317, 193.88509529400145), (640, 338, 217.41944781338472), (640, 345, 226.3455502536296), (640, 345, 226.3455502536296), (660, 345, 197.94793627586967), (660, 345, 197.94793627586967), (660, 325, 184.37208082029579), (660, 304, 173.3883339754733), (660, 283, 175.71331622791052), (660, 278, 178.48459719170293), (660, 278, 178.48459719170293), (672, 298, 167.16447858826416), (680, 311, 159.99390034021712)],
                2: [(680, 310, 160.12911499285292), (681, 311, 159.19843381535259), (704, 310, 142.41618825536548), (720, 311, 132.79482117025839), (720, 311, 132.79482117025839), (703, 301, 149.65950808537289), (685, 290, 166.22008616121201), (667, 280, 176.43057583880372), (661, 276, 179.72978316545073), (661, 276, 179.72978316545073), (671, 259, 195.42487146786075), (671, 259, 195.42487146786075), (688, 269, 185.31827900248709), (706, 279, 170.45825841435715), (724, 290, 154.07444108163082), (730, 293, 148.34632447610824), (730, 293, 148.34632447610824), (740, 276, 166.44199918242739), (740, 276, 166.44199918242739), (723, 266, 184.84458186076029), (705, 255, 198.16069109343749), (687, 245, 212.82420155615003), (682, 242, 212.09790192275614), (682, 242, 212.09790192275614), (706, 242, 211.07727601698127), (721, 242, 213.35385334019827)],
                3: [(780, 276, 140.19285372280982), (779, 275, 142.14056359110748), (756, 276, 157.13074749126929), (740, 275, 167.76970853154796), (740, 275, 167.76970853154796), (757, 285, 144.74918234953751), (775, 296, 120.95467414642465), (793, 306, 99.81542982735975), (799, 310, 92.829395662072727), (799, 310, 92.829395662072727), (789, 327, 83.734184237654219), (789, 327, 83.734184237654219), (772, 317, 99.88846506654896), (754, 307, 118.16116391255761), (736, 296, 142.28662140697404), (730, 293, 148.34632447610824), (730, 293, 148.34632447610824), (720, 310, 133.75075112584022), (720, 310, 133.75075112584022), (737, 320, 115.07093978169361), (755, 331, 91.629133231190821), (773, 341, 78.199261876213072), (778, 344, 74.618266184865377), (778, 344, 74.618266184865377), (754, 344, 80.208054286984094), (739, 344, 93.188595718765015)],
                4: [(661, 345, 196.22924324052951), (661, 346, 196.87097345772975), (673, 366, 153.66216529070826), (681, 380, 135.56189870641674), (681, 380, 135.56189870641674), (681, 360, 160.49215943904221), (681, 339, 159.67593848627152), (681, 318, 158.58777706502701), (681, 311, 159.19843381535259), (681, 311, 159.19843381535259), (701, 311, 143.56312480288599), (701, 311, 143.56312480288599), (701, 331, 133.74187497899908), (701, 352, 126.36903989554689), (701, 373, 95.338136114087121), (701, 380, 94.972584234439168), (701, 380, 94.972584234439168), (721, 380, 67.177914929203197), (721, 380, 67.177914929203197), (721, 360, 97.164506808838837), (721, 339, 109.78702892980853), (721, 318, 125.83871559693104), (721, 313, 130.37869833009211), (721, 313, 130.37869833009211), (733, 333, 105.53731868520268), (741, 346, 90.523360936972225)],
                5: [(740, 345, 91.847818328280368), (739, 346, 91.713930319516749), (728, 366, 60.38424876272672), (720, 380, 68.253690381006137), (720, 380, 68.253690381006137), (737, 370, 53.923457573811028), (755, 359, 68.992473418564117), (773, 349, 72.393079575207366), (779, 345, 73.646485661955126), (779, 345, 73.646485661955126), (789, 363, 60.82613745944829), (789, 363, 60.82613745944829), (772, 373, 40.0), (754, 383, 40.0), (736, 394, 53.541224107538135), (730, 397, 57.160867193061996), (730, 397, 57.160867193061996), (740, 415, 48.858491266703112), (740, 415, 48.858491266703112), (757, 405, 40.0), (775, 394, 40.0), (793, 384, 40.0), (798, 381, 40.0), (798, 381, 40.0), (786, 401, 40.0), (779, 415, 40.0)],
                6: [(741, 415, 48.456899012846598), (741, 414, 48.587614170857094), (729, 394, 58.343721456530986), (721, 380, 67.177914929203197), (721, 380, 67.177914929203197), (721, 400, 64.075926755872587), (721, 421, 58.009855970969511), (721, 442, 51.399936845642522), (721, 449, 49.431504012816902), (721, 449, 49.431504012816902), (701, 449, 59.07703921189767), (701, 449, 59.07703921189767), (701, 429, 71.212821471255467), (701, 408, 84.467036903563866), (701, 387, 93.60537430488408), (701, 380, 94.972584234439168), (701, 380, 94.972584234439168), (681, 380, 135.56189870641674), (681, 380, 135.56189870641674), (681, 400, 124.65481181691436), (681, 421, 103.32553606478601), (681, 442, 80.08400250499929), (681, 447, 75.074574222026882), (681, 447, 75.074574222026882), (669, 427, 113.23836166880794), (661, 414, 146.17195012310361)],
                7: [(621, 345, 235.60124608525305), (620, 346, 236.9160077017894), (609, 366, 238.48527069869289), (601, 380, 231.83383921819222), (601, 380, 231.83383921819222), (618, 370, 243.39353641342839), (636, 359, 243.39275904405724), (654, 349, 210.96634277566559), (660, 345, 197.94793627586967), (660, 345, 197.94793627586967), (670, 363, 183.76475625422472), (670, 363, 183.76475625422472), (653, 373, 201.74380373457052), (635, 383, 230.20610495652477), (617, 394, 229.09281855844463), (611, 397, 222.85998832185777), (611, 397, 222.85998832185777), (621, 415, 188.13873751973293), (621, 415, 188.13873751973293), (638, 405, 197.66139073058062), (656, 394, 183.88111486546609), (674, 384, 150.5418567615346), (679, 381, 139.91046825167007), (679, 381, 139.91046825167007), (667, 401, 152.78312291834908), (660, 415, 146.25240069142382)],
                8: [(660, 415, 146.25240069142382), (659, 414, 149.60389519890106), (636, 415, 179.56074357209977), (620, 414, 190.57095843711238), (620, 414, 190.57095843711238), (637, 424, 158.67697686431222), (655, 435, 117.8135414485814), (673, 445, 84.29055950168808), (679, 449, 74.757211260720595), (679, 449, 74.757211260720595), (669, 466, 65.100111397603385), (669, 466, 65.100111397603385), (652, 456, 85.878337030961035), (634, 446, 112.82348242068069), (616, 435, 140.76547599345446), (610, 432, 146.59499625574722), (610, 432, 146.59499625574722), (600, 449, 106.13200100179584), (600, 449, 106.13200100179584), (617, 459, 91.926869174677989), (635, 470, 73.726314266525122), (653, 480, 59.269464810684276), (658, 483, 55.884941340374112), (658, 483, 55.884941340374112), (634, 483, 60.488736186059946), (619, 483, 61.502362531382701)],
                9: [(600, 518, 40.0), (601, 517, 40.0), (612, 497, 51.547679308666972), (620, 483, 61.490150752743716), (620, 483, 61.490150752743716), (603, 493, 53.383173003272717), (585, 504, 40.0), (567, 514, 40.0), (561, 518, 40.0), (561, 518, 40.0), (551, 500, 44.313706597504371), (551, 500, 44.313706597504371), (568, 490, 49.941306552129738), (586, 480, 60.017034719460767), (604, 469, 75.589741218980038), (610, 466, 80.580428821547969), (610, 466, 80.580428821547969), (600, 448, 108.02449279040164), (600, 448, 108.02449279040164), (583, 458, 82.523570921988451), (565, 469, 61.698697427092611), (547, 479, 49.736371764766652), (542, 482, 47.50585923864886), (542, 482, 47.50585923864886), (554, 462, 61.674057860649825), (561, 448, 79.094485256383024)],
                10: [(600, 380, 230.56662594664792), (599, 379, 229.63068949308996), (576, 380, 185.08493563618285), (560, 379, 147.38513056446254), (560, 379, 147.38513056446254), (577, 389, 182.20175641848732), (595, 400, 202.38827801021148), (613, 410, 198.86013352464971), (619, 414, 190.65652038756352), (619, 414, 190.65652038756352), (609, 431, 148.59160832177818), (609, 431, 148.59160832177818), (592, 421, 158.13884828067793), (574, 411, 149.10690757381502), (556, 400, 126.68252532993847), (550, 397, 116.89075201798842), (550, 397, 116.89075201798842), (540, 414, 87.613111230066892), (540, 414, 87.613111230066892), (557, 424, 102.81199493983812), (575, 435, 111.05265983796056), (593, 445, 109.77267474713854), (598, 448, 107.05252381523421), (598, 448, 107.05252381523421), (574, 448, 90.129761402759172), (559, 448, 77.41415944986332)],
                11: [(560, 450, 76.139838676679901), (560, 449, 77.188129676637288), (548, 429, 85.489053568992261), (540, 415, 86.88837497224452), (540, 415, 86.88837497224452), (540, 435, 71.863766203167387), (540, 456, 58.043992262799435), (540, 477, 48.64635647993591), (540, 484, 46.519501834923659), (540, 484, 46.519501834923659), (520, 484, 43.347589861139632), (520, 484, 43.347589861139632), (520, 464, 47.1398527150549), (520, 443, 53.436498759981248), (520, 422, 61.396757235435587), (520, 415, 64.075926755872587), (520, 415, 64.075926755872587), (500, 415, 50.624523061950605), (500, 415, 50.624523061950605), (500, 435, 47.220069346966078), (500, 456, 44.088621370206418), (500, 477, 41.959193806083135), (500, 482, 41.604408624803511), (500, 482, 41.604408624803511), (488, 462, 41.91844274363585), (480, 449, 40.0)],
                12: [(499, 414, 50.315258603154376), (500, 415, 50.624523061950605), (523, 414, 67.281039849154993), (539, 415, 85.514902724685626), (539, 415, 85.514902724685626), (522, 405, 69.696420554781895), (504, 394, 56.142691675892415), (486, 384, 40.0), (480, 380, 40.0), (480, 380, 40.0), (490, 363, 48.959713372280461), (490, 363, 48.959713372280461), (507, 373, 59.783398940567722), (525, 383, 79.057487553231994), (543, 394, 105.18707292364694), (549, 397, 114.9216495914218), (549, 397, 114.9216495914218), (559, 380, 144.81357282529251), (559, 380, 144.81357282529251), (542, 370, 108.1276213945478), (524, 359, 76.684542774883923), (506, 349, 56.851721072384876), (501, 346, 53.164497220207302), (501, 346, 53.164497220207302), (525, 346, 74.189292099266908), (540, 346, 95.569154739651395)],
                13: [(599, 380, 229.2361014566174), (600, 379, 230.96398834299134), (611, 359, 247.77381619554563), (619, 345, 235.27810038990322), (619, 345, 235.27810038990322), (602, 355, 234.91221236838729), (584, 366, 201.92767780302833), (566, 376, 162.16564163463627), (560, 380, 147.16168103775857), (560, 380, 147.16168103775857), (550, 362, 126.85434926372936), (550, 362, 126.85434926372936), (567, 352, 161.26670511213064), (585, 342, 189.90095185882018), (603, 331, 199.92753017614095), (609, 328, 207.80930598020299), (609, 328, 207.80930598020299), (599, 310, 176.25197545181018), (599, 310, 176.25197545181018), (582, 320, 164.56000798483214), (564, 331, 133.52897475190559), (546, 341, 102.19652859951728), (541, 344, 95.981060525179686), (541, 344, 95.981060525179686), (553, 324, 118.01675120376139), (560, 310, 125.22085852701721)],
                14: [(560, 311, 125.35795667882455), (560, 310, 125.22085852701721), (548, 290, 117.16491679940881), (540, 276, 109.40112091197319), (540, 276, 109.40112091197319), (540, 296, 91.675849809708609), (540, 317, 88.619163974773187), (540, 338, 90.434450525343891), (540, 345, 94.972584234439168), (540, 345, 94.972584234439168), (520, 345, 68.226952040731746), (520, 345, 68.226952040731746), (520, 325, 68.22939872478338), (520, 304, 70.53371983184698), (520, 283, 82.799719226510206), (520, 276, 89.434851335368123), (520, 276, 89.434851335368123), (500, 276, 70.852651229786943), (500, 276, 70.852651229786943), (500, 296, 59.74395116939786), (500, 317, 54.552246128687187), (500, 338, 51.428034838923573), (500, 343, 52.176478470068943), (500, 343, 52.176478470068943), (488, 323, 48.750016384640588), (480, 310, 44.979506076052061)]
            }
        }
    }

    point_list = point_list_3robots
    pSim = PathBatterySimulator(point_list, start_point=(0, 0, 0))
    pSim.start_animation()