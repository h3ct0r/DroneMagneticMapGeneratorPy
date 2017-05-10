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
from math import pi, sqrt
import os


def load_background():
    z = np.loadtxt("/tmp/magnetic_ground_truth.np")
    for xx in xrange(0, 200):
            for yy in xrange(400, 600):
                z[yy][xx] = 0

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

user_home = os.path.expanduser('~')
USER_PREFERENCE_FILE = user_home + "/" + ".sim_preferences.json"

point_list = []
trajectory_start_pt = None

with open(USER_PREFERENCE_FILE, 'r') as f:
    data = json.load(f)
    point_list = data["point_list"]
    trajectory_start_pt = data["trajectory_start_pt"]

while is_loop_active:

    screen.fill(BLACK)
    screen.blit(background, backgroundRect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_loop_active = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            background = load_background()

    for i in xrange(len(point_list)):
        x1 = point_list[i][0]
        y1 = point_list[i][1]

        if i+1 < len(point_list):
            x2 = point_list[i+1][0]
            y2 = point_list[i+1][1]

            pygame.draw.line(screen, (255, 10, 10), [x2, y2], [x1, y1], 5)

    for border in point_list:
        pygame.draw.circle(screen, (0, 0, 0), border, 10)


    clock.tick(30)
    pygame.display.flip()
    pygame.display.set_caption('FPS: ' + str(clock.get_fps()))

    pass