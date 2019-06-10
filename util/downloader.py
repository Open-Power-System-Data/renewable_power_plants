import logging
import os
import posixpath
import urllib.parse
import urllib.request
import re
import zipfile
import pickle
import urllib
import shutil

import numpy as np
import pandas as pd
import utm  # for transforming geoinformation in the utm format
import requests
import fake_useragent
from string import Template
from IPython.display import display
import xlrd
import bs4
import bng_to_latlon
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from .helper import get_beis_link

class Downloader(object):
	"""docstring for Downloader"""
	def __init__(self, version, input_directory_path, source_path, download_from):
		super(Downloader, self).__init__()
		self.version = version
		self.input_directory_path = input_directory_path
		self.user_agent = None
		self.source_df = pd.read_csv(source_path)
		self.download_from = download_from


	def download_and_cache(self, url, session=None, filename=None, country=None, source_name=None):
		"""
		This method downloads a file into the folder whose name is defined by the attribute input_directory_path and 
		parameters country and source name if they are supplied.
		Returns the local filepath. 
		If filename is specified, the local file will be named so.
		"""
		if self.user_agent is None:
			self.user_agent = fake_useragent.UserAgent()
	
		if filename is None:
			path = urllib.parse.urlsplit(url).path
			filename = str(posixpath.basename(path))
			#print(url, "fff", len(filename))

		split_path = self.input_directory_path.split(os.sep)
		download_path_parts = split_path + [country, source_name, filename]
		download_path_parts = [part for part in download_path_parts if part is not None]
		filepath = os.path.join(*download_path_parts)

		download_directory = os.path.dirname(filepath)
		os.makedirs(download_directory, exist_ok=True)

		# check if file exists, if not download it
		if not os.path.exists(filepath):
			if not session:
				#print('No session')
				session = requests.session()

			print("Downloading file ", filename, " from ", url)
			headers = {'User-Agent' : self.user_agent.random}
			response = session.get(url, headers=headers, stream=True)

			chuncksize = 1024
			with open(filepath, 'wb') as file_handler:
				for chunck in response.iter_content(chuncksize):
					file_handler.write(chunck)
			print('Downloading: done.')
		else:
			print("Using local file from", filepath)
		
		filepath = '' + filepath
		
	
		return filepath

	def get_opsd_download_url(self, filename):
		opsd_url = 'https://data.open-power-system-data.org/renewable_power_plants'
		folder = 'original_data/raw'
		opsd_download_url = "/".join([opsd_url, self.version, folder, filename])
	
		return opsd_download_url

	def unzip_and_mark(self, filepath):
		filename = filepath.split(os.sep)[-1]
		new_directory_path = os.path.join(self.input_directory_path, country, source_name, "unzipped")
		os.makedirs(new_directory_path, exist_ok=True)
		if os.path.splitext(filepath)[1] != '.xlsx' and zipfile.is_zipfile(filepath):
			zip_ref = zipfile.ZipFile(filepath, 'r')
			zip_ref.extractall(new_directory_path)
			zip_ref.close()
		else:
			new_filepath = os.path.join(new_directory_path, filename)
			shutil.copy(filepath, new_filepath)
		
	def get_filenames_for_opsd(self, source_df):
		filenames_by_source = source_df[self.source_df['file_type'] == 'data'][['source', 'filename']]
		filenames_by_source = filenames_by_source.set_index('source')
		filenames_by_source = filenames_by_source.to_dict()['filename']
		geo_url = None
		if 'geo' in source_df['file_type'].values:
			geo_filename = source_df[source_df['file_type'] == 'geo'].iloc[0]['filename']
			geo_link = self.get_opsd_download_url(geo_filename)
			geo_url = {'url' : geo_link, 'filename' : geo_filename}
		
		return filenames_by_source, geo_url
	
	def get_download_urls(self, country):
		source_df = self.source_df[self.source_df['country'] == country]
		geo_url = None
		if self.download_from == 'original_sources':
			data_urls = {}
			# check if there are inactive urls
			inactive_df = source_df[source_df['active'] == 'no']
			if not inactive_df.empty:
				filenames_by_source, geo_url = self.get_filenames_for_opsd(inactive_df)
				data_urls.update({source : {'url' : self.get_opsd_download_url(filenames_by_source[source])} for source in filenames_by_source})
			active_df = source_df[source_df['active'] == 'yes']
			urls = active_df[active_df['file_type'] == 'data'][['source', 'url', 'filename']]
			urls = urls.set_index('source')
			data_urls.update(urls.to_dict(orient='index'))
			if 'geo' in active_df['file_type'].values:
				geo_link = source_df[source_df['file_type'] == 'geo'].iloc[0]['url']
				geo_filename = source_df[source_df['file_type'] == 'geo'].iloc[0]['filename']
				geo_url = {'url' : geo_link, 'filename' : geo_filename}
		elif self.download_from == 'opsd_server':
			filenames_by_source, geo_url = self.get_filenames_for_opsd(source_df)
			data_urls = {source : {'url' : self.get_opsd_download_url(filenames_by_source[source])} for source in filenames_by_source}
		else:
			raise ValueError('download_from must be "original_sources" or "opsd_server".')
		
		return {'data': data_urls, 'geo': geo_url}

	def download_data_for_country(self, country):
		urls = self.get_download_urls(country)
		local_paths = {}
		if urls['geo'] is not None:
			url = urls['geo']['url']
			filename = urls['geo'].get('filename', None)
			geopath = self.download_and_cache(url, country=country, filename=filename)
			local_paths['geo'] = geopath
			#print(url, "------------------>", geopath)

		for source_name in urls['data']:
			url = urls['data'][source_name]['url']
			filename = urls['data'].get('filename', None)
			datapath = self.download_and_cache(url, country=country, source_name=source_name, filename=filename)
			local_paths[source_name] = datapath
			#print(source_name, url, "------------------>", datapath)
		return local_paths