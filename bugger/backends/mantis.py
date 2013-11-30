import mechanize
from bs4 import BeautifulSoup
import re,string
from collections import defaultdict
from bugger.util import levenshtein
from bugger.exceptions import *
class Mantis(object):
	texts = {"access_denied": re.compile("Your account may be disabled or blocked or the username/password you entered is incorrect.")}
	def __init__(self, url):
		self.url = url
		self.browser = mechanize.Browser()
		self.browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

	def _open_relative(self, path):
		try:
			return self.browser.open("%s%s" % (self.url, path))
		except mechanize.URLError as e:
			raise BackendConnectionError(str(e))

	def login(self, username, password):
		self._open_relative('/login_page.php')
		self.browser.select_form("login_form")
		self.browser.method = "POST"
		username_control = self.browser.find_control("username")
		password_control = self.browser.find_control("password")
		username_control.value = username
		password_control.value = password
		soup = BeautifulSoup(self.browser.submit())
		if soup.find("div", text=self.texts["access_denied"]):
			raise BuggerLoginError("Login failed for '%s'" % username)

	def bug(self, id):
		response = self._open_relative("/view.php?id=%d" % (id))
		return Bug(response)

	def search(self, terms={}):
		self._open_relative("/view_all_bug_page.php")
		self.browser.select_form('filters_open')
		search_control = self.browser.find_control("search", type="text")
		search_control.value = terms['text']
		soup = BeautifulSoup(self.browser.submit())
		return Search(soup, terms)

class MarkupParseError(Exception): pass
class BugRenderError(Exception): pass
class DefaultBugTemplate(string.Template):
	idpattern = '[_A-Za-z][ _A-Za-z0-9]*.'
class Bug(object):
	vertical_fields = ['ID', 'Project', 'Category', 'View Status', 'Date Submitted', 'Last Update']
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
		>>> Bug.field2attr('the_underscored_field')
		'the_underscored_field'
		'''
		return name.replace(' ', '_').lower()

	def __getattr__(self, name):
		if name != 'soup' and self.soup:
			patterns = [
					re.compile('^\s*'+self.attr2field(name)+'\s*$'),
					re.compile('^\s*'+name+'\s*$')
					]
			for pattern in patterns:
				element = self.soup.find("td", text=pattern)
				if element:
					element = element.find_next_sibling()
					break
			else:
				raise AttributeError

			if name in self.vertical_fields:
				#vertical fields have the field name above their value
				# instead of to the left of it
				i = 0
				row = element.parent
				for sibling in element.previous_siblings:
					i += 1

				element = row.find_next_sibling().find_all("td", limit=i)[-1]
			return element.get_text().strip()
		raise AttributeError

	def __init__(self, html=None, markup=None, dikt=None):
		if html:
			self.soup = BeautifulSoup(html)
		elif markup:
			for attr,val in self.parse_markup(markup):
				setattr(self, self.field2attr(attr), val)
		elif dikt:
			for k, v in dikt.iteritems():
				setattr(self, self.field2attr(k), v)
		try:
			self.summary
		except AttributeError:
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

	@classmethod
	def from_dict(cls, dikt):
		return cls(dikt=dikt)

	def render(self, template_string, template_cls=DefaultBugTemplate):
		if not issubclass(template_cls, DefaultBugTemplate):
			raise BugRenderError("Invalid template class!")
		template = template_cls(template_string)
		def missing_field(key):
			try:
				return getattr(self, key)
			except AttributeError:
				return ""

		attr_dict = fielddict(missing_field)
		for (k,v) in [(self.attr2field(attr), val) for (attr, val) in self.__dict__.items()]:
			attr_dict[k] = v

		output = template.substitute(attr_dict)
		return output

	def submit(self):
		pass

	def __str__(self):
		return (self.summary)

class fielddict(defaultdict):
	def __missing__(self, key):
		if self.default_factory is None:
			raise KeyError(key)
		self[key] = value = self.default_factory(key)
		return value


class Search(object):
	def __init__(self, html, terms={}):
		self.html = html
		self.terms = terms

	def matches(self):
		# match terms, return match dicts
		rows = self.html.find(id='buglist').find_all('tr')[1:]
		matches = []
		headers = []
		for column in rows[0].find_all('td'):
			if column.a:
				headers.append(column.get_text())
			else:
				headers.append('')

		for row in rows[2:]:
			attr_dict = dict(zip(headers,
				[col.get_text() for col in row.find_all('td')]
				))
			try:
				yield Bug.from_dict(attr_dict)
			except BugNotFound:
				pass

class Filter(object):
	def __init__(self, name, want_value):
		self.name = name
		self.want = want_value

	def is_match(self):
		return levenshtein.distance(self.value, self.want) <= 2

	def is_equal(self):
		return self.value == self.want

