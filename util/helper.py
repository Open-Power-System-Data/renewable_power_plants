import requests
import bs4
from IPython.display import display, Markdown
import pandas as pd
import numpy as np

def get_beis_link(UK_page_url):
	UK_link_selector = '.download strong'
	response = requests.get(UK_page_url)
	html = response.content
	soup = bs4.BeautifulSoup(html, 'html.parser')
	span = soup.find('span', class_='download')
	link = span.find('a')
	url_UK_beis = link['href']

	return url_UK_beis


def get_markdowns_for_sources(countries_df, sources_df):
	sources_df.fillna("",inplace=True)
	country_format = "## {full_name} - {short_name}\n{data_description}"
	source_format_with_long_description = """
- [{full_name}]({url}) - {short_description}

> {long_description}
"""
	source_format_without_long_description = "- [{full_name}]({url}) - {short_description}"
	markdowns = []

	for country in countries_df['short_name']:
		country_row = countries_df.loc[countries_df['short_name'] == country]
		country_dict = country_row.to_dict(orient='records')[0] 
		country_text = country_format.format(**country_dict)
		if not pd.isna(country_dict["long_description"]) and len(country_dict["long_description"]) > 0:
			country_text += "\n{}\n".format(country_dict["long_description"])
		#display(country_row)
		country_sources = sources_df[(sources_df['country'] == country) & (sources_df['file_type'] == 'data')]
		source_list = []
		for index, source_row in country_sources.iterrows():
			source_dict = dict(source_row)
			if pd.isna(source_dict["long_description"]) or len(source_dict["long_description"])==0:
				source_text = source_format_without_long_description.format(**source_dict)
			else:
				source_text = source_format_with_long_description.format(**source_dict)
			source_list += [source_text]
		source_text = "\n".join(source_list)
	
		markdown_text = country_text + "\n" + source_text
		markdown = Markdown(markdown_text)
		markdowns += [markdown]
	
	return markdowns


# Define functions for standardizing strings
def standardize_string(x, lower=False):
	if pd.isnull(x):
		return np.nan
	if type(x) is str:
		x = x.strip()
		if lower:
			x = x.lower()
		return x
	
def standardize_column(df, column, lower=False):
	df.loc[:, column]= df.apply(lambda row: standardize_string(row[column], lower=lower),
								axis=1
							   )


# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 13:07:41 2019

@author: jolauson
"""

def sweref99tm_latlon_transform(in1, in2=None, rt90=False):
	""" Transform between lat/lon and SWEREF99TM or RT90"""
	
	if in2 is None:
		in1,in2 = in1[:,0],in1[:,1]
		return_matrix = True
	else:
		return_matrix = False

	in1 = in1.values.astype(float)
	in2 = in2.values.astype(float)
	ind = ((np.isnan(in1)) | (in1 == -9999)) | ((np.isnan(in2)) | (in2 == -9999)) # beakta ej
	out1 = np.nan * in1
	out2 = np.nan * in2
	in1 = in1[~ind]
	in2 = in2[~ind]

	from numpy import sin, cos, cosh, sinh, pi, arcsin, tan, arctan, arctanh
	asin, atan, atanh = arcsin, arctan, arctanh

	if np.nansum(in1) < np.nansum(in2): # in1 ska vara nordlig koordinat
		in1, in2 = in2, in1

	a = 6378137. # semi-major axis of the ellipsoid
	f = 1/298.257222101 # flattening of the ellipsoid
	k0 = 0.9996 # scale factor along the central meridian
	FN = 0. # false northing
	FE = 500000. # false easting
	lambda0 = 15.*pi/180 # central meridian

	if rt90: # RT90 (GRS80)
		FE = 1500064.274
		FN = -667.711
		lambda0 = (15.+48./60+22.624306/3600) * pi/180
		k0 = 1.00000561024

	e = (f*(2-f)) ** 0.5
	n = f/(2-f)
	a_hat = a/(1+n) * (1+n**2/4 + n**4/64)

	if np.nanmax(((in1, in2))) > 1000:
		# x, y -> lat, long 
		xi = (in1-FN) / (k0*a_hat)
		eta = (in2-FE) / (k0*a_hat)
		delta1 = n/2 - 2*n**2/3 + 37*n**3/96 - n**4/360
		delta2 = n**2/48 + n**3/15 - 437*n**4/1440
		delta3 = 17*n**3/480 - 37*n**4/840
		delta4 = 4397*n**4/161280
		xi2 = xi-delta1*sin(2*xi)*cosh(2*eta)-delta2*sin(4*xi)*cosh(4*eta)\
			 -delta3*sin(6*xi)*cosh(6*eta)-delta4*sin(8*xi)*cosh(8*eta)
		eta2 = eta-delta1*cos(2*xi)*sinh(2*eta)-delta2*cos(4*xi)*sinh(4*eta)\
			  -delta3*cos(6*xi)*sinh(6*eta)-delta4*cos(8*xi)*sinh(8*eta)
		phi = asin(sin(xi2)/cosh(eta2))
		lambda1 = atan(sinh(eta2)/cos(xi2))
		A = e**2+e**4+e**6+e**8
		B = -1./6*(7*e**4+17*e**6+30*e**8)
		C = 1./120*(224*e**6+889*e**8)
		D = -1./1260*4279*e**8
		out1[~ind] = 180./pi*(phi+sin(phi)*cos(phi)*\
					   (A+B*(sin(phi))**2+C*(sin(phi))**4+D*(sin(phi))**6))
		out2[~ind] = 180./pi*(lambda1+lambda0)
	else:
		# lat, long -> x, y
		phi = in1*pi/180
		lambda1 = in2*pi/180
		A = e**2
		B = (5*e**4-e**6)/6
		C = (104*e**6-45*e**8)/120
		D = 1237*e**8/1260
		phi2 = phi-sin(phi)*cos(phi)*(A+B*(sin(phi))**2+C*(sin(phi))**4+D*(sin(phi))**6)
		lambda2 = lambda1-lambda0
		xi = atan(tan(phi2)/cos(lambda2))
		eta = atanh(cos(phi2)*sin(lambda2))
		beta1 = n/2-2*n**2/3+5*n**3/16+41*n**4/180
		beta2 = 13*n**2/48-3*n**3/5+557*n**4/1440
		beta3 = 61*n**3/240-103*n**4/140
		beta4 = 49561*n**4/161280
		out1[~ind] = k0*a_hat*(xi+beta1*sin(2*xi)*cosh(2*eta)+beta2*sin(4*xi)*cosh(4*eta)\
					   +beta3*sin(6*xi)*cosh(6*eta)+beta4*sin(8*xi)*cosh(8*eta))+FN
		out2[~ind] = k0*a_hat*(eta+beta1*cos(2*xi)*sinh(2*eta)+beta2*cos(4*xi)*sinh(4*eta)\
					   +beta3*cos(6*xi)*sinh(6*eta)+beta4*cos(8*xi)*sinh(8*eta))+FE
			
	if return_matrix:
		return np.column_stack((out1, out2))
	else:
		if len(out1)==1:
			return out1[0], out2[0]
		else:
			return out1, out2