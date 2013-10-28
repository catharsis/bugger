import sys
from os.path import expanduser
import re
import mechanize
from bs4 import BeautifulSoup
from bug import Bug, BugNotFound
import textwrap
import argparse
import pydoc
from ConfigParser import SafeConfigParser, NoSectionError

class NoPaging(Exception): pass
class BuggerLoginError(Exception): pass

def windowsize():
	from fcntl import ioctl
	from termios import TIOCGWINSZ
	from array import array
	winsize = array("H", [0, 0, 0, 0] )
	ioctl(sys.stdout.fileno(), TIOCGWINSZ, winsize)
	return (winsize[1], winsize[0])

class Bugger(object):
	texts = {"access_denied": re.compile("Your account may be disabled or blocked or the username/password you entered is incorrect.")}
	def __init__(self, url):
		self.url = url
		self.browser = mechanize.Browser()
		self.browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

	def login(self, username, password):
		self.browser.open("%s/login_page.php" % self.url)
		self.browser.select_form("login_form")
		self.browser.method = "POST"
		username_control = self.browser.find_control("username")
		password_control = self.browser.find_control("password")
		username_control.value = username
		password_control.value = password
		soup = BeautifulSoup(self.browser.submit())
		if soup.find("div", text=self.texts["access_denied"]):
			raise BuggerLoginError("Login failed for '%s'" % username)

	def bug(self, bug_id):
		response = self.browser.open("%s/view.php?id=%d" % ( self.url, bug_id))
		return Bug(response.read())

def main_func():
	reload(sys)
	sys.setdefaultencoding("utf-8")
	configparser = SafeConfigParser()
	url = None
	for p in ['.buggerrc', expanduser('~/.buggerrc'), expanduser('~/.config/bugger/buggerrc')]:
		try:
			configparser.readfp(open(p))
			break #success, break
		except IOError: #no such config file?
			pass

	parser = argparse.ArgumentParser(description='Mechanized Mantis', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	try:
		parser.set_defaults(**dict(configparser.items('bugger')))
	except NoSectionError:
		fallback_defaults = {
				'url': 'http://tracker.example.com',
				}
		parser.set_defaults(**fallback_defaults)
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


if __name__ == '__main__':
	main_func()
