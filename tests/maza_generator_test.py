import os
import re
import sys
import csv
import bisect
#import pyexiv2
import argparse
import datetime, calendar
import math

from shapely import affinity
from shapely.geometry import *

import numpy as np
from scipy.spatial import ConvexHull

import pygame

class CoverPolygon(object):
	def __init__(self, vertices, lawnmower_width, angle):
		self.polyObj = Polygon(vertices)
		self.vertices = list(self.polyObj.convex_hull.exterior.coords)

		self.tetha = angle
		self.lawnmower_width = lawnmower_width
		self.lawnmower_path = list(self.calcLawnmower())
		pass

	def getLawnmower(self):
		return self.lawnmower_path

	def getVertices(self):
		return self.vertices

	def calcLawnmower(self):

		rotate_angle = self.tetha - 360		

		rPolyObj = affinity.rotate(self.polyObj, rotate_angle)
		rvertices = list(rPolyObj.exterior.coords)

		# max and min horizontal/vertical values
		maxx = int(max([v[0] for v in rvertices]) + 1)
		minx = int(min([v[0] for v in rvertices]) - 1)
		maxy = int(max([v[1] for v in rvertices]) + 1)
		miny = int(min([v[1] for v in rvertices]) - 1)

		print maxy, miny

		# distance
		d = maxy - miny
		seg_n = int(d / self.lawnmower_width)

		print d, seg_n

		line_pts = [miny + (self.lawnmower_width * (i + 1)) for i in xrange(seg_n)]
		print line_pts
		
		# gen path
		path = []
		i = 0
		while i < seg_n:
			p = [line_pts[i]]
			if i + 1 < seg_n:
				p.append(line_pts[i + 1])
				i += 2
			else:
				i += 1

			for j in xrange(len(p)):
				intersectObj = rPolyObj.intersection(
					LineString([(minx - 10, p[j]), (maxx + 10, p[j])])
					)
				
				if not intersectObj.is_empty:
					inter = list(
						rPolyObj.intersection( 
							LineString([(maxx, p[j]), (minx, p[j])])
							).coords
						)
					if (i + j) % 2 == 0:
						inter.reverse()

					path.extend(inter)

		lawnPath = LineString(path)
		lawnPath = affinity.rotate(lawnPath, rotate_angle * -1)

		# Generate new polygon with the 
		endPoly = Polygon(lawnPath.coords)
		cHull = list(endPoly.convex_hull.exterior.coords)
		endPoly = Polygon(cHull)

		c1 =  list(endPoly.centroid.coords)
		c2 = list(self.polyObj.centroid.coords)
		
		print 'centroid:', c1[0]
		print 'centroid original:', c2[0]
		print 'ex', c2[0][0] - c1[0][0]
		print 'ey', c2[0][1] - c1[0][1]

		lawnPath = affinity.translate(lawnPath, xoff=c2[0][0] - c1[0][0], yoff=c2[0][1] - c1[0][1])

		return list(lawnPath.coords), list(endPoly.convex_hull.exterior.coords)

if __name__ == "__main__":

	angle = 130
	l_width = 30

	p_vert = [(300, 100), (700, 110), (770, 400), (500, 500), (200, 400)]
	#poly = Polygon(p_vert)
	#chull = list(poly.convex_hull.exterior.coords)
	# #print chull
	# min_bbox = minimum_bounding_rectangle(chull)
	# print "min_bbox:", min_bbox

	# dx = min_bbox[0][0] - min_bbox[1][0]
	# dy = min_bbox[0][1] - min_bbox[1][1]
	# rads = math.atan2(-dy,dx)
	# rads %= 2 * math.pi
	# degs = math.degrees(rads)

	# print degs

	# poly_box = Polygon(min_bbox)
	# poly_box = affinity.rotate(poly_box, degs - 360)
	# box_coords = list(poly_box.exterior.coords)
	# print "straight bbox:", box_coords

	
	#print 'Total hexes:', ((800 * 600) / r ** 2) * (2 / (3 * math.sqrt(3) ))

	# Centroids inside square
	# ulp = box_coords[1]
	# lrp = box_coords[3]

	# startx = ulp[0] + 1
	# starty = ulp[1] + 1

	# width = (r * 2)
	# horiz = width * 3/4
	# height = (math.sqrt(3)/2) * width

	# print 'horiz, height', horiz, height
	# #whex = horiz
	# #hhex = (math.sqrt(3) * r)

	# hh = (lrp[0] - ulp[0]) / horiz
	# hv = (lrp[1] - ulp[1]) / (height / 2)
	# hv += 1
	# print 'Hexes Horizontal:', hh, math.ceil(hh), 'vertical:', hv, math.ceil(hv)
	# #print 'whex:', whex, 'hhex:', hhex 

	# print 'start:', startx, starty

	# base_x = startx

	# hex_positions = []
	# for j in xrange(int(math.ceil(hv))):
	# 	if j % 2 != 0:
	# 		base_x = startx + horiz
	# 	else:
	# 		base_x = startx

	# 	for i in xrange(int(hh)):
	# 		x = base_x + ((horiz * 2) * (i))
	# 		y = starty + ((height / 2) * (j))
	# 		hex_positions.append([x, y])

	# print "hex_positions:", len(hex_positions)
	# #print hex_positions
	# draw_points = hex_positions

	# h_list = []
	# for center in hex_positions:
	# 	h = HexagonCover(center, r, l_width)
	# 	h_list.append(h)

	cPoly = CoverPolygon(p_vert, l_width, angle)
	#print h_list

	# h = HexagonCover(c, r, l_width)
	# print 'vertices:', h.getVertices()

	draw_points, dp2 = cPoly.getLawnmower()
	print 'lawnmower:', draw_points

	# DRAWING ROUTINES! ----------- ---------- ------------

	pygame.init()
	screen = pygame.display.set_mode( (800, 600) )
	mono_font = pygame.font.SysFont("monospace", 12)

	is_loop_active = True

	BLACK = (0,   0,   0)
	WHITE = (255, 255, 255)
	GREEN = (0, 255,   0)
	RED = (255,   0,   0)
	BLUE = (0,  60,   255)
	YELLOW = (255, 255,   0)

	while is_loop_active:

	    screen.fill(BLACK)

	    for event in pygame.event.get():
	        if event.type == pygame.QUIT:
	            is_loop_active = False

	    for i in xrange(len(draw_points)):
	        pos_index = draw_points[i]
	        x1 = int(pos_index[0])
	        y1 = int(pos_index[1])

	        if i+1 < len(draw_points):
	            next_index = draw_points[i + 1]
	            x2 = int(next_index[0])
	            y2 = int(next_index[1])

	            pygame.draw.line(screen, WHITE, [x2, y2], [x1, y1], 3)
	        pygame.draw.circle(screen, WHITE, [x1, y1], 2)
		
		pygame.draw.polygon(screen, YELLOW, cPoly.getVertices(), 2)
		pygame.draw.polygon(screen, BLUE, dp2, 2)
		


	    
	    pygame.display.flip()
