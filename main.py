import geopandas as gpd
import folium
from branca.colormap import linear
import math

# Step 1: Load the data
pop_density_gdf = gpd.read_file('C:/tmp/clipped_geopackage.gpkg')
cities_gdf = gpd.read_file(
    'C:/Geospatial-Data-Engineering/Data/pol_adm_gov_v02_20220414_shp/pol_admbnda_adm2_gov_v02_20220414.shp')

# Ensure CRS is the same
pop_density_gdf = pop_density_gdf.to_crs(cities_gdf.crs)

# Perform Spatial Join
pop_density_within_cities = gpd.sjoin(pop_density_gdf, cities_gdf, how='inner', op='within')

# Calculate mean population density per city
mean_density_per_city = pop_density_within_cities.groupby('ADM2_PL').agg({
    'OBS_VALUE_T': 'mean'
}).reset_index()

# Merge with city geometries
mean_density_per_city_gdf = cities_gdf.merge(mean_density_per_city, on='ADM2_PL')

# Calculate the bounds of the GeoDataFrame (min/max coordinates)
bounds = mean_density_per_city_gdf.total_bounds  # [minx, miny, maxx, maxy]

# Calculate the center point of the map (mean of min and max for x and y)
center_lat = (bounds[1] + bounds[3]) / 2  # Average of miny and maxy
center_lon = (bounds[0] + bounds[2]) / 2  # Average of minx and maxx

# Initialize the map using the calculated center
m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

# Fit the map bounds to the data
m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

# Create a color map
colormap = linear.YlOrRd_09.scale(mean_density_per_city_gdf['OBS_VALUE_T'].min(),
                                  mean_density_per_city_gdf['OBS_VALUE_T'].max())
colormap.caption = "Population Density (people/km²)"

# Add city polygons as individual layers
for _, row in mean_density_per_city_gdf.iterrows():
    tooltip = (f"<b>City:</b> {row['ADM2_PL']}<br>"
               f"<b>Mean Density:</b> {row['OBS_VALUE_T']:.2f} people/km²")

    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, obs_value=row['OBS_VALUE_T']: {
            'fillColor': colormap(obs_value),
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.6
        },
        tooltip=folium.Tooltip(tooltip, sticky=True)
    ).add_to(m)

# Add the color scale legend (move it to left-center as a vertical bar)
vertical_scale_css = '''
<style>
    .color-scale {
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%);
        z-index: 1000;
        width: 35px;
        height: 300px;
        border: 1px solid black;
        background: linear-gradient(to top, #ffffcc, #ff0000);
    }
    .color-scale span {
        position: absolute;
        color: black;
        text-align: center;
        width: 100%;
    }
    .color-scale .min {
        bottom: 0%;
    }
    .color-scale .max {
        top: 0%;
    }
</style>
'''
m.get_root().html.add_child(folium.Element(vertical_scale_css))

# Add the color scale div
colormap_div = f'''
<div class="color-scale">
    <span class="min">{math.ceil(mean_density_per_city_gdf['OBS_VALUE_T'].min())}</span>
    <span class="max">{math.ceil(mean_density_per_city_gdf['OBS_VALUE_T'].max())}</span>
</div>
'''
m.get_root().html.add_child(folium.Element(colormap_div))

# Add title
title_html = '''
    <div style="position: fixed; 
                top: 15px; left: 50%; transform: translateX(-50%); 
                background-color: white; padding: 10px; 
                font-size: 18px; font-weight: bold; z-index: 9999; 
                border: 1px solid black; border-radius: 5px;">
        Poland Population Density by City
    </div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save map to HTML file
m.save('Poland_Population_Density_By_City_Vertical_Scale_No_LayerControl.html')

# Display the map (if in a Jupyter notebook)
m
