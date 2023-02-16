from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
import sys, os
import requests as req
import math
from typing import Tuple
from shapely.geometry import Point, LineString
from shapely.wkt import loads
# from QuerySpeedDataFromHeremaps import speedLimit

api_key = ''
LINEARID = []
FULLNAME = []
RTTYP = []
MTFCC = []
ROADFUNCTIONALCLASS = []
SPEEDLIMITFROMREFSPEED = []
SPEEDLIMITTOREFSPEED = []
geometry = []


#read Tiger file for Nebraska
cities = gpd.read_file("/Users/kgyamfi/Downloads/NebraskaTigerFiles/compiled.shp")


# Extract start and end coordinates of each linestring
first_coord = cities["geometry"].apply(lambda g: g.coords[0])
last_coord = cities["geometry"].apply(lambda g: g.coords[-1])

# Add start and end as columns to the gdf
cities["start_coord"] = first_coord
cities["end_coord"] = last_coord


#switch the positions of start and end cordinates
cities["road_start_lat"] = [sub[1] for sub in cities.start_coord]
cities["road_start_long"] = [sub[0] for sub in cities.start_coord]
cities["road_end_lat"] = [sub[1] for sub in cities.end_coord]
cities["road_end_long"] = [sub[0] for sub in cities.end_coord]

#see the dataframe
cities.head()

# Python program to check if all
# elements in a List are same
res = False
def chkList(lst):
    if len(lst) < 0 :
        res = True
    res = lst.count(lst[0]) == len(lst)

    if(res):
        return(True)
    else:
        return(False)
    

def all_equal(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)



# segmenting linestring with specified distances


def cut(line, distance):
    # Cuts a line in two at a distance from its starting point
    # This is taken from shapely manual

#     distance = distance * line.length
    if distance <= 0.0 or distance >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

def split_line_with_points(line, distance, speedFromred,speedTored,funcClass, startEndCordinates):
    
    if all_equal(startEndCordinates):
#         print('start and end coordinates are same')
        return([line],[speedFromred[0]],[speedTored[0]],[funcClass[0]])
    else:
        #Check if speed limits are the same return roadsegment without split
        if chkList(speedFromred) and chkList(speedTored):
            return([line],[speedFromred[0]],[speedTored[0]],[funcClass[0]])
        else:
            segments = []
            remainingLength = []
            for p in distance:
                if pd.isna(p):
                    segments.append(segments[-1])
                else:
                    if len(segments) == 0:
                        d = line.project(p)
                        seg = cut(line,d)

                        segments.append(seg[0])
                        remainingLength.append(seg[-1])
                    else:
                        d = ((remainingLength[-1])).project(p)
                        seg = cut((remainingLength[-1]),d)
                        segments.append(seg[0])
                        remainingLength.append(seg[-1])
            return segments,speedFromred,speedTored,funcClass
        

# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__

#Query SpeedLimit from Heremaps RouteMacting Api
def speedLimit(start: Tuple[str,str], end: Tuple[str,str]):
  roadFunctionalClass = []
  endPoints = []
  distanceProp = []
  speedLimitFromRefSpeed = []
  speedLimitTorefSpeed = []
  startLat = start[0]
  startLong = start[1]
  endLat = end[0]
  endLong = end[1]
  wayPoint0 = f"{startLat},{startLong}"
  wayPoint1 = f"{endLat},{endLong}"
  
  try:
      resp = req.get(f"https://routematching.hereapi.com/v8/match/routelinks?apikey={api_key}&waypoint0={wayPoint0}8&waypoint1={wayPoint1}&mode=car&routeMatch=1&attributes=SPEED_LIMITS_FCn(*)",timeout=(10,200))
      data = resp.json()
#       print(data)
      roadSegmentNumber =  len(data['response']['route'][0]["leg"][0]["link"])
      startEndCordinates = [(startLat,startLong),(endLat,endLong)]
  except KeyError:
    speedLimitFromRefSpeed=[]
    speedLimitTorefSpeed=[]
    endPoints=[]
    roadFunctionalClass = []
    startEndCordinates = []
    return(speedLimitFromRefSpeed, speedLimitTorefSpeed, endPoints,roadFunctionalClass,startEndCordinates)

  for i in range(roadSegmentNumber):
        
        try:
            PostedspeedLimitFromRefSpeed = math.ceil(int(data['response']['route'][0]["leg"][0]["link"][i]["attributes"]["SPEED_LIMITS_FCN"][0]["FROM_REF_SPEED_LIMIT"]) / 1.609)
            speedLimitFromRefSpeed.append(PostedspeedLimitFromRefSpeed)
        except KeyError:
            PostedspeedLimitFromRefSpeed = np.nan
            speedLimitFromRefSpeed.append(PostedspeedLimitFromRefSpeed)
            
        try:
            PostedspeedLimitTorefSpeed = math.ceil(int(data['response']['route'][0]["leg"][0]["link"][i]["attributes"]["SPEED_LIMITS_FCN"][0]["TO_REF_SPEED_LIMIT"]) / 1.609)
            speedLimitTorefSpeed.append(PostedspeedLimitTorefSpeed)

        except KeyError:
            PostedspeedLimitTorefSpeed = np.nan
            speedLimitTorefSpeed.append(PostedspeedLimitTorefSpeed)
 
        try:
            points = (data['response']['route'][0]["leg"][0]["link"][i]["shape"][-2:])
            changeLatLong = Point(points[-1],points[0])
            endPoints.append(changeLatLong)
        except KeyError:
            changeLatLong = Point(np.nan,np.nan)
            endPoints.append(changeLatLong)
            
        try:
            functionalClass = data['response']['route'][0]["leg"][0]["link"][i]["functionalClass"]
            roadFunctionalClass.append(functionalClass)
        except KeyError:
            functionalClass = np.nan
            roadFunctionalClass.append(functionalClass)

  return(speedLimitFromRefSpeed, speedLimitTorefSpeed, endPoints,roadFunctionalClass,startEndCordinates)
        


