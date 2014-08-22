from math import (
                  cos, sin, atan2
                  )
import math

def distance(latOne, lonOne, latTwo, lonTwo):
    """
        haversine formula
    """
    R = 6371 # KM
    latOneRadians = math.radians(latOne)
    latTwoRadians = math.radians(latTwo)
    latDistance = math.radians(latTwo-latOne)
    lonDistance = math.radians(lonTwo-lonOne)

    a = math.sin(latDistance/2)**2 + math.cos(latOneRadians) * math.cos(latTwoRadians) * math.sin(lonDistance/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    d = R * c

    return d


print distance(52.5318, 13.3898, 52.52346, 13.35981) # 2.230579904723257

# seattle = [47.621800, -122.350326]
# olympia = [47.041917, -122.893766]
print distance(47.621800, -122.350326, 47.041917, -122.893766)


def bearing(startLat, startLong, endLat, endLong):
    startLat = math.radians(startLat)
    startLong = math.radians(startLong)
    endLat = math.radians(endLat)
    endLong = math.radians(endLong)

    dLong = endLong - startLong

    dPhi = math.log(math.tan(endLat/2.0+math.pi/4.0)/math.tan(startLat/2.0+math.pi/4.0))
    if abs(dLong) > math.pi:
         if dLong > 0.0:
             dLong = -(2.0 * math.pi - dLong)
         else:
             dLong = (2.0 * math.pi + dLong)

    bearing = (math.degrees(math.atan2(dLong, dPhi)) + 360.0) % 360.0;

    return bearing

print bearing(43.682213, -70.450696, 43.682194, -70.450769)
print bearing(0.0,0.0,0.0,0.0)
print bearing(0.0,0.0,0.0,10.0)
print bearing(0.0,0.0,10.0,0.0)
print bearing(0.0,0.0,0.0,-10.0)
print bearing(0.0,0.0,-10.0,0.0)
print bearing(0.0,0.0,-1.0,10.0)
print bearing(53.32055555555556 , -1.7297222222222221, 53.31861111111111, -1.6997222222222223)
print bearing(53.32055555555556 , -1.7297222222222221, 53.31861111111111, -1.6997222222222223)
print bearing(53.32055, -1.72972, 53.31861, -1.69972)


def midPoint(startLat, startLong, endLat, endLong):
    startLat = math.radians(startLat)
    startLong = math.radians(startLong)
    endLat = math.radians(endLat)
    endLong = math.radians(endLong)

    dLon = math.radians(endLong - startLong)


    Bx = math.cos(endLat) * math.cos(dLon)
    By = math.cos(endLat) * math.sin(dLon)
    lat3 = math.atan2(math.sin(startLat) + math.sin(endLat), math.sqrt((math.cos(startLat) + Bx) * (math.cos(startLat) + Bx) + By * By))
    lon3 = startLong + math.atan2(By, math.cos(startLat) + Bx)

    midLat = math.degrees(lat3)
    midLon = math.degrees(lon3)

    return midLat, midLon

print midPoint(43.682213, -70.450696, 43.682194, -70.450769)

"""
    Destination point given distance and bearing from start point
    http://gis.stackexchange.com/questions/76077/how-to-create-points-based-on-the-distance-and-bearing-from-a-survey-point
"""
def destinationPoint(startLat, startLon, brng, distanceTraveled):
    point     = (startLat, startLon)
    distance  = math.radians(distanceTraveled)
    bearing   = math.radians(brng)
    angle     = 90 - bearing
    bearing   = math.radians(bearing)
    angle     = math.radians(angle)

    cosa = math.cos(angle)
    cosb = math.cos(bearing)
    xfinal, yfinal = (point[0] +(distance * cosa), point[1]+(distance * cosb))

    return xfinal, yfinal

print destinationPoint(43.682213, -70.450696, 6, 10)












