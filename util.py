import sys
import unittest
import math


def rotate_pt_around_yz_axes(x, y, z, aof, attack_az):
    """
    :param x: X coordinate of point
    :param y: Y coordinate of point
    :param z: Z coordinate of point
    :param aof: angle of fall (rotation around Y axis)
    :param attack_az: attack azimuth angle (rotation around Z axis)
    :return: sx, sy, sz  (rotated X, Y, Z coordinates)
    """
    s_psi = math.sin(math.radians(aof))
    c_psi = math.cos(math.radians(aof))
    s_phi = math.sin(math.radians(attack_az))
    c_phi = math.cos(math.radians(attack_az))
    # Y axis rotation
    x2 = z * s_psi + x * c_psi
    y2 = y
    z2 = z * c_psi - x * s_psi
    # Z axis rotation
    sx = x2 * c_phi - y2 * s_phi
    sy = x2 * s_phi + y2 * c_phi
    sz = z2
    return sx, sy, sz


def apply_list_offset(lst, offset):
    """
    :param lst: list of values
    :param offset: value to be added to the list
    :return: new list with offset applied
    """
    return [i + offset for i in lst]


def apply_surfaces_offset(surfaces, offset):
    """
    :param offset: (X, Y, Z) offset
    :param surfaces: list of 4 (X, Y, Z) points for a quadrilateral
    :return: new list of surfaces with offset applied
    """
    ox, oy, oz = offset
    return [[[x1 + ox, y1 + oy, z1 + oz],
             [x2 + ox, y2 + oy, z2 + oz],
             [x3 + ox, y3 + oy, z3 + oz],
             [x4 + ox, y4 + oy, z4 + oz]] for ((x1, y1, z1), (x2, y2, z2), (x3, y3, z3), (x4, y4, z4)) in surfaces]


def measure_between(vec):
    """
    :param vec: list of N coordinates
    :return: list of N-1 distances between all pairwise N coordinates
    """
    return [abs(vec[i + 1] - vec[i]) for i in range(len(vec) - 1)]


def midpoints(vec):
    """
    :param vec: list of N coordinates
    :return: list of N-1 points that represent the midpoint between all pairwise N coordinates
    """
    return [vec[i] + abs(vec[i+1] - vec[i]) / 2.0 for i in range(len(vec)-1)]


def geometric_center(surfaces):
    """
    :param surfaces: list of (X, Y, Z) points for a quadrilateral
    :return: X, Y, Z geometric center of all surfaces
    """
    min_x, min_y, min_z = sys.maxint, sys.maxint, sys.maxint
    max_x, max_y, max_z = -sys.maxint, -sys.maxint, -sys.maxint
    for x, y, z in surfaces:
        max_x = max(x, max_x)
        min_x = min(x, min_x)
        max_y = max(y, max_y)
        min_y = min(y, min_y)
        max_z = max(z, max_z)
        min_z = min(z, min_z)
    return (max_x - min_x) / 2.0, (max_y - min_y) / 2.0, (max_z - min_z) / 2.0


class TestUtil(unittest.TestCase):
    def test_midpoints(self):
        vec = [-113.54, -75.70, -37.85, 0.00, 37.84]
        testlist = [-94.62, -56.775, -18.925, 18.92]
        midpts = midpoints(vec)
        self.assertEqual(len(midpts), len(testlist))
        for i, _ in enumerate(midpts):
            self.assertAlmostEquals(midpts[i], testlist[i])

    def test_geometric_center(self):
        surfaces = [[[-2, 5, 5], [-2, 0, 5], [-2, 0, 0], [-2, 5, 0]], [[2, -5, -5], [2, 0, -5], [2, 0, 0], [2, -5, 0]]]
        x, y, z = geometric_center(surfaces)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 0)
        self.assertAlmostEqual(z, 0)

    def test_list_offset(self):
        values = [-20, -10, 0, 10, 20]
        new_gridlines = apply_list_offset(values, 5)
        self.assertEqual(new_gridlines, [-15, -5, 5, 15, 25])

    def test_surfaces_offset(self):
        srf = [[[1, 2, 3], [11, 22, 33], [-1, -2, 4], [0, 0, -7]], [[4, 5, 6], [2, 3, 4], [-11, -22, -33], [0, 0, 1]]]
        new_srf = apply_surfaces_offset(srf, (1, -1, -2))
        self.assertEqual(new_srf[0][0], [2, 1, 1])
        self.assertEqual(new_srf[0][1], [12, 21, 31])
        self.assertEqual(new_srf[0][2], [0, -3, 2])
        self.assertEqual(new_srf[0][3], [1, -1, -9])
