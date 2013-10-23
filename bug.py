from bs4 import BeautifulSoup
import re,string
class BugNotFound(Exception): pass
class Bug(object):
	def __getattr__(self, name):
		text = re.compile(string.capwords(name, '_').replace('_', ' '))
		element = self.soup.find("td", text=text)
		if not element:
			raise AttributeError
		return element.find_next_sibling().text.strip()

	def __init__(self, html):
		self.soup = BeautifulSoup(html)
		try:
			#if we fail to populate summary, we're out of luck
			self.summary
		except AttributeError:
			raise BugNotFound

	def __str__(self):
		return (self.summary)
