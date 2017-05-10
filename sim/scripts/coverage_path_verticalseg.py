import pygame
import sys
import math
import json
import subprocess
import shapely
from shapely.geometry import *
from shapely import affinity
import heapq
import time

import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from geometry_helper import *

# Define some colors
DEEP_BLUE = (   0,   0,   50)
BLACK     = (   0,   0,   0)
WHITE     = ( 255, 255, 255)
GREEN     = (   0, 255,   0)
RED       = ( 255,   0,   0)
BLUE      = (   0,  60,   255)
YELLOW    = ( 255, 255,   0)

# Geosoft : program to create waypoints
# Restriction from south to north
# CPE tecnologia, VANT courses
#   Vant stmart one aibotix

pygame.init()
monoFont = pygame.font.SysFont("monospace", 15)

sizeX = 800
sizeY = 600
size = [sizeX, sizeY]
#screen = pygame.display.set_mode(size)
DISPLAY = (1, 1)
DEPTH = 32
FLAGS = 0
screen_mode = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)

screen = pygame.Surface((8000, 6000))

clickedPos = []

def shortest_path(G, start, end):
    def flatten(L):       # Flatten linked list of form [0,[1,[2,[]]]]
        while len(L) > 0:
            yield L[0]
            L = L[1]

    q = [(0, start, ())]  # Heap of (cost, path_head, path_rest).
    visited = set()       # Visited vertices.
    while True:
        (cost, v1, path) = heapq.heappop(q)
        if v1 not in visited:
            visited.add(v1)
            if v1 == end:
                return list(flatten(path))[::-1] + [v1]
            path = (v1, path)
            for (v2, cost2) in G[v1].iteritems():
                if v2 not in visited:
                    heapq.heappush(q, (cost + cost2, v2, path))

lineWidth = 10

#"""
pointsJson = sys.argv[1]
clickedPos = json.loads(pointsJson)
clickedPos.append(clickedPos[0])

if len(sys.argv) == 3:
    lineWidth = int(sys.argv[2])
#"""

min_left = sizeX
for pos in clickedPos:
    left = pos[0]
    if left < min_left:
        min_left = left

print "min_left:", min_left

done = False
drawLines = False
lineAngle = -1

#simulationState = 'GENERATE_POLYGON'
simulationState = 'CALCULATE_BEST_ANGLE'
#simulationState = 'SHOW_BEST_POLYGON'

lineAngle = 0

numberOfLines = int(math.ceil(abs(sizeX - min_left)/lineWidth))

bestSize = 0
bestAngle = 0
bestPositions = []
bestPositionsRotated = []

cx = 0
cy = 0

# Used to delimite the calculations of the lines
min_x = sizeX
max_x = 0

clock = pygame.time.Clock()

tsp_coords = []
single_tsp_coords = []
square_coords = []
last_position = 0

basePath = "/Users/h3ct0r/Sites/"

