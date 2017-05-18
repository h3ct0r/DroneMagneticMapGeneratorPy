import numpy as np
import random

__author__ = 'Hector Azpurua'


class BackgroundGenerator(object):

    def __init__(self, np_file='/tmp/magnetic_ground_truth.np', width=800, height=600):
        self.np_file = np_file
        self.width = width
        self.height = height
        self.mat_output = np.zeros((self.height , self.width))
        pass

    def generate_background(self, low_limit=1, high_limit=5):
        for i in xrange(random.randint(low_limit, high_limit)):
            size = random.randint(200, 400)
            sigma = size * random.uniform(0.09, 0.2)
            g = self.gen_gauss(size, sigma)

            center = (random.randint(0, self.width), random.randint(0, self.height))

            for x in xrange(g.shape[0]):
                for y in xrange(g.shape[1]):
                    pos = (center[0] + x, center[1] + y)

                    if self.width > pos[0] >= 0 and self.height > pos[1] >= 0:
                        self.mat_output[pos[1]][pos[0]] = self.mat_output[pos[1]][pos[0]] + g[y, x]
                pass
            pass

    def gen_gauss(self, size=10, sigma=1):
        zeroes = (size, size)
        g = np.zeros(zeroes)

        for i in xrange(-(size - 1)/2, (size - 1)/2):
            for j in xrange(-(size - 1)/2, (size - 1)/2):
                x0 = (size + 1)/2
                y0 = (size + 1)/2
                x = i + x0
                y = j + y0
                g[y, x] = np.exp( -( pow((x-x0), 2) + pow((y-y0), 2)) / (2.*sigma*sigma) )
            pass
        pass

        return g
        pass

    def get_mat(self):
        return self.mat_output

    def save_mat(self):
        np.savetxt(self.np_file, self.get_mat())
        pass
pass

if __name__ == '__main__':

    print "Testing background generator"

    bGen = BackgroundGenerator()
    bGen.generate_background()
    bGen.save_mat()