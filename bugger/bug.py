from bs4 import BeautifulSoup
import re,string
from collections import defaultdict
class BugNotFound(Exception): pass
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
			texts = [re.compile(self.attr2field(name)), re.compile(name)]
			for text in texts:
				element = self.soup.find("td", text=text)
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
				while element:
					element = element.find_previous_sibling()
					i += 1

				element = row.find_next_sibling().find_all("td", limit=i-1)[-1]
			return element.text.strip()
		raise AttributeError

	def __init__(self, html=None, markup=None):
		if html:
			self.soup = BeautifulSoup(html)
		elif markup:
			for attr,val in self.parse_markup(markup):
				setattr(self, self.field2attr(attr), val)
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

	def render(self, template_string=None, template_cls=DefaultBugTemplate):
		if not issubclass(template_cls, DefaultBugTemplate):
			raise BugRenderError("Invalid template class!")
		if not template_string:
			template_string = self._default_template_string
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

	_default_template_string = """Summary: ${Summary}
Description: ${Description}
Reported by: ${Reporter}
Additional Information: ${Additional Information}"""

class fielddict(defaultdict):
	def __missing__(self, key):
		if self.default_factory is None:
			raise KeyError(key)
		self[key] = value = self.default_factory(key)
		return value
