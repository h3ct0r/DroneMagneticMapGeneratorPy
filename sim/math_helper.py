from math import sin, cos, sqrt, atan2
import random
from shapely.geometry import *
from shapely import affinity
import heapq
import numpy as np
from scipy.spatial import distance


def get_distance_3d_path(p_list):
    dst = 0
    for i in xrange(len(p_list)):
        d1 = p_list[i]
        if i+1 < len(p_list):
            d2 = p_list[i+1]
            dst += distance.euclidean(d1, d2)
    return dst


def get_3d_coverage_points(p_list, robot_heigth, np_file, np_mat=None):
    if np_mat is None:
        np_mat = np.loadtxt(np_file)
        np_mat *= 255.0/np_mat.max()
    points = []

    x_size = np_mat.shape[1]
    y_size = np_mat.shape[0]

    for p in p_list:
        x = p[0]
        y = p[1]
        if x >= x_size or y >= y_size or x < 0 or y < 0:
            points.append((x, y, robot_heigth))
        else:
            z = np_mat[y][x]
            z_mod = z + robot_heigth
            points.append((x, y, z_mod))
    return points


def get_3d_point(point, robot_heigth, np_file):
    np_mat = np.loadtxt(np_file)
    np_mat *= 255.0/np_mat.max()

    x, y = point
    z = np_mat[y][x]

    return y, x, z + robot_heigth


def generate_json_string_from_list(my_list):
    """
    generate_json_string_from_list
    :param my_list:
    :return:
    """
    point_str = "["
    for x in xrange(len(my_list)):
        point = my_list[x]
        point_str += "[" + str(int(point[0])) + "," + str(int(point[1])) + "]"
        if x < len(my_list) - 1:
            point_str += ","
    point_str += "]"
    return point_str


def shortest_path(graph, start, end):
    """
    shortest_path
    :param graph:
    :param start:
    :param end:
    :return:
    """
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
            for (v2, cost2) in graph[v1].iteritems():
                if v2 not in visited:
                    heapq.heappush(q, (cost + cost2, v2, path))


def dijkstra(graph, src, dest, visited=None, distances=None, predecessors=None):
    """
    calculates a shortest path tree routed in src
    :param graph:
    :param src:
    :param dest:
    :param visited:
    :param distances:
    :param predecessors:
    :return:
    """
    if visited is None:
        visited = []

    if distances is None:
        distances = {}

    if predecessors is None:
        predecessors = {}

    # a few sanity checks
    if src not in graph:
        raise TypeError('the root of the shortest path tree cannot be found in the graph')
    if dest not in graph:
        raise TypeError('the target of the shortest path cannot be found in the graph')
        # ending condition
    if src == dest:
        # We build the shortest path and display it
        path = []
        pred = dest
        while pred is not None:
            path.append(pred)
            pred = predecessors.get(pred, None)
#           print('shortest path: ' + str(path) + " cost=" + str(distances[dest]))
        return path, distances[dest]
    else:
        # if it is the initial  run, initializes the cost
        if not visited:
            distances[src] = 0
        # visit the neighbors
        for neighbor in graph[src]:
            if neighbor not in visited:
                new_distance = distances[src] + graph[src][neighbor]
                if new_distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = src

        # mark as visited
        visited.append(src)
        # now that all neighbors have been visited: recurse
        # select the non visited node with lowest distance 'x'
        # run Dijskstra with src='x'
        unvisited = {}
        for k in graph:
            if k not in visited:
                unvisited[k] = distances.get(k, float('inf'))
        x = min(unvisited, key=unvisited.get)
        path, distances[dest] = dijkstra(graph, x, dest, visited, distances, predecessors)
        return path, distances[dest]


def hex_points(x, y, tetha, radius):
    """
    Given x and y of the origin, return the six points around the origin of RADIUS distance
    :param x:
    :param y:
    :param tetha:
    :param radius:
    :return:
    """
    for i in range(6):
        yield cos(tetha * i) * radius + x, sin(tetha * i) * radius + y


