import sys
from os.path import expanduser, exists
import re
import mechanize
from bs4 import BeautifulSoup
from bug import Bug, BugNotFound
from search import Search
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
	template_strings = {
			'detailed': """Summary: ${Summary}
Description: ${Description}
Reported by: ${Reporter}
Additional Information: ${Additional Information}"""
,'blurb': "${id} ${Summary} (${Status})"
}
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

	def load_template(self, type, use_template=None):
		if use_template and exists(expanduser(use_template)):
			with open(expanduser(use_template)) as tf:
				return tf.read()
		return self.template_strings[type]

	def search(self, terms = {'text': ''}):
		url = "%s/view_all_bug_page.php" % self.url
		self.browser.open(url)
		self.browser.select_form('filters_open')
		search_control = self.browser.find_control("search", type="text")
		search_control.value = terms['text']
		soup = BeautifulSoup(self.browser.submit())
		for match in Search(soup, terms).matches():
			try:
				yield Bug.from_dict(match)
			except BugNotFound:
				pass

	def bug(self, bug_id):
		response = self.browser.open("%s/view.php?id=%d" % ( self.url, bug_id))
		return Bug(response.read())

def do_show(bugger, args):
	bug = bugger.bug(args.id)
	return bug.render(bugger.load_template('detailed', args.template))

def do_search(bugger, args):
	output = ""
	template = bugger.load_template('blurb')
	for bug in bugger.search({'text': args.term}):
		output += bug.render(template) + '\n'
	return output.strip()



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
	parser.add_argument('--username', help='Mantis username')
	parser.add_argument('--password', help='Mantis password')

	subparsers = parser.add_subparsers()
	search_parser = subparsers.add_parser('search', help='Search for bugs')
	search_parser.add_argument('term', help='Find bugs matching `term`')
	search_parser.set_defaults(func=do_search)

	bug_parser = subparsers.add_parser('show', help='View individual bug')
	bug_parser.add_argument('id', type=int, help='Show bug with id `id`')
	bug_parser.set_defaults(func=do_show)

	args = parser.parse_args()
	output = ''
	try:
		bugger = Bugger(args.url)
		if args.username and args.password:
			bugger.login(args.username, args.password)

		output = args.func(bugger, args)
	except BugNotFound:
		output = "Sorry, that bug doesn't exist."
	except BuggerLoginError:
		output = "Login failed for user '%s', please check your username and password" % username

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
