import geopandas as gpd
import folium
from branca.colormap import linear

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

# Initialize Folium map
m = folium.Map(location=[52.1, 19.4], zoom_start=6)

# Create a color map
colormap = linear.YlOrRd_09.scale(mean_density_per_city_gdf['OBS_VALUE_T'].min(),
                                  mean_density_per_city_gdf['OBS_VALUE_T'].max())
colormap.caption = "Population Density (people/km²)"

# Add city polygons as individual layers
for _, row in mean_density_per_city_gdf.iterrows():
    city_layer = folium.FeatureGroup(name=row['ADM2_PL'])
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
    ).add_to(city_layer)

    city_layer.add_to(m)

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
        color: white;
        text-align: center;
        width: 100%;
    }
    .color-scale .min {
        top: 0%;
    }
    .color-scale .max {
        bottom: 0%;
    }
</style>
'''
m.get_root().html.add_child(folium.Element(vertical_scale_css))

# Add the color scale div
colormap_div = '''
<div class="color-scale">
    <span class="min">High</span>
    <span class="max">Low</span>
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
        Population Density Map of Poland
    </div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Remove the layer control from the map
# Commented this out to remove the layer control
# LayerControl(collapsed=False).add_to(m)

# Save map to HTML file
m.save('Poland_Population_Density_By_City_Vertical_Scale_No_LayerControl.html')

# Display the map (if in a Jupyter notebook)
m
