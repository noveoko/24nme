import geopandas as gpd
import random
from shapely.geometry import Point

def generate_land_coordinates():
    # Load the land shapefile
    world = gpd.read_file('ne_110m_land.shp')

    while True:
        # Generate a random coordinate
        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        point = Point(longitude, latitude)

        # Check if the point is within any of the land polygons
        if any(world.contains(point)):
            return (latitude, longitude)