# -------- Main Program Loop -----------
while done == False:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    # Set the screen background
    screen.fill(BLACK)
    color = WHITE

    if(simulationState == 'GENERATE_POLYGON'):
      # Draw all previous selected points
      if(len(clickedPos) > 0):
        for i in xrange(len(clickedPos)):
          pygame.draw.rect(screen, color, [clickedPos[i][0], clickedPos[i][1], 5, 5])

          if(i > 0 and i < len(clickedPos)):
            pygame.draw.line(screen, color, [clickedPos[i-1][0], clickedPos[i-1][1]], [clickedPos[i][0], clickedPos[i][1]])

        # Draw current mouse pos
        lastClicked = clickedPos[-1]
        actualMousePos = pygame.mouse.get_pos()
        pygame.draw.line(screen, color, lastClicked, actualMousePos)

    elif(simulationState == 'CALCULATE_BEST_ANGLE'):

      # Draw the GREEN vertical lines
      x_pos_line = min_left
      for i in xrange(numberOfLines):
        pygame.draw.line(screen, GREEN, [x_pos_line, 0], [x_pos_line, sizeY])
        x_pos_line += lineWidth

      # Draw the polygon
      for i in xrange(len(clickedPos)):
        x1, y1 = clickedPos[i]
        if(i > 0 and i < len(clickedPos)):
          x2, y2 = clickedPos[i-1]
          pygame.draw.line(screen, color, [x2,y2], [x1,y1])

      # Color the lines inside the polygon and get their size
      totalSize = 0
      lineMatchCounter = 0
      temporalPositions = []
      x_pos_line = min_left
      for x in xrange(numberOfLines):
        # Speed-up the process ignoring lines outside the polygon
        #if(lineWidth * x < min_x - (max_x - min_x) or lineWidth * x > max_x + 100):
        #  continue

        start = 0
        end = 0
        for y in xrange(sizeY):
          pixelValue = screen.get_at((x_pos_line, y))
          if(pixelValue != GREEN):
            if(start == 0):
              start = y
            else:
              end = y

        if(start != 0 and end == 0):
          end = start

        if(start != 0 and end != 0):
          lineMatchCounter += 1

        totalSize += end - start

        pygame.draw.line(screen, RED, [x_pos_line, start], [x_pos_line, end])

        if(start != 0 and end != 0):
          temporalPositions.append( (x_pos_line, start) )
          temporalPositions.append( (x_pos_line, end) )

        x_pos_line += lineWidth

      if lineMatchCounter > 0:
        totalSize = totalSize / lineMatchCounter
      else:
        totalSize = 0

      if(totalSize >= bestSize):
        bestSize = totalSize
        bestAngle = lineAngle
        bestPositions = temporalPositions

      simulationState = 'GENERATE_LIST_OF_POINTS'

    elif(simulationState == 'GENERATE_LIST_OF_POINTS'):

      # Rotate the polygon
      for i in xrange(len(bestPositions)):
        point = bestPositions[i]
        x1,y1 = rotate2d(bestAngle * -1, point, (cx,cy))
        bestPositionsRotated.append((x1,y1))

      #print "bestPositionsRotated", bestPositionsRotated
      simulationState = 'SHOW_BEST_POLYGON'

    elif(simulationState == 'SHOW_BEST_POLYGON'):
      # Draw original polygon
      if(len(clickedPos) > 0):
        for i in xrange(len(clickedPos)):
          pygame.draw.rect(screen, color, [clickedPos[i][0], clickedPos[i][1], 5, 5])
          if(i > 0 and i < len(clickedPos)):
            pygame.draw.line(screen, color, [clickedPos[i-1][0], clickedPos[i-1][1]], [clickedPos[i][0], clickedPos[i][1]])

      # Draw generated points
      #for i in xrange(len(bestPositions)):
      #  x1,y1 = bestPositions[i]
      #  pygame.draw.line(screen, BLUE, [x1,y1], [x1,y1])
      #  if(i > 0 and i < len(bestPositions)):
      #    x2,y2 = bestPositions[i-1]
      #    pygame.draw.line(screen, BLUE, [x2,y2], [x1,y1])

      # Draw the rotated polygon
      for i in xrange(len(bestPositionsRotated)):
        x1, y1 = bestPositionsRotated[i]

        # Show the point number on the screen
        labelNumber = monoFont.render(str(i+1), 1, (255,255,0))
        screen.blit(labelNumber, (int(x1), int(y1)-15))

        pygame.draw.rect(screen, BLUE, [int(x1), int(y1), 5, 5])
        if(i > 0 and i < len(bestPositionsRotated)):
          x2,y2 = bestPositionsRotated[i-1]
          pygame.draw.line(screen, BLUE, [x2,y2], [x1,y1])

      simulationState = 'CALCULATE_TSP_SIMPLE'

    elif(simulationState == 'CALCULATE_TSP_SIMPLE'):
        weightMatrix = {}
        isEvenCount = 1
        isNotEvenCount = 0
        for i in xrange(len( bestPositionsRotated )):
          weightMatrix[i] = {}

          isEven = False
          if(i % 2 == 0):
            isEven = True
            if(isEvenCount == 0):
              isEvenCount += 1
            else:
              isEvenCount = 0
          else:
            if(isNotEvenCount == 0):
              isNotEvenCount += 1
            else:
              isNotEvenCount = 0

          for y in xrange(len( bestPositionsRotated )):
            #print "i", i, "y", y
            if(y == i):
              weightMatrix[i][y] = 0
              pass
            elif(isEven):
              if(isEvenCount == 0):
                if(y == i+1 or (y == i-2 and i != 0)):
                  weightMatrix[i][y] = 1
                else:
                  weightMatrix[i][y] = 999
              else:
                if(y == i+2 or (y == i+1 and i != 0)):
                  weightMatrix[i][y] = 1
                else:
                  weightMatrix[i][y] = 999
            else:
              if(isNotEvenCount == 0):
                if(y == i-1 or y == i-2):
                  weightMatrix[i][y] = 1
                else:
                  weightMatrix[i][y] = 999
              else:
                if(y == i+2 or y == i-1):
                  weightMatrix[i][y] = 1
                else:
                  weightMatrix[i][y] = 999

        print "weightMatrix", weightMatrix

        path = shortest_path(weightMatrix, 0, len(bestPositionsRotated) - 2)
        if len(path) != len( bestPositionsRotated):
          path = shortest_path(weightMatrix, 0, len(bestPositionsRotated) - 1)

        print "path", path, len(path)

        tsp_coords = []
        for index in path:
            tsp_coords.append((int(bestPositionsRotated[index][0]), int(bestPositionsRotated[index][1])) )
        pass

        single_tsp_coords = []
        for h in range(len(tsp_coords)):
            x1 = tsp_coords[h][0]
            y1 = tsp_coords[h][1]

            #single_tsp_coords.append((x1, y1))

            if h + 1 < len(tsp_coords):
                x2 = tsp_coords[h + 1][0]
                y2 = tsp_coords[h + 1][1]

                p1 = (x1, y1)
                p2 = (x2, y2)

                p_list = get_line_points(p1, p2, step=20)
                if len(p_list) == 0:
                    p_list.append(p1)
                else:
                    if p_list[0] != p1:
                        p_list.insert(0, p1)
                    if p_list[-1] != p2:
                        p_list.append(p2)

                #print "p1", (x1, y1), "p2", (x2, y2)
                #print "p_list", len(p_list), p_list
                single_tsp_coords += p_list
                #print "single_tsp_coords", single_tsp_coords
            pass

        print "tsp_coords", len(tsp_coords), tsp_coords
        print "single_tsp_coords", len(single_tsp_coords), single_tsp_coords

        simulationState = 'SHOW_TSP'

    elif(simulationState == 'SHOW_TSP'):
      pygame.draw.polygon(screen, GREEN, tsp_coords, 1)
      cost = 0
      for i in xrange(1, len(tsp_coords)):
          d, theta = points_to_vector(tsp_coords[i], tsp_coords[i - 1])
          cost += d

      print "total_cost", cost, "len(tsp_coords)", len(tsp_coords)

      d, theta = points_to_vector(clickedPos[0], clickedPos[1])
      print "hex side:", d
      print "hex area:", ((3 * math.sqrt(3)) / 2) * (d ** 2)

      hex_width = math.ceil(2 * d)
      hex_height = math.ceil(math.sqrt(3) * d)
      print "hex width:", hex_width
      print "hex height:", hex_height

      # http://en.wikipedia.org/wiki/Law_of_cosines
      triangle_base = math.sqrt((d ** 2 + d ** 2) - ((2 * (d * d)) * math.cos(math.radians(120))))
      triangle_base = math.ceil(triangle_base)
      print "base of triangle", triangle_base
      dbase, t = points_to_vector(clickedPos[2], clickedPos[4])
      print "   real base", dbase

      triangle_height = (triangle_base / 2) * math.tan(math.radians(30))
      triangle_height = math.ceil(triangle_height)
      print "height of triangle", triangle_height
      xa = clickedPos[4][1] + (triangle_base / 2)
      dbase2, t = points_to_vector((clickedPos[4][0], xa), clickedPos[3])
      print "   real height", dbase2
      pygame.draw.line(screen, RED, (clickedPos[4][0], xa), clickedPos[3])

      num_vertical_lines = int(((d * 2) / lineWidth) + 1)
      print "num_vertical_lines", num_vertical_lines

      counter = 0
      for pos in tsp_coords:
        label = monoFont.render(str(counter), 1, (255, 255, 0))
        screen.blit(label, pos)
        counter += 1

      pygame.draw.polygon(screen, RED, clickedPos, 1)

      lines_in_1 = math.ceil(triangle_height / lineWidth)
      print "number of partitions inside 1:", lines_in_1

      width_of_2 = hex_width - (2 * triangle_height)
      lines_in_2 = math.ceil(width_of_2 / lineWidth)
      print "Width of 2:", width_of_2
      print "number of partitions inside 2:", lines_in_2

      #hex_width triangle_height

      total_1_2 = hex_width - ((((lines_in_2 - 1) + (lines_in_1 - 1)) + 1) * lineWidth)
      print "hex_width", hex_width, "total_1_2", total_1_2


      lines_in_3 = math.ceil(total_1_2 / lineWidth)
      print "number of partitions inside 3:", lines_in_3

      h = lineWidth

      a_first = (2 * h) / math.tan(math.radians(30))
      a_last = (2 * (h * (lines_in_1 - 1))) / math.tan(math.radians(30))
      first_term = math.ceil(((lines_in_1 - 1) * (a_first + a_last)) / 2)

      second_term = (hex_height * (lines_in_2 - 1))

      print "a ", (total_1_2 - (h * (lines_in_3 - 1)))
      print "b ", total_1_2

      b_first = (2 * (total_1_2 - (h * (lines_in_3 - 1)))) / math.tan(math.radians(30))
      b_last = (2 * total_1_2) / math.tan(math.radians(30))
      third_term = math.ceil( ((lines_in_3) * (b_first + b_last)) / 2)

      total_calculated = first_term + second_term + third_term

      print "first_term", first_term, "second_term", second_term, "third term", third_term

      rest_side = math.sqrt(((b_first/2) ** 2) + ((total_1_2 - (h * (lines_in_3 - 1))) ** 2))

      print "rest_side", rest_side

      hex_lawnmower_perimeter = total_calculated + ((d * 3) - rest_side)

      print "total_calculated", hex_lawnmower_perimeter
      print "total_cost waypoint", cost
      print "size", lineWidth, "with_geometry", hex_lawnmower_perimeter, "via waypoint", cost
      print "-----------------"

      #f_line, t = points_to_vector(tsp_coords[3], tsp_coords[2])
      #print "   real base first line", f_line

      simulationState = 'GENERATE_SQUARE'

    elif(simulationState == 'GENERATE_SQUARE'):

      #centroid
      border_polygon = Polygon(clickedPos)

      #border_polygon.centroid.x
      #border_polygon.centroid.y

      c = (int(border_polygon.centroid.x), int(border_polygon.centroid.y))

      # Distance to the first point
      dx, dy = clickedPos[0][0] - c[0], clickedPos[0][1] - c[1]
      mag = math.sqrt(dx ** 2 + dy ** 2)

      #print "mag:", mag

      pygame.draw.polygon(screen, GREEN, tsp_coords, 1)
      pygame.draw.circle(screen, WHITE, c, 3)

      angle_step = 360 / 4

      square_coords = []
      for i in xrange(4):
          actual_step = (angle_step * i)

          x, y = vector_components((mag * 0.6), actual_step * 3.14/180)
          new_pos = (int(c[0] + x), int(c[1] + y))
          square_coords.append(new_pos)

      simulationState = "DRAW_ALL"
      pass

    elif(simulationState == "DRAW_ALL"):


        pygame.draw.polygon(screen, GREEN, tsp_coords, 1)
        pygame.draw.polygon(screen, RED, square_coords, 1)

        pygame.draw.circle(screen, BLUE, tsp_coords[0], 3)
        pygame.draw.circle(screen, WHITE, tsp_coords[-1], 3)

        counter = 1
        for pos in tsp_coords:
            label = monoFont.render(str(counter), 1, (255,255,0))
            screen.blit(label, pos)
            counter += 1


        pygame.draw.polygon(screen, RED, clickedPos, 1)
        border_polygon = Polygon(clickedPos)
        c = (int(border_polygon.centroid.x), int(border_polygon.centroid.y))
        pygame.draw.circle(screen, WHITE, c, 1)

        """
        counter = 1
        for pos in bestPositionsRotated:
            label = monoFont.render(str(counter), 1, (255,255,0))
            screen.blit(label, pos)
            counter += 1
        """
        done = True

    pygame.draw.rect(screen, BLACK, [0, sizeY - 25, sizeX, 25])
    label = monoFont.render("Best angle: "+str(bestAngle)+" best Size: "+str(bestSize)+" Actualpos :"+str(pygame.mouse.get_pos()), 1, (255,255,0))
    screen.blit(label, (10, sizeY - 25))

    clock.tick()
    pygame.display.set_caption("fps:" + str(clock.get_fps()))

    #clock.tick(100) # Limit to 20 FPS
    pygame.display.flip()

    #pygame.time.delay(10)

#print int(organizedCoordinates[0][0]), int(organizedCoordinates[0][1])

# Print coords to file
f = open("/tmp/hex_coords_calculated.txt", "w")
for pos in tsp_coords:
    line = str(pos[0]) + " " + str(pos[1]) + "\n"
    f.write(line)
f.close()

f = open("/tmp/hex_coords_more_resolution_calculated.txt", "w")
for pos in single_tsp_coords:
    line = str(pos[0]) + " " + str(pos[1]) + "\n"
    f.write(line)
f.close()

f = open("/tmp/square_coords_calculated.txt", "w")
for pos in square_coords:
    line = str(pos[0]) + " " + str(pos[1]) + "\n"
    f.write(line)
f.close()

time.sleep(0)
pygame.quit()