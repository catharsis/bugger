from bs4 import BeautifulSoup
import re
class Bug(object):
	def __init__(self, html):
		self.soup = BeautifulSoup(html)
		self.summary = self.soup.find("td", text=re.compile("Summary")).find_next_sibling()

	def __str__(self):
		return (self.summary.text.strip())
