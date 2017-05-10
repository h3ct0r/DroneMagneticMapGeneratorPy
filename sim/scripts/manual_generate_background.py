__author__ = 'h3ct0r'

from math import sin, cos, pi, sqrt, atan2, degrees
import random
from shapely.geometry import *
from shapely import affinity
import pygame
import re
import sys
from shapely.geometry import *
from shapely import affinity
import json
import numpy as np
from matplotlib import pyplot as plt


def generate_background(center, mat_output, low_limit=1, high_limit=5):
    size = random.randint(250, 250)
    sigma = size * random.uniform(0.09, 0.15)
    g = gen_gauss(size, sigma)

    g_x_mid = int(g.shape[0]/2)
    g_y_mid = int(g.shape[1]/2)

    for x in xrange(-g_x_mid, g_x_mid):
        for y in xrange(-g_y_mid, g_y_mid):
            pos = (center[0] + x, center[1] + y)

            if 800 > pos[0] >= 0 and 600 > pos[1] >= 0:
                mat_output[pos[1]][pos[0]] = mat_output[pos[1]][pos[0]] + g[y + g_y_mid, x + g_y_mid]
        pass

    return mat_output


def gen_gauss(size=10, sigma=1):
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


def load_background():
    z = np.loadtxt("/tmp/magnetic_ground_truth.np")
    plt.imsave("../background.png", z)
    background = pygame.image.load("../background.png")
    print "Background loaded..."
    return background

sys.setrecursionlimit(1500)

BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
GREEN = (0, 255,   0)
RED = (255,   0,   0)
BLUE = (0,  60,   255)
YELLOW = (255, 255,   0)

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600

pygame.init()
mono_font = pygame.font.SysFont("monospace", 12)
clock = pygame.time.Clock()

screen = pygame.display.set_mode( (IMAGE_WIDTH, IMAGE_HEIGHT) )

is_loop_active = True

mat_output = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH))

background = pygame.image.load("../background.png")
backgroundRect = background.get_rect()

while is_loop_active:

    screen.fill(BLACK)
    screen.blit(background, backgroundRect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_loop_active = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            mat_output = generate_background(pos, mat_output)
            np.savetxt("/tmp/magnetic_ground_truth.np", mat_output)
            background = load_background()


    clock.tick(30)
    pygame.display.flip()
    pygame.display.set_caption('FPS: ' + str(clock.get_fps()))

    pass