import sys
import mechanize
from bug import Bug, BugNotFound
import textwrap
import argparse
import pydoc

class NoPaging(Exception): pass
def windowsize():
	from fcntl import ioctl
	from termios import TIOCGWINSZ
	from array import array
	winsize = array("H", [0, 0, 0, 0] )
	ioctl(sys.stdout.fileno(), TIOCGWINSZ, winsize)
	return (winsize[1], winsize[0])

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
	output = ""
	try:
		bug = Bugger(url).bug(bug_id)
		output += bug.summary
		output += "\n"
		output += "Description: " + bug.description
		output += "\n"
		output += "Additional Information: " + bug.additional_information
	except BugNotFound:
		output = "Sorry, that bug doesn't exist."

	try:
		width, height = windowsize()
		if output.count("\n") > height:
			pydoc.pager(output)
		else:
			raise NoPaging
	except (IOError, NoPaging):
		print(output)
		pass
