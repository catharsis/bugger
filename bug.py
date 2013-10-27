from bs4 import BeautifulSoup
import re,string
class BugNotFound(Exception): pass
class MarkupParseError(Exception): pass
class Bug(object):

	@staticmethod
	def attr2field(name):
		'''
		>>> Bug.attr2field('some_field')
		'Some Field'
		>>> Bug.attr2field("information")
		'Information'
		>>> Bug.attr2field("another_field")
		'Another Field'
		'''
		return string.capwords(name, '_').replace('_', ' ')

	@staticmethod
	def field2attr(name):
		'''
		>>> Bug.field2attr('Some Field')
		'some_field'
		>>> Bug.field2attr('Information')
		'information'
		>>> Bug.field2attr('Another Field')
		'another_field'
		'''
		return name.replace(' ', '_').lower()

	def __getattr__(self, name):
		if name != 'soup' and self.soup:
			text = re.compile(self.attr2field(name))
			element = self.soup.find("td", text=text)
			if not element:
				raise AttributeError
			return element.find_next_sibling().text.strip()
		raise AttributeError

	def __init__(self, html=None, markup=None):
		if html:
			self.soup = BeautifulSoup(html)
			try:
				self.summary
			except AttributeError:
				raise BugNotFound
		elif markup:
			for attr,val in self.parse_markup(markup):
				setattr(self, self.field2attr(attr), val)
			try:
				self.summary
			except AttributeError:
				raise BugNotFound
		else:
			raise BugNotFound

	@staticmethod
	def parse_markup(markup):
		attr = None
		value = ""

		while markup.find("#"):
			i = markup.find("#")
			j = markup.find(':')
			attr = markup[i+1:j].strip()
			markup = markup[j+1:]
			if markup.find('#') > -1:
				val = markup[:markup.find('#')]
				yield (attr, val)
			else:
				break
		val = markup
		yield (attr, val)

	@classmethod
	def from_html(cls, html):
		return cls(html=html)

	@classmethod
	def from_markup(cls, markup):
		return cls(markup=markup)


	def submit(self):
		pass

	def __str__(self):
		return (self.summary)
