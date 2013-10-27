from nose.tools import *
import sys
sys.path.append('../..')
from bugger import *

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
			<table>
		</body
	</html>
	'''
	my_bug = bug.Bug.from_html(html)
	eq_(u'A test bug!', my_bug.summary)

def test_markup_construct():
	multiline_value = '''
	this is a value


	spanning over
	multiple lines
	'''
	markup = '''
	# Summary: A test bug!
	# Some Field: This is the strangest bug
	# Multiline:{multiline}'''.format(multiline=multiline_value)
	my_bug = bug.Bug.from_markup(markup)
	eq_(u'A test bug!', my_bug.summary.strip())
	eq_(u'This is the strangest bug', my_bug.some_field.strip())
	print repr(multiline_value)
	print repr(my_bug.multiline)
	eq_(multiline_value, my_bug.multiline)

@raises(bug.BugNotFound)
def test_raises_BugNotFound():
	bug.Bug(html="This is clearly not an HTML bug")
