import pandas as pd
import numpy as np
import fiona
import cartopy.io.shapereader as shpreader
import shapely.geometry as sgeom
from shapely.prepared import prep
from shapely.ops import unary_union
import zipfile
import os

class NUTSConverter(object):
	"""docstring for NUTSConverter"""
	def __init__(self, downloader, eu_mapping_files_directory_path):
		super(NUTSConverter, self).__init__()
		self.country = None
		self.downloader = downloader
		self.postcode2nuts_df = None
		self.municipality2nuts_df = None
		self.latlon2nuts = None
		self.__initialize_eu_mapping_files(eu_mapping_files_directory_path)

	def __initialize_eu_mapping_files(self, eu_mapping_files_directory_path):
		# Temporarily redirect the downloader to the directory for eu mapping files
		original_input_directory_path = self.downloader.get_input_directory_path()
		#print('Original IDP', original_input_directory_path)
		self.downloader.set_input_directory_path(eu_mapping_files_directory_path)

		filepaths = self.downloader.download_data_for_country('EU')

		self.eurostat_eu_lau2nuts_path = filepaths['Eurostat']

		eurostat_eu_shapefile_zip_path = filepaths['Eurostat_shapefile']
		self.latlon2nuts = self.open_shapefile(eurostat_eu_shapefile_zip_path)

		#print('Original IDP', original_input_directory_path)
		# Restore the downloader's original input directory path 
		self.downloader.set_input_directory_path(original_input_directory_path)
		#print('Original IDP', self.downloader.get_input_directory_path())


	def open_postcode2nuts(self, postcode2nuts_path):
		return pd.read_csv(postcode2nuts_path,
			sep=';',
			quotechar="'",
			dtype={'CODE' : str, 'NUTS3' : str}
		)

	def open_lau2nuts(self, eurostat_eu_lau2nuts_path, lau_name_type='LATIN'):
		# Prepare the dataframe for mapping municipality names and codes to NUTS-3 regions
		lau_name_column = 'LAU NAME '
		if lau_name_type == 'LATIN':
			lau_name_column += 'LATIN'
		elif lau_name_type == 'NATIONAL':
			lau_name_column += 'NATIONAL'
		else:
			raise ValueError('lau_name_type can only be "LATIN" or "NATIONAL", but is set to: ' + str(lau_name_type))

		municipality2nuts_df = pd.read_excel(eurostat_eu_lau2nuts_path,
			sheet_name=self.country,
			usecols=[lau_name_column, 'LAU CODE', 'NUTS 3 CODE']
		)
		municipality2nuts_df.rename(columns={lau_name_column : 'municipality', 'LAU CODE' : 'municipality_code', 'NUTS 3 CODE' : 'NUTS3'},
			inplace=True
		)

		return municipality2nuts_df

	def open_shapefile(self, eurostat_eu_shapefile_zip_path):
		# Prepare the data for mapping geocoordinates (longitude, latitude) to NUTS-3 regions
		with zipfile.ZipFile(eurostat_eu_shapefile_zip_path, 'r') as container_zip:
			directory_path = os.path.dirname(eurostat_eu_shapefile_zip_path)
			directory_path = os.path.join(directory_path, 'NUTS')
			inner_zip_path = container_zip.extract('NUTS_RG_01M_2016_4326_LEVL_3.shp.zip', directory_path)
			with zipfile.ZipFile(inner_zip_path, 'r') as nuts_zip:
				nuts_zip.extractall(directory_path)
				eurostat_eu_shapefile_path = os.path.join(directory_path, 'NUTS_RG_01M_2016_4326_LEVL_3.shp')

		reader = shpreader.Reader(eurostat_eu_shapefile_path)
		nuts3_regions = reader.records()
		latlon2nuts = {}
		for nuts3_region in nuts3_regions:
			country = nuts3_region.attributes['CNTR_CODE']
			nuts3_code = nuts3_region.attributes['FID']
			latlon2nuts[country] = latlon2nuts.get(country, []) + [nuts3_region]

		return latlon2nuts

	def missing_nuts_mask(self, data_df):
		if 'NUTS3' in data_df:
			return data_df['NUTS3'].isnull()
		else:
			return np.tile(True, data_df.shape[0])

	def clean_after_join(self, df):
		if 'NUTS3' in df.columns and 'NUTS3_y' in df.columns:
			df.loc[:, 'NUTS3'] = df.apply(lambda row: row['NUTS3'] if not pd.isnull(row['NUTS3']) else row['NUTS3_y'],
									axis=1
			)

			columns_to_drop = [column for column in df.columns if column.endswith('_y')]
			
			df.drop(columns_to_drop, axis='columns', inplace=True)

		return df


	def nuts_from_postcode(self, data_df, postcode_column='postcode'):
		df = pd.merge(data_df, self.postcode2nuts_df, left_on=postcode_column, right_on='CODE', how='left', suffixes=('','_y'))
		df.drop(['CODE'], axis='columns', inplace=True)

		df = self.clean_after_join(df)

		return df

	def __from_municipality2nuts(self, data_df, left_column, right_column):
		df = pd.merge(data_df, self.municipality2nuts_df,
						left_on=left_column,
						right_on=right_column,
						how='left',
						suffixes = ('', '_y')
		)

		df = self.clean_after_join(df)

		return df


	def nuts_from_municipality(self, data_df, municipality_column='municipality'):
		return self.__from_municipality2nuts(data_df, municipality_column, 'municipality')

	def nuts_from_municipality_code(self, data_df, municipality_code_column='municipality_code'):
		return self.__from_municipality2nuts(data_df, municipality_code_column, 'municipality_code')

	def __nuts_from_latlon(self, latitude, longitude, closest_approximation=False):
		if pd.isnull(longitude) or pd.isnull(latitude):
				return None
		map_point = sgeom.Point(longitude, latitude)

		for nuts3 in self.latlon2nuts[self.country]:
			if nuts3.geometry.contains(map_point):
				return nuts3.attributes['FID']

		if closest_approximation:
			minimal_distance = 1e12
			closest_nuts = None
			for nuts3 in self.latlon2nuts[self.country]:
				distance = map_point.distance(nuts3.geometry)
				if distance < minimal_distance:
					minimal_distance = distance
					closest_nuts = nuts3
			return closest_nuts.attributes['FID']

		return None

	def nuts_from_latlon(self, data_df, latitude_column='lat', longitude_column='lon', closest_approximation=False):
		mask = self.missing_nuts_mask(data_df)
		data_df.loc[mask, 'NUTS3'] = data_df[mask].apply(lambda row: self.__nuts_from_latlon(row[latitude_column], row[longitude_column], closest_approximation), axis=1)
		return data_df

	def add_nuts_information(self, data_df, country, postcode2nuts_path,
		lau_name_type = 'LATIN', postcode_column='postcode', municipality_column='municipality',
		municipality_code_column='municipality_code', latitude_column = 'lat', longitude_column = 'lon',
		how = ['latlon', 'postcode', 'municipality_code', 'municipality'], closest_approximation=False, verbose=False):
		self.country = country
		
		if 'municipality' in how or 'municipality_code' in how:
			self.municipality2nuts_df = self.open_lau2nuts(self.eurostat_eu_lau2nuts_path, lau_name_type=lau_name_type)
		if 'postcode' in how:
			self.postcode2nuts_df = self.open_postcode2nuts(postcode2nuts_path)

		df = data_df

		for method in how:
			if 'NUTS3' in df.columns and df['NUTS3'].notnull().all():
				print('Done')
				break
			if method == 'postcode':
				df = self.nuts_from_postcode(df, postcode_column=postcode_column)
			elif method == 'municipality':
				df = self.nuts_from_municipality(df, municipality_column=municipality_column)
			elif method == 'municipality_code':
				df = self.nuts_from_municipality_code(df, municipality_code_column=municipality_code_column)
			elif method == 'latlon':
				df = self.nuts_from_latlon(df, latitude_column=latitude_column, longitude_column=longitude_column, closest_approximation=closest_approximation)
			if verbose:
				print("After using" , method, " data, NUTS codes are unknown for", df['NUTS3'].isnull().sum(), "power stations.")

		df['nuts_3_region'] = df['NUTS3']
		df['nuts_2_region'] = df['NUTS3'].str[:-1]
		df['nuts_1_region'] = df['NUTS3'].str[:-2]

		df.drop('NUTS3', axis='columns', inplace=True)

		return df