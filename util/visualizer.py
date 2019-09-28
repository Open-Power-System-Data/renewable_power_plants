import cartopy.crs as ccrs 
import cartopy.feature as cfeature
from cartopy.io import shapereader
import geopandas
import shapely
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import cartopy

def visualize_points(latitudes, longitudes, country, categories=None, eps=0.03):
	# Remove the locations not in Europe
	european_latitude_mask = np.logical_and(latitudes >= 34, latitudes <= 81)
	european_longitude_mask= np.logical_and(longitudes >= -31, longitudes <= 69)
	
	european_mask = np.logical_and(european_latitude_mask, european_longitude_mask)
	
	latitudes = latitudes[european_mask]
	longitudes = longitudes[european_mask]

	if categories is not None:
		categories = categories[european_mask]
		
	# Determine the coordinates of boundary locations
	max_lat = latitudes.max()
	min_lat = latitudes.min()

	max_lon = longitudes.max()
	min_lon = longitudes.min()
	
	# Make the area to show a bit larger
	max_lat = max_lat + (max_lat - min_lat) * eps
	min_lat = min_lat - (max_lat - min_lat) * eps
	
	max_lon = max_lon + (max_lon - min_lon) * eps
	min_lon = min_lon - (max_lon - min_lon) * eps
	
	# Get the shape file for visualizing countries
	shp_filename = shapereader.natural_earth('10m', 'cultural', 'admin_0_countries')
	
	df_geo = geopandas.read_file(shp_filename)
	
	polygon = df_geo.loc[df_geo['ADMIN'] == country]['geometry'].values[0]

	# Make sure that polygon is technically multi-part
	# (see https://github.com/SciTools/cartopy/issues/948)
	if type(polygon) == shapely.geometry.polygon.Polygon:
		polygon=[polygon]
		
	# Make the figure
	figure(num=None, figsize=(8, 6), dpi=100, facecolor='white', edgecolor='k')
	ax = plt.axes(projection=ccrs.PlateCarree())
	ax.add_geometries(polygon, crs=ccrs.PlateCarree(), facecolor='white', edgecolor='0.5', zorder=1)
	ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())
	ax.coastlines(resolution='10m', color='black')

	
	# Plot the locations
	if categories is None:
		ax.scatter(longitudes, latitudes, s=1.5, zorder=2, c='#123456')
	else:
		labels = categories.unique()
		for label in labels:
			category_mask = (categories == label)
			latitude_subset = latitudes[category_mask]
			longitude_subset = longitudes[category_mask]
			ax.scatter(longitude_subset, latitude_subset, s=1.5, zorder=2, label=label)
		ax.legend()
		
	
	# Show the figure
	plt.show()


def visualize_countries(countries):
	title = "Countries currently covered by the OPSD renewable power plants package:\n" + ", ".join(countries)

	figure(num=None, figsize=(8, 8), dpi=1000, facecolor='white')
	ax = plt.axes(projection=ccrs.PlateCarree()) 
	ax.add_feature(cartopy.feature.OCEAN, facecolor='#0C8FCE') 
	ax.coastlines(resolution="10m", color="#FFFFFF")

	# Get the shape file for visualizing countries
	shp_filename = shapereader.natural_earth("10m", 'cultural', 'admin_0_countries')
	df_geo = geopandas.read_file(shp_filename)

	wider_european_region = shapely.geometry.Polygon([(-31, 34), (-31, 81), (69, 81), (69, 34)])
	df_selected = df_geo[df_geo["geometry"].intersects(wider_european_region) & (df_geo["NAME"].isin(countries))]
	df_other = df_geo[df_geo["geometry"].intersects(wider_european_region) & (~df_geo["NAME"].isin(countries))]

	for index, row in df_selected.iterrows():
		country_polygon = row['geometry']
		# Mark selected countries
		facecolor = "#173F5F"
		edgecolor = "#FFFFFF"
		# Make sure that polygon is technically multi-part
		# (see https://github.com/SciTools/cartopy/issues/948)
		if type(country_polygon) == shapely.geometry.polygon.Polygon:
			country_polygon = [country_polygon]
		
		ax.add_geometries(country_polygon, crs=ccrs.PlateCarree(), facecolor=facecolor, edgecolor=edgecolor, zorder=2)

	for index, row in df_other.iterrows():
		country_polygon = row["geometry"]
		facecolor = "#EAF7F3"
		edgecolor = "#FFFFFF"
		if type(country_polygon) == shapely.geometry.polygon.Polygon:
			country_polygon = [country_polygon]
		ax.add_geometries(country_polygon, crs=ccrs.PlateCarree(), facecolor=facecolor, edgecolor=edgecolor, zorder=1)
	
	ax.set_extent([-31, 69, 34, 81], crs=ccrs.PlateCarree())

	plt.title(title, fontsize=8)

	plt.show()