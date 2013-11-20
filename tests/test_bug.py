from nose.tools import *
import sys
from string import Template
from bugger import bug

def test_html_construct():
	html = '''
	<html>
		<body>
			<table>
				<tr>
					<td id='summary'>
						Summary
					</td>
					<td>
						A test bug!
					</td>
				</tr>
				<tr>
					<td id='level_of_effort'>
						level_of_effort
					</td>
					<td>
						1-2 days
					</td>
				</tr>
			<table>
		</body
	</html>
	'''
	my_bug = bug.Bug.from_html(html)
	eq_(u'A test bug!', my_bug.summary)
	eq_(u'1-2 days', my_bug.level_of_effort)

def test_markup_construct():
	multiline_value = '''
	this is a value

	spanning over
	multiple lines ...
			it has tabs in it too
		which the parser
			doesn't mess up

embedded control characters are also OK, like \n and \t and stuff..
	'''
	markup = '''
	# Summary: A test bug!
	# Some Field: This is the strangest bug
	# Multiline:{multiline}'''.format(multiline=multiline_value)
	my_bug = bug.Bug.from_markup(markup)
	eq_(u'A test bug!', my_bug.summary.strip())
	eq_(u'This is the strangest bug', my_bug.some_field.strip())
	eq_(multiline_value, my_bug.multiline)

@raises(bug.BugNotFound)
def test_raises_BugNotFound():
	bug.Bug(html="This is clearly not an HTML bug")

def test_render():
	markup = '''
	# Summary: A test bug!
	# Some Field: This is the strangest bug
	'''

	template = '''	__Summary__
	${Summary}
	--------------------
	${Some Field}
	'''
	my_bug = bug.Bug.from_markup(markup)
	output = my_bug.render(template)
	ok_("the strangest bug" in output)
	ok_("A test bug!" in output)

	template = ''' Oops: ${Missing Field} '''
	output = my_bug.render(template)
	ok_("Oops: " in output)