def hex_centres(h_wide, h_high, radius, half_hex_height):
    """
    hex_centres
    :param h_wide:
    :param h_high:
    :param radius:
    :param half_hex_height:
    :return:
    """
    for x in range(h_wide):
        for y in range(h_high):
            yield (x * 3 + 1) * radius + radius * 1.5 * (y % 2), (y + 1) * half_hex_height


def get_random_colour():
    return random.randrange(256), random.randrange(256), random.randrange(256)


def get_hex_point_list(h_wide, h_high, radius, half_hex_height, tetha):
    """
    Return a list of Shapely hex polygons
    :param h_wide:
    :param h_high:
    :param radius:
    :param half_hex_height:
    :param tetha:
    :return:
    """
    poly_list = []

    for x, y in hex_centres(h_wide, h_high, radius, half_hex_height):
        poly_list.append(Polygon(list(hex_points(x, y, tetha, radius))))

    return poly_list


def points_to_vector(p1, p2):
    """
    Convert two points to a vector.
    :param p1:
    :param p2:
    :return: magnitude and angle.
    """
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    mag = sqrt(dx ** 2 + dy ** 2)
    theta = atan2(dy, dx)
    return mag, theta


def is_number(s):
    """
    Return is the element is a number
    :param s:
    :return:
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def generate_cover_poly_with_translation(hex_poly_obj, hex_line_angle_obj, c_center, generated_leaflet_pos):
    """
    generate_cover_poly_with_translation
    :param hex_poly_obj:
    :param hex_line_angle_obj:
    :param c_center:
    :param generated_leaflet_pos:
    :return:
    """
    cx2 = int(hex_poly_obj.centroid.x)
    cy2 = int(hex_poly_obj.centroid.y)

    cover_poly_obj = Polygon(generated_leaflet_pos)
    cover_poly_obj = affinity.translate(cover_poly_obj, cx2 - c_center[0], cy2 - c_center[1])
    cover_poly_obj = affinity.rotate(cover_poly_obj, hex_line_angle_obj)

    return cover_poly_obj

# Jarvis algorithm
TURN_LEFT, TURN_RIGHT, TURN_NONE = (1, -1, 0)


def turn(p, q, r):
    """
    Returns -1, 0, 1 if p,q,r forms a right, straight, or left turn.
    :param p:
    :param q:
    :param r:
    :return:
    """
    return cmp((q[0] - p[0])*(r[1] - p[1]) - (r[0] - p[0])*(q[1] - p[1]), 0)


def _dist(p, q):
    """
    Returns the squared Euclidean distance between p and q.
    :param p:
    :param q:
    :return:
    """
    dx, dy = q[0] - p[0], q[1] - p[1]
    return dx * dx + dy * dy


def _next_hull_pt(points, p):
    """
    Returns the next point on the convex hull in CCW from p.
    :param points:
    :param p:
    :return:
    """
    q = p
    for r in points:
        t = turn(p, q, r)
        if t == TURN_RIGHT or t == TURN_NONE and _dist(p, r) > _dist(p, q):
            q = r
    return q


def convex_hull(points):
    """
    Returns the points on the convex hull of points in CCW order.
    :param points:
    :return:
    """
    hull = [min(points)]
    for p in hull:
        q = _next_hull_pt(points, p)
        if q != hull[0]:
            hull.append(q)
    return hull


def is_number(s):
    """
    Return is the element is a number
    :param s:
    :return:
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_line_points(p1, p2, step=0):
        "Bresenham's line algorithm"

        x0 = int(p1[0])
        y0 = int(p1[1])
        x1 = int(p2[0])
        y1 = int(p2[1])

        points_in_line = []
        count = 0
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1

        if dx > dy:
            err = dx / 2.0
            while x != x1:
                if count >= step:
                    points_in_line.append((x, y))
                    count = 0
                else:
                    count += 1
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                if count >= step:
                    points_in_line.append((x, y))
                    count = 0
                else:
                    count += 1
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        if count >= step:
            points_in_line.append((x, y))
            count = 0
        else:
            count += 1

        return points_in_line
