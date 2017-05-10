import math

def points_to_vector(p1, p2):
    """
    Convert two points to a vector.
    :param p1:
    :param p2:
    :return: magnitude and angle.
    """
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    mag = math.sqrt(dx ** 2 + dy ** 2)
    theta = math.atan2(dy, dx)
    return mag, theta

def vector_components(mag, theta):
    """
    :param mag:
    :param theta:
    :return: Return x,y components
    """
    # components
    x, y = mag * math.cos(theta), mag * math.sin(theta)
    return x, y

def area(p):
    return 0.5 * abs(sum(x0*y1 - x1*y0
                         for ((x0, y0), (x1, y1)) in segments(p)))

def segments(p):
    return zip(p, p[1:] + [p[0]])

def rotate2d(degrees,point,origin):
    """
    A rotation function that rotates a point around a point
    to rotate around the origin use [0,0]
    """
    x = point[0] - origin[0]
    yorz = point[1] - origin[1]
    newx = (x*math.cos(math.radians(degrees))) - (yorz*math.sin(math.radians(degrees)))
    newyorz = (x*math.sin(math.radians(degrees))) + (yorz*math.cos(math.radians(degrees)))
    newx += origin[0]
    newyorz += origin[1]

    return newx,newyorz


def get_line_points(p1, p2, step=0):
        "Bresenham's line algorithm"

        x0, y0 = p1
        x1, y1 = p2

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
