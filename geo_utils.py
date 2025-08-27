# geo_utils.py - Geographic utility functions

import math
from typing import Tuple

def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    """Convert lat/lon to tile numbers"""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def num2deg(xtile: int, ytile: int, zoom: int) -> Tuple[float, float]:
    """Convert tile numbers to lat/lon of the top-left corner"""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def get_parent_tile(x: int, y: int, zoom: int) -> Tuple[int, int, int, Tuple[int, int]]:
    """
    Calculates the parent tile coordinates and the quadrant of the child.
    Returns (parent_x, parent_y, parent_zoom, (quadrant_x, quadrant_y)).
    Quadrant is (0,0) for top-left, (1,0) for top-right, etc.
    """
    parent_x = x // 2
    parent_y = y // 2
    parent_zoom = zoom - 1
    quadrant_x = x % 2
    quadrant_y = y % 2
    return (parent_x, parent_y, parent_zoom, (quadrant_x, quadrant_y))
