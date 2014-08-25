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

"""
    Destination point given distance and bearing from start point
    http://gis.stackexchange.com/questions/76077/how-to-create-points-based-on-the-distance-and-bearing-from-a-survey-point
    http://www.mathsteacher.com.au/year7/ch08_angles/07_bear/bearing.htm
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
