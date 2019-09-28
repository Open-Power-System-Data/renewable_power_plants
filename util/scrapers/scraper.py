class Scraper(object):
	"""docstring for Scraper"""
	def __init__(self, url):
		super(Scraper, self).__init__()
		self.url = url
		self.session = None

	def set_session(self, session):
		self.session = session

	def scrape(self, filepath):
		pass