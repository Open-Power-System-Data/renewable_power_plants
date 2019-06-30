import requests
import bs4
from IPython.display import display, Markdown
import pandas as pd

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