# Final Code for finding speed limit for each road segment and appending to lists
def speedLimitForRoadSegments(geoDataFrame):
    
    
    
    for row in geoDataFrame.itertuples():
        print(row)
        speedLimitfromrefSpeed,speedLimitTorefSpeed,endPoints,funcClass,startEndCordinates = speedLimit((row[6][0],row[6][1]),(row[7][0],row[7][1]))
        
        if len(endPoints) == 0:     
            LINEARID.extend([row[1]])
            FULLNAME.extend([row[2]])
            RTTYP.extend([row[3]])
            MTFCC.extend([row[4]])
            ROADFUNCTIONALCLASS.extend([np.nan])
            SPEEDLIMITFROMREFSPEED.extend([np.nan])
            SPEEDLIMITTOREFSPEED.extend([np.nan])
            geometry.extend([row[5]])
        elif len(speedLimitTorefSpeed) == 0 and len(speedLimitTorefSpeed) == 0:
            letSegmentedline,speedLimitfromrefSpeed,speedLimitTorefSpeed,funcClass = split_line_with_points(row[5],endPoints,speedLimitfromrefSpeed,speedLimitTorefSpeed,funcClass,startEndCordinates)
            numberOfSegments = len(endPoints)
            LINEARID.extend([row[1]] * numberOfSegments)
            FULLNAME.extend([row[2]] * numberOfSegments)
            RTTYP.extend([row[3]] * numberOfSegments)
            MTFCC.extend([row[4]] * numberOfSegments)
            ROADFUNCTIONALCLASS.extend(funcClass)
            SPEEDLIMITFROMREFSPEED.extend([np.nan] * numberOfSegments)
            SPEEDLIMITTOREFSPEED.extend([np.nan] * numberOfSegments)
            geometry.extend(letSegmentedline)
        else:
            letSegmentedline,speedLimitfromrefSpeed,speedLimitTorefSpeed,funcClass = split_line_with_points(row[5],endPoints,speedLimitfromrefSpeed,speedLimitTorefSpeed,funcClass,startEndCordinates)
            numberOfSegments = len(letSegmentedline)
            LINEARID.extend([row[1]] * numberOfSegments)
            FULLNAME.extend([row[2]] * numberOfSegments)
            RTTYP.extend([row[3]] * numberOfSegments)
            MTFCC.extend([row[4]] * numberOfSegments)
            ROADFUNCTIONALCLASS.extend(funcClass)
            SPEEDLIMITFROMREFSPEED.extend(speedLimitfromrefSpeed)
            SPEEDLIMITTOREFSPEED.extend(speedLimitTorefSpeed)
            geometry.extend(letSegmentedline)
        print(len(LINEARID),len(FULLNAME),len(RTTYP),len(MTFCC),len(SPEEDLIMITFROMREFSPEED),len(SPEEDLIMITTOREFSPEED),len(geometry))


#Call to start whole process
speedLimitForRoadSegments(cities)

#convert lists to dataframe
df = pd.DataFrame(
    {'LINEARID': LINEARID,
     'FULLNAME': FULLNAME,
     'RTTYP': RTTYP,
     'MTFCC': MTFCC,
     'RDFUNCLASS': ROADFUNCTIONALCLASS,
     'S_LMT_F_RF': SPEEDLIMITFROMREFSPEED,
     'S_LMT_T_RF': SPEEDLIMITTOREFSPEED,
     'geometry': geometry
    })

#convert the dataframe to geodataframe
df['LINEARID'] = df['LINEARID'].astype(object)
df['FULLNAME'] = df['FULLNAME'].astype(object)
df['RTTYP'] = df['RTTYP'].astype(object)
df['MTFCC'] = df['MTFCC'].astype(object)
df['RDFUNCLASS'] = df['RDFUNCLASS'].astype(object)
df['S_LMT_F_RF'] = df['S_LMT_F_RF'].astype(object)
df['S_LMT_T_RF'] = df['S_LMT_T_RF'].astype(object)

gdf = gpd.GeoDataFrame(df,geometry = 'geometry')
gdf.crs = 'EPSG:4269'

gdf.to_file('/Users/kgyamfi/Desktop/test/geodataframeshp')