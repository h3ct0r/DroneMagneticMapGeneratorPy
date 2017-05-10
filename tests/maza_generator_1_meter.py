import os
import re
import sys
import csv
import bisect
#import pyexiv2
import argparse
import datetime, calendar
import math
from scipy.spatial import distance
import networkx as nx
import matplotlib.pyplot as plt

from shapely import affinity
from shapely.geometry import *

import numpy as np
from scipy.spatial import ConvexHull

import pygame

import sim.math_helper
import sim.tsp_solver

class CoverPolygon(object):
	def __init__(self, vertices, lawnmower_width, angle, meter_pixel_ratio=1.0):
		self.polyObj = Polygon(vertices)
		self.vertices = list(self.polyObj.convex_hull.exterior.coords)

		self.tetha = angle
		self.meter_pixel_ratio = meter_pixel_ratio
		self.lawnmower_width = lawnmower_width * meter_pixel_ratio
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

					inter = sim.math_helper.get_line_points(inter[0], inter[1], self.lawnmower_width)

					#if self.lawnmower_width / self.meter_pixel_ratio <= 4:

					if (i + j) % 2 == 0:
						inter.reverse()

					# Uncomment for greedy WP visit jump
					# print '----- ----- ----- -----'
					# if len(inter) > 2:
					# 	tmp = list(inter)
					# 	inter = []
					# 	for x in xrange(0, len(tmp), 2):
					# 		print 'Val:', x
					# 		if x == 0:
					# 			print 'a', x
					# 			inter.append(tmp[x])
					# 		elif x == 2:
					# 			print 'b', x
					# 			inter.append(tmp[x])
					# 			print 'b', x - 1
					# 			inter.append(tmp[x - 1])	
					# 		else:
					# 			print 'c', x - 1
					# 			inter.append(tmp[x - 1])
					# 			print 'c', x
					# 			inter.append(tmp[x])
					# print '----- ----- ----- -----'


					path.extend(inter)

		print 'path:', path

		neighbors = []
		for i in xrange(len(path)):
			for j in xrange(len(path)):
				if i == j:
					continue

				p1 = path[i]
				p2 = path[j]
				d = distance.euclidean(p1, p2)
				if d < self.lawnmower_width + (self.lawnmower_width * 0.5):
					neighbors.append((i, j))

		print 'neighbors:', neighbors

		G = nx.Graph()
		G.add_edges_from(neighbors)
		g_elements = nx.coloring.greedy_color(G, strategy=nx.coloring.strategy_saturation_largest_first)
		label_list = list(set(g_elements.values()));
		print 'label_list:', label_list
		elem_label = {}

		for i in xrange(len(g_elements)):
			label = g_elements[i]
			if label not in elem_label:
				elem_label[label] = []

			elem_label[label].append(i)
		pos = nx.spring_layout(G)
		color_list = ['red', 'blue', 'yellow', 'green', 'black', 'brown', 'pink']

		for k in elem_label.keys():
			nx.draw_networkx_nodes(G, pos, nodelist=elem_label[k], node_color=color_list.pop(0))

		nx.draw_networkx_edges(G,pos, neighbors, width=1)
		plt.show()

		sparced_path = []
		is_every_label_sparced = False
		while not is_every_label_sparced:
			print 'Generating...'

			for k in elem_label.keys():
				coords = [path[i] for i in elem_label[k]]
				solver = sim.tsp_solver.TspSolver(coords)
				tour = [coords[i] for i in solver.get_tour()]

				if len(sparced_path) > 0:
					p = sparced_path[-1]
					counter = 0
					while distance.euclidean(p, tour[0]) < self.lawnmower_width + (self.lawnmower_width * 0.5) \
							and counter < 3:
						tour = [coords[i] for i in solver.get_tour()]
						counter += 1

					if counter >= 3:
						print 'Repeat sparced path generation...'
						sparced_path = []
						break

					tour = [coords[i] for i in solver.get_tour()]

				sparced_path += tour
			is_every_label_sparced = True

		lawnPath = LineString(sparced_path)
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

	angle = 90
	l_width = 20

	p_vert = [(300, 100), (700, 110), (770, 400), (500, 500), (200, 400)]

	#path =  [
	#(300, 100), (300, 130), (300, 160), 
	#(330, 160),  (330, 130),  (330, 100), 
	#(360, 100), (360, 130), (360, 160), 
	#(390, 160), (390, 130),  (390, 100)
	#]

	cPoly = CoverPolygon(p_vert, l_width, angle, meter_pixel_ratio=3)

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

	    pygame.draw.polygon(screen, YELLOW, cPoly.getVertices(), 2)

	    for i in xrange(len(draw_points)):
	        pos_index = draw_points[i]
	        x1 = int(pos_index[0])
	        y1 = int(pos_index[1])

	        if i+1 < len(draw_points):
	            next_index = draw_points[i + 1]
	            x2 = int(next_index[0])
	            y2 = int(next_index[1])

	            pygame.draw.line(screen, WHITE, [x2, y2], [x1, y1], 1)
	        
	    for i in xrange(len(draw_points)):
			pos_index = draw_points[i]
			x1 = int(pos_index[0])
			y1 = int(pos_index[1])
			label = mono_font.render(str(i), 1, YELLOW)
			screen.blit(label, (x1 + 10, y1))
			pygame.draw.circle(screen, BLUE, [x1, y1], 4)
	    
	    pygame.display.flip()
