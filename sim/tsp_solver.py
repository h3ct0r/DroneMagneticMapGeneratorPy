#!/usr/bin/python

import random
import sys
import getopt
from PIL import Image, ImageDraw, ImageFont
from math import sqrt


class TspSolver(object):

    def __init__(self, coords, verbose=False, max_iterations=100, move_operator='reversed_sections', start_temp=None, alpha=None):
        self.out_file_name = None
        self.max_iterations = max_iterations
        self.verbose = verbose

        if move_operator == "swapped_cities":
            self.move_operator = TspSolver.swapped_cities
        else:
            self.move_operator = TspSolver.reversed_sections

        self.run_algorithm = TspSolver.run_hillclimb

        self.start_temp = None
        self.alpha = None
        
        # setup the things tsp specific parts hillclimb needs
        self.init_function = lambda: TspSolver.init_random_tour(len(coords))
        self.matrix = TspSolver.cartesian_matrix(coords)
        self.objective_function = lambda tour: -TspSolver.tour_length(self.matrix, tour)
        
        if self.verbose:
            print 'using move_operator: %s' % move_operator

        pass

    def get_tour(self):
        iterations, score, best = self.run_algorithm(self.init_function, 
            self.move_operator, self.objective_function, self.max_iterations)
        
        if self.verbose:
            print 'iterations:', iterations
            print 'score:', score
            print 'best:', best

        return best

    @staticmethod
    def hillclimb(init_function, move_operator, objective_function, max_evaluations):
        '''
        hillclimb until either max_evaluations is reached or we are at a local optima
        '''
        best = init_function()
        best_score = objective_function(best)

        num_evaluations = 1

        print 'hillclimb started: score=%f', best_score

        while num_evaluations < max_evaluations:
            # examine moves around our current position
            move_made = False
            for next in move_operator(best):
                if num_evaluations >= max_evaluations:
                    break

                # see if this move is better than the current
                next_score = objective_function(next)
                num_evaluations += 1
                if next_score > best_score:
                    best = next
                    best_score = next_score
                    move_made = True
                    break  # depth first search

            if not move_made:
                break  # we couldn't find a better move (must be at a local maximum)

        print 'hillclimb finished: num_evaluations=%d, best_score=%f', num_evaluations, best_score
        return num_evaluations, best_score, best

    @staticmethod
    def hillclimb_and_restart(init_function, move_operator, objective_function, max_evaluations):
        '''
        repeatedly hillclimb until max_evaluations is reached
        '''
        best = None
        best_score = 0

        num_evaluations = 0
        while num_evaluations < max_evaluations:
            remaining_evaluations = max_evaluations - num_evaluations

            print '(re)starting hillclimb %d/%d remaining', remaining_evaluations, max_evaluations
            evaluated, score, found = TspSolver.hillclimb(init_function, move_operator, objective_function, remaining_evaluations)

            num_evaluations += evaluated
            if score > best_score or best is None:
                best_score = score
                best = found

        return num_evaluations, best_score, best

    @staticmethod
    def rand_seq(size):
        '''generates values in random order
        equivalent to using shuffle in random,
        without generating all values at once'''

        values = range(size)
        for i in xrange(size):
            # pick a random index into remaining values
            j = i + int(random.random()*(size-i))
            # swap the values
            values[j],values[i]=values[i],values[j]
            # return the swapped value
            yield values[i] 

    @staticmethod
    def all_pairs(size):
        '''generates all i,j pairs for i,j from 0-size'''

        for i in TspSolver.rand_seq(size):
            for j in TspSolver.rand_seq(size):
                yield (i,j)

    @staticmethod
    def reversed_sections(tour):
        '''generator to return all possible variations where the section between two cities are swapped'''
        for i, j in TspSolver.all_pairs(len(tour)):
            if i != j:
                copy=tour[:]
                if i < j:
                    copy[i:j+1]=reversed(tour[i:j+1])
                else:
                    copy[i+1:]=reversed(tour[:j])
                    copy[:j]=reversed(tour[i+1:])
                if copy != tour: # no point returning the same tour
                    yield copy

    @staticmethod
    def swapped_cities(tour):
        '''generator to create all possible variations where two cities have been swapped'''
        for i,j in TspSolver.all_pairs(len(tour)):
            if i < j:
                copy=tour[:]
                copy[i],copy[j]=tour[j],tour[i]
                yield copy
    
    @staticmethod
    def cartesian_matrix(coords):
        '''create a distance matrix for the city coords that uses straight line distance'''
        matrix={}
        for i,(x1,y1) in enumerate(coords):
            for j,(x2,y2) in enumerate(coords):
                dx,dy=x1-x2,y1-y2
                dist=sqrt(dx*dx + dy*dy)
                matrix[i,j]=dist
        return matrix

    @staticmethod
    def tour_length(matrix,tour):
        '''total up the total length of the tour based on the distance matrix'''
        total=0
        num_cities=len(tour)
        for i in range(num_cities):
            j=(i+1)%num_cities
            city_i=tour[i]
            city_j=tour[j]
            total+=matrix[city_i,city_j]
        return total

    @staticmethod
    def write_tour_to_img(coords,tour,title,img_file):
        padding=20
        # shift all coords in a bit
        coords=[(x+padding,y+padding) for (x,y) in coords]
        maxx,maxy=0,0
        for x,y in coords:
            maxx=max(x,maxx)
            maxy=max(y,maxy)
        maxx+=padding
        maxy+=padding
        img=Image.new("RGB",(int(maxx),int(maxy)),color=(255,255,255))
        
        font=ImageFont.load_default()
        d=ImageDraw.Draw(img);
        num_cities=len(tour)
        for i in range(num_cities):
            j=(i+1)%num_cities
            city_i=tour[i]
            city_j=tour[j]
            x1,y1=coords[city_i]
            x2,y2=coords[city_j]
            d.line((int(x1),int(y1),int(x2),int(y2)),fill=(0,0,0))
            d.text((int(x1)+7,int(y1)-5),str(i),font=font,fill=(32,32,32))
        
        
        for x,y in coords:
            x,y=int(x),int(y)
            d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(196,196,196))
        
        d.text((1,1),title,font=font,fill=(0,0,0))
        
        del d
        img.save(img_file, "PNG")

    @staticmethod
    def init_random_tour(tour_length):
       tour=range(tour_length)
       random.shuffle(tour)
       return tour

    @staticmethod
    def run_hillclimb(init_function, move_operator, objective_function, max_iterations):
        iterations, score, best = TspSolver.hillclimb_and_restart(init_function, move_operator,
                                                                  objective_function, max_iterations)
        return iterations, score, best


if __name__ == "__main__":
    coords = [
        (380, 74), (441, 74), (502, 74), (624, 134), (563, 134), (502, 134), (441, 134), (380, 134), (379, 194), (440, 194), (501, 194), (562, 194), (623, 194), (621, 254), (560, 254), (499, 254), (438, 254), (377, 254), (316, 254), (315, 314), (376, 314), (437, 314), (498, 314), (559, 314), (620, 314), (618, 374), (557, 374), (496, 374), (435, 374), (374, 374), (313, 374), (373, 434), (434, 434), (495, 434), (556, 434), (617, 434), (615, 494), (554, 494), (493, 494), (432, 494), (371, 494), (453, 554), (392, 554)
    ]

    tsp = TspSolver(coords, verbose=True, max_iterations=1000)
    print tsp.get_tour()