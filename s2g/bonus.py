#!/usr/env/bin python
# encoding: utf-8
import matplotlib
import numpy as np
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from shapely.geometry import Point, box, Polygon, MultiPoint

__all__ = ['plot_lines', 'great_circle_dist', 'perpend_to_line',
           'bounds_overlay', 'lines_within_box', 'line_distance',
           'line_contains_point', 'lines_touch', 'point_projects_to_line',
           'point_projects_to_points', 'cut_line', 'distance_to_buffer']


def plot_lines(lines, **kwargs):
    def plot_line(ob):
        x, y = ob.xy
        plt.plot(x, y, linewidth=1, solid_capstyle='round', zorder=1, **kwargs)

    for u in lines:
        if u.geom_type in ['LineString', 'LinearRing', 'Point']:
            plot_line(u)
        elif u.geom_type is 'MultiLineString':
            for p in u:
                plot_line(p)


def great_circle_dist(p1, p2):
    """Return the distance (in km) between two points in
    geographical coordinates.
    """
    lon0, lat0 = p1
    lon1, lat1 = p2
    EARTH_R = 6372.8
    lat0 = np.radians(float(lat0))
    lon0 = np.radians(float(lon0))
    lat1 = np.radians(float(lat1))
    lon1 = np.radians(float(lon1))
    dlon = lon0 - lon1
    y = np.sqrt(
        (np.cos(lat1) * np.sin(dlon)) ** 2
        + (np.cos(lat0) * np.sin(lat1)
           - np.sin(lat0) * np.cos(lat1) * np.cos(dlon)) ** 2)
    x = np.sin(lat0) * np.sin(lat1) + \
        np.cos(lat0) * np.cos(lat1) * np.cos(dlon)
    c = np.arctan2(y, x)
    return EARTH_R * c


def distance_to_buffer(distance):
    """
    Convert great circle distance (in small range < 1000km) to
    Euclidean form of point buffer used by shapely.
    :param distance: great circle distance in kilometers
    :return: point shift in Euclidean coordinates.
    """
    magic_num = 1078.599717114 # km
    return distance / magic_num


def perpend_to_line(p1, p2, p3):
    """Return the perpendicular line of a point to a line segment
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    px = x2 - x1
    py = y2 - y1
    sqr = float(px * px + py * py)
    if sqr == 0:
        return x1, y1
    u = ((x3 - x1) * px + (y3 - y1) * py) / sqr
    if u > 1:
        u = 1
    elif u < 0:
        u = 0
    x = x1 + u * px
    y = y1 + u * py
    return x, y


def bounds_overlay(a, b):
    """Checking overlay by bounds (minx, miny, maxx, maxy)
    """
    # for i, j in product([0, 2], [1, 3]):
    #     px, py = (b1[i], b1[j])
    #     if b2[0] <= px <= b2[2] and b2[1] <= py <= b2[3]:
    #         return True
    # return False
    bbox1 = box(a[0], a[1], a[2], a[3])
    bbox2 = box(b[0], b[1], b[2], b[3])
    return bbox1.intersects(bbox2)


def lines_within_box(lines, bounding_box, cut_segment=True):
    """
    Extract the bounded segments from a list of lines
    :param lines: a list of LineString
    :param bounding_box: the bounding coordinates in (minx, miny, maxx, maxy)
           or Polygon instance
    :return: a list of bounded segments
    """
    if isinstance(bounding_box, Polygon):
        bbox = bounding_box
    else:
        bbox = box(bounding_box[0], bounding_box[1],
                   bounding_box[2], bounding_box[3])
    segments = []
    for line in lines:
        if line.intersects(bbox):
            if cut_segment:
                segments.append(line.intersection(bbox))
            else:
                segments.append(line)
    return segments


def line_distance(coords):
    """Return total road distance in kilometers"""
    dist = []
    for i in range(0, len(coords) - 1):
        dist.append(great_circle_dist(coords[i], coords[i + 1]))
    return np.sum(dist)


def line_contains_point(line, point, buf=10e-5):
    p = Point(point).buffer(buf)
    return line.intersects(p)


def lines_touch(one, other, buf=10e-5):
    """Predict the connection of two lines
    """
    a = MultiPoint([one.coords[0], one.coords[-1]]).buffer(buf)
    b = MultiPoint([other.coords[0], other.coords[-1]]).buffer(buf)
    return one.intersects(b) or other.intersects(a)


def point_projects_to_line(point, line):
    """Get the nearest point index on line
    """
    nearest = None
    min_dist = -1
    for i in range(0, len(line.coords)):
        p = line.coords[i]
        # d = great_circle_dist(p, point)
        d = Point(p).distance(Point(point))
        if min_dist < 0:
            min_dist = d
            nearest = i
        else:
            if d < min_dist:
                min_dist = d
                nearest = i
    return nearest


def point_projects_to_points(point, others):
    """Get the nearest point given a group of points
    """
    p = Point(point)
    nearest = None
    min_dist = -1
    for other in others:
        dist = Point(other).distance(p)
        if min_dist < 0:
            min_dist = dist
            nearest = other
        else:
            if dist < min_dist:
                min_dist = dist
                nearest = other
    return nearest


def cut_line(line, resolution=1.0):
    assert line.geom_type == 'LineString'
    coords = line.coords
    sampled_points = [0]
    distances = [0]
    acc_dist = 0
    added = False
    for i in range(1, len(coords)):
        acc_dist += great_circle_dist(coords[i - 1], coords[i])
        if acc_dist >= resolution:
            added = True
            sampled_points.append(i)
            distances.append(acc_dist)
            acc_dist = 0
        else:
            added = False
    if not added:
        sampled_points.append(i)
    distances.append(acc_dist)
    # assert len(sampled_points) >= 2
    return sampled_points, distances


def cut_line_with_context(line):
    """
    A intelligent line cutting algorithm with context info.
    :param line: a LineString instance of shapely
    :return: a tuple of (sampled_points_indices, distances)
    """
    assert line.geom_type == 'LineString'
    pass