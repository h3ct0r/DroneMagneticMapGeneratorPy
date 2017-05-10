from mayavi import mlab
from tvtk.tools import visual
import numpy as np

__author__ = 'Hector Azpurua'


class RoiSimulator(object):

    color_codes = [
        (0, 0, 0),
        (1, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (1, 1, 0),
        (0, 1, 1),
        (1, 0, 1)
    ]

    ball_radius = 10
    curve_radius = 5

    def __init__(self, wp_list, np_file='/tmp/magnetic_ground_truth.np', width=800, height=600):
        self.debug = True

        self.width = width
        self.height = height

        self.wp_list = wp_list

        self.f = mlab.figure(size=(self.width, self.height))
        visual.set_viewer(self.f)

        v = mlab.view(135, 180)

        self.balls = []
        self.trajectories = []

        colors = list(RoiSimulator.color_codes)
        color_black = colors.pop(0)
        color_red = colors.pop(0)

        wp_curve = visual.curve(color=color_red, radius=RoiSimulator.curve_radius)
        hist_pos = []

        for i in xrange(len(self.wp_list)):
            ball = visual.sphere(color=color_black, radius=RoiSimulator.ball_radius)
            wp = self.wp_list[i]

            ball.x = wp[1]
            ball.y = wp[0]
            ball.z = wp[2]

            self.balls.append(ball)

            arr = visual.vector(float(wp[1]), float(wp[0]), float(wp[2]))
            hist_pos.append(arr)

        wp_curve.extend(hist_pos)

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
    pass

    def anim(self):
        pass

    def start_animation(self):
        a = visual.iterate(20, self.anim)
        visual.show()
        return a

if __name__ == '__main__':

    print "Testing region of interest simulator"

    point_list = [
            (200, 200, 500),
            (10, 100, 500),
            (100, 10, 500),
            (100, 200, 500),
            (300, 200, 500)
        ]

    rSim = RoiSimulator(point_list)
    rSim.start_animation()
