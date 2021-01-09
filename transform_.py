import math
from pygeotile.tile import Tile


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)[::-1]


def calculate_corners(coordinates):
    lt = max([i[0] for i in x[0]])
    lb = min([i[0] for i in x[0]])
    rt = max([i[1] for i in x[0]])
    rb = min([i[1] for i in x[0]])
    return lt, lb, rt, rb


def calculated2tiles(lt, lb, rt, rb, zoom):
    lefttop = (lt, rt)
    rightbottom = (lb, rb)
    return deg2num(*lefttop[::-1], zoom), deg2num(*rightbottom[::-1], zoom)


def tile_range(lt, lb, rt, rb, zoom):
    lefttop = (lt, rt)
    rightbottom = (lb, rb)
    lefttop = Tile.for_latitude_longitude(*lefttop[::-1], zoom)
    rightbottom = Tile.for_latitude_longitude(*rightbottom[::-1], zoom)
    return lefttop, rightbottom
