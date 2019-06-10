import requests
import bs4

def get_beis_link(UK_page_url):
	UK_link_selector = '.download strong'
	response = requests.get(UK_page_url)
	html = response.content
	soup = bs4.BeautifulSoup(html, 'html.parser')
	span = soup.find('span', class_='download')
	link = span.find('a')
	url_UK_beis = link['href']

	return url_UK_beis