import sys
import mechanize
from bug import Bug, BugNotFound
import textwrap
import argparse
class Bugger(object):
	def __init__(self, url):
		self.url = url
		self.browser = mechanize.Browser()

	def bug(self, bug_id):
		response = self.browser.open("%s/view.php?id=%d" % ( self.url, bug_id))
		return Bug(response.read())

if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding("utf-8")
	parser = argparse.ArgumentParser(description='Mechanized Mantis')
	parser.add_argument('url', help='URL to Mantis')
	parser.add_argument('id', type=int, help='ID of the bug to operate on')
	args = parser.parse_args()
	url = args.url
	bug_id = args.id
	try:
		bug = Bugger(url).bug(bug_id)
		print bug.summary
		print
		print textwrap.fill("Description: " + bug.description)
		print
		print textwrap.fill("Additional Information: " + bug.additional_information)
	except BugNotFound:
		print "Sorry, that bug doesn't exist."
	
