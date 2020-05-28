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
from .scrapers.scraper_factory import ScraperFactory

def download_and_cache(url, session=None, download_directory_path=None, filename=None):
		"""
		This function downloads a file into the folder whose name is defined by the parameter input_directory_path.
		Returns the local filepath. 
		If filename is specified, the local file will be named so.
		"""

		user_agent = fake_useragent.UserAgent()
	
		if filename is None:
			path = urllib.parse.urlsplit(url).path
			filename = str(posixpath.basename(path))

		split_path = input_directory_path.split(os.sep)
		download_path_parts = split_path + [filename]
		download_path_parts = [part for part in download_path_parts if part is not None]
		filepath = os.path.join(*download_path_parts)

		os.makedirs(download_directory_path, exist_ok=True)

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

class Downloader(object):
	"""docstring for Downloader"""
	def __init__(self, version, input_directory_path, source_path, download_from):
		super(Downloader, self).__init__()
		self.version = version
		self.input_directory_path = input_directory_path
		self.user_agent = None
		self.source_df = pd.read_csv(source_path)
		self.download_from = download_from

	def set_input_directory_path(self, input_directory_path):
		self.input_directory_path = input_directory_path

	def get_input_directory_path(self):
		return self.input_directory_path

	def derive_filepath(self, country, source_name, filename):
		split_path = self.input_directory_path.split(os.sep)
		download_path_parts = split_path + [country, source_name, filename]
		download_path_parts = [part for part in download_path_parts if part is not None]
		filepath = os.path.join(*download_path_parts)

		return filepath

	def scrape_and_cache(self, url, country, source_name, filename, session=None):
		"""
		This method instantiates the scraper for the given source and country,
		uses is to scrape the data from the url and stores them into the file
		of the given name.
		Returns the local filepath.
		"""

		filepath = self.derive_filepath(country, source_name, filename)

		download_directory = os.path.dirname(filepath)
		os.makedirs(download_directory, exist_ok=True)

		scraper = ScraperFactory.getScraper(country, source_name, url)
		
		if not os.path.exists(filepath):
			if session is not None:
				scraper.set_session(session)
			print('Scraping from', url)
			scraper.scrape(filepath)
		else:
			print('Using local file from', filepath)

		return filepath

		#return 'scrape/{}/{}/{} -> {}'.format(country, source_name, url, filepath)

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

		filepath = self.derive_filepath(country, source_name, filename)

		download_directory = os.path.dirname(filepath)
		os.makedirs(download_directory, exist_ok=True)

		# check if file exists; if it doesn't, download it
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
		folder = 'original_data'
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
		filenames_by_source = source_df[['source', 'filename']]
		filenames_by_source = filenames_by_source.set_index('source')
		filenames_by_source = filenames_by_source.to_dict()['filename']
		return filenames_by_source
	
	def get_download_urls(self, country):
		source_df = self.source_df[self.source_df['country'] == country]
		geo_url = None

		if self.download_from == 'original_sources':
			data_urls = {}
			# check if there are inactive urls
			inactive_df = source_df[source_df['active'] == 'no']
			if not inactive_df.empty:
				filenames_by_source = self.get_filenames_for_opsd(inactive_df)
				for source in filenames_by_source:
					filename = filenames_by_source[source]
					data_urls.update({source : {'url' : self.get_opsd_download_url(filename), 'filename' : filename}})

			active_df = source_df[source_df['active'] == 'yes']
			urls = active_df[['source', 'url', 'filename', 'download_method']]
			urls = urls.set_index('source')
			data_urls.update(urls.to_dict(orient='index'))

		elif self.download_from == 'opsd_server':
			filenames_by_source = self.get_filenames_for_opsd(source_df)
			data_urls = {source : {'url' : self.get_opsd_download_url(filenames_by_source[source])} for source in filenames_by_source}
		else:
			raise ValueError('download_from must be "original_sources" or "opsd_server".')
		
		return data_urls

	def download_data_for_country(self, country):
		urls = self.get_download_urls(country)
		local_paths = {}

		for source_name in urls:
			url = urls[source_name]['url']
			filename = urls[source_name]['filename']
			
			if 'download_method' in urls[source_name] and urls[source_name]['download_method'] == 'scrape':
				datapath = self.scrape_and_cache(url, country, source_name, filename)
			else:
				datapath = self.download_and_cache(url, country=country, source_name=source_name, filename=filename)
			
			local_paths[source_name] = datapath

		return local_paths