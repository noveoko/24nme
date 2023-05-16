import folium
from h3 import h3
from collections import Counter
import numpy as np

def plot_most_populated_hexagons(coordinates):
    # Convert coordinates to h3 hexagons at resolution 10
    hexagons = [h3.geo_to_h3(lat, lon, 10) for lat, lon in coordinates]
    
    # Count occurrences of each hexagon
    hexagon_counts = Counter(hexagons)
    
    # Get the 3 most common hexagons
    most_common_hexagons = hexagon_counts.most_common(3)
    
    # Create a map centered at the first most common hexagon
    first_hexagon_center = h3.h3_to_geo(most_common_hexagons[0][0])
    m = folium.Map(location=first_hexagon_center, zoom_start=7)
    
    # Add the most common hexagons to the map
    for hexagon, count in most_common_hexagons:
        # Get the boundary of the hexagon
        boundary = h3.h3_to_geo_boundary(hexagon)
        # Add a polygon to the map for this hexagon
        folium.Polygon(
            locations=boundary + [boundary[0]],  # ensure the polygon is closed
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6,
            popup=f'Count: {count}',
        ).add_to(m)
    
    # Display the map
    return m
