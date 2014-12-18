import math

def generateQK(qk, level):
    if level == 0:
        yield qk
    else:
        for i in range(0, 4): # QuadKey
            backUp = qk
            qk = qk + str(i)
            for g in generateQK(qk, level -1):
                yield g
            qk = backUp

def getNext(ov):
    l = len(ov)-1
    i = 1
    while l >= 0 and i !=0:
        ov[l] = ((ov[l]+1) % 4) # Odometer resets after reaching 3 to 0
        if ov[l] == 0:
            i = 1
        else:
            i = 0
        l = l - 1

    if i != 0 and l < 0:
        return False
    return True

def generateQuadKeys(width):
    ov = [0 for i in range(width)]
    om = [4 for i in range(width)] #max limit for each value on the Odometer

    while True:
        yield "".join(str(i) for i in ov)
        if getNext(ov) == False:
            break




EarthRadius = 6378137
MinLatitude = -85.05112878
MaxLatitude = 85.05112878
MinLongitude = -180
MaxLongitude = 180


import numpy

def clip(num, min_value, max_value):
    """num - the number to clip
       min_value - minimum allowable value
       max_value - maximum allowable value
    """
    return numpy.minimum(numpy.maximum(num, min_value), max_value)


def map_size(level_of_detail):
    """determines the map width and height (in pixels) at a specified level of detail
       level_of_detail, from 1 (lowest detail) to 23 (highest detail)
       returns map height and width in pixels
    """
    return float(256 << level_of_detail)

def pixel_xy_to_lat_lng(x, y, level_of_detail):
    """converts a pixel x,y coordinates at a specified level of detail into
       latitude,longitude WGS-84 coordinates (in decimal degrees)
       x - coordinate of point in pixels
       y - coordinate of point in pixels
       level_of_detail, from 1 (lowest detail) to 23 (highest detail)
    """
    m_size = map_size(level_of_detail)

    x = (clip(x, 0, m_size - 1) / m_size) - .5
    y = .5 - (clip(y, 0, m_size - 1) / m_size)

    lat = 90. - 360. * numpy.arctan(numpy.exp(-y * 2 * numpy.pi)) / numpy.pi
    lng = 360. * x
    return lat, lng

def QuadKeyToTileXY(quadKey):
    tileX, tileY = 0, 0
    levelOfDetail = len(quadKey)

    i = levelOfDetail
    while i > 0:
        mask = 1 << (i - 1)
        if '0' == quadKey[levelOfDetail - i]:
            pass
        elif '1' == quadKey[levelOfDetail - i]:
            tileX |= mask
        elif '2' == quadKey[levelOfDetail - i]:
            tileY |= mask
        elif '3' == quadKey[levelOfDetail - i]:
            tileX |= mask
            tileY |= mask
        else:
            print "Invalid quad key !!!"

        i = i - 1

    return (levelOfDetail, tileX, tileY)


def fromPointToLatLng(x, y):
    pixelsPerLonDegree = float(256.0 / 360.0)
    pixelsPerLonRadian = float(256.0 / (2.0 * math.pi))

    ox, oy = 256/2, 256 / 2

    lng = (x - ox) / pixelsPerLonDegree
    latRadians = (y - oy) / -pixelsPerLonRadian
    lat = math.degrees(2 * math.atan(math.exp(latRadians)) - math.pi / 2)

    return lat, lng


def getBoundaries(x, y, z):

    lat1, lon1 = fromPointToLatLng(x*256/ math.pow(2, z), (y+1)*256/ math.pow(2, z))
    lat2, lon2 = fromPointToLatLng((x+1)*256/ math.pow(2, z), y*256/ math.pow(2, z))

    return lon1, lat1, lon2, lat2


def xyzToLatLongDegree(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)

  (tl, tr, bl, br) = getBoundaries(x, y, z)


  return (lat_deg, lon_deg, tl, tr, bl, br)



for width in range(0, 9):
    f = open("quadkeys_8.txt"%(width), "w")
    g2 = generateQuadKeys(width)
    for q in g2:
        #line = q + "\n"
        #f.write(line)
        (z, x, y) = QuadKeyToTileXY(q)
        (lat, lon, tl, tr, bl, br) = xyzToLatLongDegree(x, y, z)
        line = "%s (%d %d %d) %f %f [%f %f %f %f]\n" %(q, z, x, y, lat, lon, tl, tr, bl, br)
        f.write(line)

"""

for width in range(8, 14):
    f = open("quadkeys_%d.txt"%(width), "w")
    g2 = generateQuadKeys(width)
    for q in g2:
        #line = q + "\n"
        #f.write(line)
        (z, x, y) = QuadKeyToTileXY(q)
        (lat, lon, tl, tr, bl, br) = xyzToLatLongDegree(x, y, z)
        line = "%s (%d %d %d) %f %f [%f %f %f %f]\n" %(q, z, x, y, lat, lon, tl, tr, bl, br)
        f.write(line)
    references:
    http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/
    http://instaar.colorado.edu/~wickert/grass/googleearth/gdal2tiles.py
    http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    https://developers.google.com/maps/documentation/javascript/examples/map-coordinates
    http://msdn.microsoft.com/en-us/library/bb259689.aspx
"""