import cartopy.crs as ccrs 
import cartopy.feature as cfeature
from cartopy.io import shapereader
import geopandas
import shapely
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
#import matplotlib.pyplot as plt
import cartopy
#import cartopy.io.shapereader as shpreader
#import cartopy.crs as ccrs
#import pandas as pd

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
    """ Adapted from https://matthewkudija.com/blog/2018/05/25/country-maps/
    """
    #projection = ccrs.Robinson()
    print(countries)
    title = "Countries currently covered by the OPSD renewable power plants package"

    #ax = plt.axes(projection=projection)
    #ax.add_feature(cartopy.feature.OCEAN, facecolor='white')
    #ax.outline_patch.set_edgecolor("0.5")

    figure(num=None, figsize=(8, 8), dpi=1000, facecolor='white', edgecolor='k')
    ax = plt.axes(projection=ccrs.Orthographic())
    # Get the shape file for visualizing countries
    shp_filename = shapereader.natural_earth('10m', 'cultural', 'admin_0_countries')
    df_geo = geopandas.read_file(shp_filename)
    df_europe = df_geo.loc[df_geo["CONTINENT"] == "Europe", :]

    for index, row in df_europe.iterrows():
        polygon = row['geometry']
        # Make sure that polygon is technically multi-part
        # (see https://github.com/SciTools/cartopy/issues/948)
        if type(polygon) == shapely.geometry.polygon.Polygon:
            polygon=[polygon]
        # Make the figure
        if row["NAME"] in countries:
            facecolor = "#000099"#"#71a2d6"
        else:
            facecolor = "#DDDDDD"
        ax.add_geometries(polygon, crs=ccrs.PlateCarree(), facecolor=facecolor, edgecolor='#FFFFFF', zorder=1)
        ax.set_extent([-31, 69, 34, 81], crs=ccrs.PlateCarree())
        ax.coastlines(resolution='10m', color='grey')

    plt.title(title, fontsize=8)

    plt.show()


def mainam():
    df = pd.read_csv('countries.csv', index_col='ISO_CODE')

    projection = ccrs.Robinson()
    title = 'Four Regions With The Same Population'
    colors = ['#f4b042', '#92D050','#71a2d6','#b282ac','#DDDDDD']
    #colors = ['#orange' ,'#green','#blue ','#purple','#grey  ']
    annotation = 'Four Regions With The Same Population: https://mapchart.net/showcase.html'
    plot_countries(df,projection,colors,annotation,title,edgecolor='white')

    projection = ccrs.Orthographic(-30,40)
    colors = ['#71a2d6','#DDDDDD']
    annotation = 'NATO Member Countries: https://en.wikipedia.org/wiki/Member_states_of_NATO'
    title = 'NATO Members'
    plot_countries(df,projection,colors,annotation,title,edgecolor='grey')

    projection = ccrs.Orthographic(10,50)
    colors = ['#000099','#DDDDDD']
    annotation = 'EU Member Countries: https://en.wikipedia.org/wiki/Member_state_of_the_European_Union'
    title = 'EU Members'
    plot_countries(df,projection,colors,annotation,title,edgecolor='grey')

    print('Done.\n')


if __name__ == '__main__':
    main()