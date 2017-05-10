__author__ = 'h3ct0r'

import json
import sys
import time
import pylab
import subprocess
import numpy as np
from scipy.cluster.vq import *

import warnings

kmeans_color_array = [
    (0, 0, 1),
    (0, 1, 0),
    (1, 0, 0),
    (0, 1, 1),
    (1, 1, 0),
    (1, 0, 1),
    (1, 0, 1),
    (0, 0, 0),
    (0, 0.5, 0.5),
    (0.5, 1, 0.5)
]


def run_kmeans(xy, cluster_size=2):

    points_per_robot = []

    if len(xy) == 1 or (len(xy) == 2 and cluster_size == 1):
        points_per_robot.append([xy])
        return points_per_robot

    elif len(xy) == 2 and cluster_size == 2:
        points_per_robot.append([xy[0]])
        points_per_robot.append([xy[1]])
        return points_per_robot

    xy = np.asarray(xy)
    data = np.column_stack([xy])
    data = data.astype(np.float32)

    res = []
    labels = []

    # Apply Kmeans with user defined cluster size and run 90 times
    continue_loop_kmeans = True
    while continue_loop_kmeans:
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                print 'data', data, 'cluster_size', cluster_size
                res, labels = kmeans2(data, cluster_size, 90)
                continue_loop_kmeans = False
            except Warning:
                print "Warning.."

    colors = ([kmeans_color_array[i] for i in labels])

    # plot colored points and mark centroids as (X)
    pylab.scatter(xy[:, 0], xy[:, 1], c=colors)
    pylab.scatter(res[:, 0], res[:, 1], marker='o', s=500, linewidths=2, c='none')
    pylab.scatter(res[:, 0], res[:, 1], marker='x', s=500, linewidths=2)
    pylab.savefig('/tmp/kmeans_'+str(time.time())+".png")
    pylab.clf()

    positions = []
    actual_pos = labels[0]
    positions.append(actual_pos)
    for i in labels:
        if actual_pos == i:
            continue
        else:
            if i not in positions:
                actual_pos = i
                positions.append(actual_pos)



    # Iterate the labels result from the kmeans
    for i in range(len(positions)):
        contours = []

        # Generate the contours of every cluster by number
        # Example: label 1, label 2, etc.
        for y in range(len(xy)):
            if labels[y] == i:
                element = xy[y]
                contours.append(element)

        contours = np.asarray(contours)

        clustered_points = []
        for point in contours[:, 0:3]:
            idx = point[0]
            idy = point[1]

            clustered_points.append((idx, idy))

        points_per_robot.append(clustered_points)

    return points_per_robot

if len(sys.argv) < 4:
    print "\nERROR:     Usage: python kmeans_toursplit_textmode.py adjacency_file number_of_robots result_file\n\n"
    exit(1)

json_filepath = sys.argv[1]
number_of_robots = int(sys.argv[2])
response_filepath = sys.argv[3]

if not number_of_robots or number_of_robots <= 0:
    number_of_robots = 1

json_data = open(json_filepath)
adjdata = json.load(json_data)

hex_centroid_list = []

for i in xrange(len(adjdata['distances'].keys())):
    if str(i) == adjdata["start_point"]:
        continue

    hex_point = (adjdata['distances'][str(i)][0], adjdata['distances'][str(i)][1])
    hex_centroid_list.append(hex_point)

print 'hex_centroid_list', hex_centroid_list, 'number_of_robots', number_of_robots

kmeans_result = run_kmeans(hex_centroid_list, number_of_robots)

print "kmeans_result:", kmeans_result

kmeans_to_graph_indexes = []
for cluster_index in xrange(len(kmeans_result)):

    cluster_array = []
    for point in kmeans_result[cluster_index]:
        for key in xrange(len(adjdata['distances'].keys())):
            hex_point = (adjdata['distances'][str(key)][0], adjdata['distances'][str(key)][1])
            if hex_point == point:
                cluster_array.append(key)
                break
        pass
    pass
    kmeans_to_graph_indexes.append(cluster_array)

print "kmeans_to_graph_indexes:", kmeans_to_graph_indexes
print "cluster_array", cluster_array

tsp_cluster_result = []

for cluster_array in kmeans_to_graph_indexes:

    tsp_program = "simple_python"

    if tsp_program == "linkern":
        # Header for Linkern
        f = open("/Users/h3ct0r/Sites/pointListOut.tsp", "w")
        f.write('NAME: %s\n' % "TESTNAME")
        f.write('TYPE: TSP\n')
        f.write('DIMENSION: %d\n' % len(cluster_array))
        f.write('EDGE_WEIGHT_TYPE: EUC_2D\n')
        f.write('NODE_COORD_SECTION\n')
        city_counter = 0
        for city_index in cluster_array:
            f.write('%d %d %d\n' % (city_counter, adjdata['distances'][str(city_index)][0], adjdata['distances'][str(city_index)][1]))
            city_counter += 1
        f.write('EOF:\n')
        f.close()

        solfile = '/Users/h3ct0r/Desktop/concorde/LINKERN/result'
        LINKERN = '/Users/h3ct0r/Desktop/concorde/LINKERN/linkern'
        LINKERN_OPTS = ' -K 1 -q 3 -I 1 -R 1 -r 3 -o %s %s'

        cmd = LINKERN + LINKERN_OPTS % (solfile, "/Users/h3ct0r/Sites/pointListOut.tsp")
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = pipe.communicate()
        status = pipe.wait()

        #print output, error

        if status:
            print 'Solver failed; status = %s\n' % status
            print 'Error:', error
            exit(1)

        organized_coordinates = []
        cost_list = []

        ins = open(solfile, "r")
        next(ins)
        for line in ins:
            node_number = line.split()
            organized_coordinates.append(int(node_number[0]))
            cost_list.append(int(node_number[2]))
        ins.close()

        print "organized coordinates:", organized_coordinates

        new_org_coordinates = []
        for i in organized_coordinates:
            new_org_coordinates.append(cluster_array[i])

        tsp_cluster_result.append(new_org_coordinates)
        print "new org coord:", new_org_coordinates
        print "cost list:", cost_list

    if tsp_program == "simple_python":

        f = open("/tmp/pointListOut.tsp", "w")
        for city_index in cluster_array:
            f.write('%d,%d\n' % (adjdata['distances'][str(city_index)][0], adjdata['distances'][str(city_index)][1]))
        f.close()


        cmd = "python /Users/h3ct0r/PycharmProjects/route_map/sim/tsp.py -n 100000 /tmp/pointListOut.tsp"
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = pipe.communicate()
        status = pipe.wait()

        #print output, error

        if status:
            print 'Solver failed; status = %s\n' % status
            print 'Error:', error
            exit(1)

        organized_coordinates = []
        cost_list = []

        solfile = '/tmp/tsp_result'
        ins = open(solfile, "r")
        next(ins)
        for line in ins:
            node_number = line.split()
            organized_coordinates.append(int(node_number[0]))
        ins.close()

        print "organized coordinates:", organized_coordinates

        new_org_coordinates = []
        for i in organized_coordinates:
            new_org_coordinates.append(cluster_array[i])

        tsp_cluster_result.append(new_org_coordinates)
        print "new org coord:", new_org_coordinates
    pass

begin_num = ord('a')
letters_generated = [chr(i) for i in range(begin_num, begin_num + (number_of_robots + 2))]

f = open(response_filepath, "w")
for route in tsp_cluster_result:
    letter = letters_generated.pop(0)
    f.write(str(letter))
    f.write(" ")
    for i in route:
        f.write(str(i))
        f.write(" ")
f.close()