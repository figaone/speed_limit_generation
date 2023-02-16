import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import geopandas
from shapely import wkt
from shapely.geometry import Polygon, LineString, Point
import mapclassify
import fiona as fiona
import tsfresh
from tsfresh import select_features
from tsfresh.utilities.dataframe_functions import impute
from tsfresh.feature_extraction import ComprehensiveFCParameters
from tsfresh.feature_extraction import extract_features
import folium
from folium.plugins import MarkerCluster
import overpy
import itertools
from operator import itemgetter
from scipy.spatial import cKDTree
from shapely.geometry import Point, LineString



import glob
import os

combined = gpd.read_file('/Users/kgyamfi/Desktop/Python/Intrans Works/speedLimits/shapefiles/Nebraska/Nebraska_Interstate_highways/TRANS_SpeedLimits_DOT.shp')
tigerRoadgdf3 = gpd.read_file('/Users/kgyamfi/Desktop/Python/Intrans Works/speedLimits/shapefiles/Nebraska/Nebraska_Interstate_highways/TRANS_SpeedLimits_DOT.shp')

# setting the path for joining multiple files
files = os.path.join("/Users/kgyamfi/Downloads/KOJO_DATASET", "*.csv")

# list of merged files returned
files = glob.glob(files)
print("Resultant CSV after joining all CSV files at a particular location...")
for f in files:
    print(os.path.basename(f))
    print('-------------------')
    #Convert time to datetime
    dfDrive1 = pd.read_csv(f"{f}")
    dfDrive1.dropna(subset=["gps_long", "gps_lat"], how="any", inplace=True)
    dfDrive1.reset_index()
    #convert black box data frame to geodataframe
    drive1gdf = geopandas.GeoDataFrame(dfDrive1,geometry=geopandas.points_from_xy(dfDrive1.gps_long, dfDrive1.gps_lat))
    drive1gdf = drive1gdf.set_crs('EPSG:4269')
    
    #Find speed limit for first data using omaha
    blackBoxData_w_tigerRoaddf_data = geopandas.sjoin_nearest(drive1gdf,combined,max_distance=0.0002 ,distance_col="distances")
    blackBoxData_w_tigerRoaddf_data_dupes = blackBoxData_w_tigerRoaddf_data.reset_index().drop_duplicates(subset='index', keep='first').set_index('index')
    #Find the remaning points without speed limit
    index_list = blackBoxData_w_tigerRoaddf_data_dupes.index.tolist()
    new_df = drive1gdf[~drive1gdf.index.isin(index_list)]
    
    #Use the remaining for speed limit using heremaps
    new_df_w_tigerRoaddf_data = geopandas.sjoin_nearest(new_df,tigerRoadgdf3,max_distance=0.0002 ,distance_col="distances")
    new_df_w_tigerRoaddf_data_dupes = new_df_w_tigerRoaddf_data.reset_index().drop_duplicates(subset='index', keep='first').set_index('index')
    #Merge the two data points
    df_final1 = pd.concat([blackBoxData_w_tigerRoaddf_data_dupes,new_df_w_tigerRoaddf_data_dupes])
    df_final1_dupes = df_final1.reset_index().drop_duplicates(subset='index', keep='first').set_index('index')
    df1 = pd.DataFrame(df_final1_dupes.drop(columns='geometry'))
    df1['LINEARID'] = df1.LINEARID.astype('str')
    df1.to_csv(f'/Users/kgyamfi/Downloads/KOJO_DATASET/Processed_With_Speed_limit/{os.path.basename(f)}')