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

my_points = \
[(772.3563258846535, 104.74782350085405), (202.5343674320234, 104.74782350085435), (202.53436743202369, 499.6244438320629), (772.3563258846538, 499.62444383206264), (772.3563258846535, 104.74782350085405)]

my_points2 = \
[(432.90616497557914, 160.48594955804498), (311.6393096326941, 160.4859495580451), (311.63930963269434, 362.4290108401797), (432.90616497557926, 362.42901084017967), (432.90616497557914, 160.48594955804498)]

#my_points2 = [(300, 100), (700, 110), (770, 400), (500, 500), (200, 400)]
while is_loop_active:

    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_loop_active = False

    for i in xrange(len(my_points)):
        pos_index = my_points[i]
        x1 = int(pos_index[0])
        y1 = int(pos_index[1])

        if i+1 < len(my_points):
            next_index = my_points[i + 1]
            x2 = int(next_index[0])
            y2 = int(next_index[1])

            pygame.draw.line(screen, WHITE, [x2, y2], [x1, y1])

        label = mono_font.render(str(i + 1), 1, BLUE)
        screen.blit(label, (x1 + 10, y1))

        pygame.draw.circle(screen, WHITE, [x1, y1], 2)

    for i in xrange(len(my_points2)):
        pos_index = my_points2[i]
        x1 = int(pos_index[0])
        y1 = int(pos_index[1])

        if i+1 < len(my_points2):
            next_index = my_points2[i + 1]
            x2 = int(next_index[0])
            y2 = int(next_index[1])

            pygame.draw.line(screen, BLUE, [x2, y2], [x1, y1])

        label = mono_font.render(str(i + 1), 1, BLUE)
        screen.blit(label, (x1 + 10, y1))

        pygame.draw.circle(screen, WHITE, [x1, y1], 2)

    label = mono_font.render(str(pygame.mouse.get_pos()), 1, BLUE)
    screen.blit(label, (0, 0))
    
    clock.tick(30)
    pygame.display.flip()
    pygame.display.set_caption('FPS: ' + str(clock.get_fps()))

    pass