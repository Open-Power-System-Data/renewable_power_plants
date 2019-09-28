import re
import time
import pprint

import traceback
import fake_useragent
import requests
from bs4 import BeautifulSoup

from .scraper import Scraper

pp = pprint.PrettyPrinter(indent=4)

class CZ_ERU_Scraper(Scraper):
	"""docstring for CZ_ERU_Scraper"""
	def __init__(self, url):
		super(CZ_ERU_Scraper, self).__init__(url)
		self.user_agent = fake_useragent.UserAgent().random
		self.header = [ 'site_name','site_region', 'site_postcode', 'site_locality', 'site_district', 'number_of_sources',
			'megawatts_electric_total', 'megawatts_electric_hydro', 'megawatts_electric_solar', 'megawatts_electric_biogas_and_biomass',
			'megawatts_electric_wind', 'megawatts_electric_unspecified', 'megawatts_thermal_total', 'megawatts_thermal_hydro', 
			'megawatts_thermal_solar', 'megawatts_thermal_biogas_and_biomass','megawatts_thermal_wind', 'megawatts_thermal_unspecified',
			'watercourse_length_km', 'watercourse', 'holder_name', 'holder_region', 'holder_address', 'holder_postcode',
			'holder_locality', 'holder_district', 'licence_approval_date', 'licence_number', 'holder_representative', 'link']
		self.request_count = 0
		self.multiple_types_dict = {x:[] for x in range(7)}

	def __get_headers(self):
		# Create a fake user agent
		user_agent = fake_useragent.UserAgent().random

		# Set the header
		headers = {
			'Host': 'licence.eru.cz',
			'Origin': 'http://licence.eru.cz',
			'Referer': 'http://licence.eru.cz/index.php',
			'User-Agent' : user_agent,
		}

		return headers


	def scrape(self, filepath):
		# Create a session if it's not already been done
		print('Scraping the CZ dataset. This will take some time. Please wait.')
		if self.session is None:
			self.session = requests.session()

		# Go to the link 'http://licence.eru.cz/index.php' to establish the session
		response = self.session.post(self.url)

		# Set the form data for filtering power stations
		data = {
			'GroupId' : '11',                       # Electrical energy production
			'SelAdProcStatusId' : 'Udělená licence' # Licence approved
		}

		# Get the header for going through the pages
		self.headers = self.__get_headers()

		# Filter the stations
		response = self.session.post(self.url + '?action=filter&', data, headers=self.headers)
		
		page = 0
		links_of_sites = []
		soup = BeautifulSoup(response.content, 'html.parser')

		links_of_sites = []
		sites = []

		# Create the csv file with the appropriate header
		self.create_csv(filepath)

		# Iterate through pages
		while not self.no_more_pages(soup):
			# Get the filtered stations
			roff = page * 30
			response = self.session.get(self.url + '?roff=' + str(roff), headers=self.headers)
			
			soup = BeautifulSoup(response.content, 'html.parser')

			# Extract the links of individual licence holders
			new_links = self.extract_links(soup)

			# Extract the sites described at each holder's page
			for link in new_links:
				sites_from_the_link = self.get_sites_from_the_link(link)
				sites.extend(sites_from_the_link)

			# if more than 2000 sites are collected,
			# flush them to the file
			if len(sites) > 2000:
				self.flush_to_csv(sites, filepath)
				sites = []
		
			page = page + 1

		# flush the remaining sites
		self.flush_to_csv(sites, filepath)

	def create_csv(self, filepath):
		header_line = ','.join(self.header)

		with open(filepath, "w") as f:
			f.write(header_line + '\n')

	def flush_to_csv(self, sites, filepath):
		with open(filepath, 'a') as f:
			for site in sites:
				strings = []

				for column in self.header:
					string = str(site.get(column, ''))
		
					if ',' in string:
						if string.endswith('\\'):
							string = string.replace('\\', '')
						string = '"' + string + '"'
						#print(string, column, site['link'])

					strings.append(string)
				
				line = ','.join(strings)

				f.write(line + '\n')

	def no_more_pages(self, soup):
		next_links = soup.find_all('a', {'class' : 'pager-next'})

		if next_links is not None and len(next_links) > 0:
			return False
		else:
			return True

	def extract_links(self, soup):
		anchors = soup.find_all('a')
		links = [anchor.get('href') for anchor in anchors]
		links = [link for link in links if 'detail.php' in link]
		links = ['http://licence.eru.cz' + link[1:] for link in links]

		return links

	def get_sites_from_the_link(self, link):
		self.__link = link

		response = self.session.get(link, headers=self.headers)

		soup = BeautifulSoup(response.content, 'html.parser')
		# Extract the details about the holder of the licence
		holder = self.extract_holder_details(soup)
		
		# Extract the details of the individual sites
		# managed by the holder
		sites = self.extract_sites(soup)

		for site in sites:
			site.update(holder)
			site['link'] = link

		return sites

	def extract_holder_details(self, soup):
		header_cells = soup.select('#lic-header-table th')
		data_cells = soup.select('#lic-header-table td')

		licence_holder = {}
		name_was_previous = False

		for header_cell,data_cell in zip(header_cells, data_cells):
			data = self.clean(data_cell.decode_contents())
			header = self.clean(header_cell.decode_contents())

			if len(header) == 0 and name_was_previous is True:
				geo_details = self.extract_holder_geodetails(data_cell.decode_contents())
				licence_holder.update(geo_details)
				name_was_previous = False
			elif header == 'Držitel licence':
				name = self.clean(data_cell.select_one('h1').text)
				licence_holder['holder_name'] = name.replace('"', '\\"')
				name_was_previous = True
			elif header == 'Číslo licence':
				licence_holder['licence_number'] = data
			elif header == 'Odpovědný zástupce':
				licence_holder['holder_representative'] = data
			elif header == 'Datum zahájení výkonu licencované činnosti':
				licence_holder['licence_approval_date'] = data

		return licence_holder

	def clean(self, string):
		if '--' in string:
			return ''
		else:
			string = string.strip().replace(u'\xa0', ' ').replace('\t', ' ')
			string = ' '.join(string.split())
			string = string.replace('\n', ' ')

			return string

	def to_float(self, string):
		string = self.clean(string)
		string = string.replace(' ', '')

		return float(string)

	def to_int(self, string):
		string = self.clean(string)
		string = string.replace(' ', '')

		return float(string)


	def extract_sites(self, soup):
		general_details_tds = soup.select('.lic-tez-header-table tr:nth-child(1) td')
		production_details_tables = soup.select('.lic-tez-data-table')

		sites = []

		for general_details_td, production_details_table in zip(general_details_tds, production_details_tables):
			site = {}
			general_details = self.extract_general_details(general_details_td)
			#print(general_details)
			production_details = self.extract_production_details(production_details_table)
			site.update(general_details)
			site.update(production_details)
			
			sites.append(site)

		return sites

	def extract_general_details(self, main_td):
		details = {}

		detail_divs = main_td.find_all('div')

		name_div = detail_divs[1]
		site_name = self.clean(name_div.decode_contents())

		site_name = site_name.replace('"', '\\"')

		details['site_name'] = site_name
		details['site_postcode'] = ''
		details['site_locality'] = ''
		details['site_district'] = ''
		details['site_region'] = ''

		if len(detail_divs) >= 3:
			geo_div = detail_divs[2]

			geo_content = self.clean(geo_div.decode_contents())

			geo_strings = [string.strip() for string in geo_content.split(',')]
	
			details['site_postcode'], details['site_locality'] = self.extract_postcode_and_locality(geo_strings[0])
	
			for string in geo_strings[2:]:
				if 'okres' in string:
					parts = string.split('okres ')
					if len(parts) == 2:
						details['site_district'] = parts[1]
				elif 'kraj' in string:
					parts = string.split('kraj ')
					if len(parts) == 2:
						details['site_region'] = parts[1]

		return details

	def extract_electric_thermal_megawatts(self, row):
		data_cells = row.select('td')
		megawatts_electric = self.to_float(data_cells[0].decode_contents())
		megawatts_thermal = self.to_float(data_cells[1].decode_contents())

		return megawatts_electric, megawatts_thermal

	def set_megawatts_electric_and_thermal(self, row, details, energy_type):
		megawatts_electric, megawatts_thermal = self.extract_electric_thermal_megawatts(row)
		mwe_key = 'megawatts_electric_{}'.format(energy_type)
		mwt_key = 'megawatts_thermal_{}'.format(energy_type)
		details[mwe_key] = megawatts_electric
		details[mwt_key] = megawatts_thermal

	def extract_production_details(self, table):
		details = {}

		rows = table.select('tr.bl')

		for row in rows[2:]:
			header_cell = row.select_one('th')
			header = self.clean(header_cell.decode_contents())

			if header == 'Celkový':
				self.set_megawatts_electric_and_thermal(row, details, 'total')
			elif header == 'Vodní':
				self.set_megawatts_electric_and_thermal(row, details, 'hydro')
			elif header == 'Sluneční':
				self.set_megawatts_electric_and_thermal(row, details, 'solar')
			elif header == 'Plynový a spalovací':
				self.set_megawatts_electric_and_thermal(row, details, 'biogas_and_biomass')
			elif header == 'Větrný':
				self.set_megawatts_electric_and_thermal(row, details, 'wind')
			elif header == 'Bez názvu':
				self.set_megawatts_electric_and_thermal(row, details, 'unspecified')
			elif header == 'Počet zdrojů':
				data_cell = row.select_one('td')
				number_of_sources = self.to_int(data_cell.decode_contents())
				details['number_of_sources'] = number_of_sources
			elif header == 'Vodní tok':
				data_cell = row.select_one('td')
				watercourse = data_cell.decode_contents()
				details['watercourse'] = self.clean(watercourse)
			elif header == 'Říční km':
				data_cell = row.select_one('td')
				watercourse_length = self.to_float(data_cell.decode_contents())
				details['watercourse_length_km'] = watercourse_length
			elif header in ['Parní', 'Jaderný', 'Přečerpávací', 'Paroplynová', 'Kogenerace']:
				# This row represents conventional technology, so ignore it.
				# Parní = steam turbine, Jaderný = nuclear, Přečerpávací = pumped storage,
				# Paroplynová = fossil fuels, Kogenerace = cogeneration
				continue
			
		#print(details)
		return details

	def extract_holder_geodetails(self, details):
		# Extract information on the licence holder

		# Prepare the dictionary in which the data will be stored
		licence_holder = {}
	
		details = details.split('<br/>')
		details = [self.clean(detail) for detail in details]

		address = details[0]
		postcode_and_locality = details[1]
		postcode, locality = self.extract_postcode_and_locality(postcode_and_locality)

		geo_details_dict = {}

		extractors = {
			'district' : re.compile('okres (.*?)$'),
			'region' : re.compile('kraj (.*?)\s?$'),
		}

		geo_details_dict = {}
	
		for j in range(2, len(details)):
			geo_details = details[j]
			for key in extractors:
				match = extractors[key].search(geo_details)
				if match is not None:
					geo_details_dict[key] = match.group(1)


		licence_holder['holder_address'] = address
		licence_holder['holder_postcode'] = postcode
		licence_holder['holder_locality'] = locality
		licence_holder['holder_district'] = geo_details_dict.get('district', '')
		licence_holder['holder_region'] = geo_details_dict.get('region', '')


		return licence_holder

	def extract_postcode_and_locality(self, string):
		postcode_prefix = ""

		locality = ''
		postcode = ''

		for i, x in enumerate(string):
			if x.isdigit() or x == ' ':
				if x.isdigit():
					postcode_prefix += x
			else:
				locality = string[i:]
				break

		if len(postcode_prefix) == 5:
			postcode = int(postcode_prefix)

		return postcode, locality