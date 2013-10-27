import sys
from os.path import expanduser
import mechanize
from bug import Bug, BugNotFound
import textwrap
import argparse
import pydoc
from ConfigParser import SafeConfigParser

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
	configparser = SafeConfigParser()
	url = None
	for p in [expanduser('~/.buggerrc'), expanduser('~/.config/bugger/buggerrc')]:
		try:
			configparser.readfp(open(p))
			break #success, break
		except IOError: #no such config file?
			pass

	parser = argparse.ArgumentParser(description='Mechanized Mantis', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.set_defaults(**dict(configparser.items('bugger')))
	parser.add_argument('--url', '-u', help='URL to Mantis')
	parser.add_argument('--template', '-t', help='Path to rendering template for bugs')
	parser.add_argument('id', type=int, help='ID of the bug to operate on')
	args = parser.parse_args()
	url = args.url
	bug_id = args.id
	output = ""
	try:
		bug = Bugger(url).bug(bug_id)
		output = bug.render(args.template)
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
