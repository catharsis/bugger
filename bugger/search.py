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
			yield dict(zip(headers,[col.get_text() for col in row.find_all('td')]))


