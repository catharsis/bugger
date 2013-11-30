import sys
from os.path import expanduser, exists
import re
import argparse
import pydoc
from backends import mantis
import string
from ConfigParser import SafeConfigParser, NoSectionError
__all__=['BugNotFound', 'BuggerLoginError', 'BugRenderError', 'BackendConnectionError']
from exceptions import *

class DefaultBugTemplate(string.Template):
	idpattern = '[_A-Za-z][ _A-Za-z0-9]*.'

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
	def __init__(self, url):
		self.active_backend = mantis.Mantis(url)
	
	def load_template(self, type, use_template=None):
		if use_template and exists(expanduser(use_template)):
			with open(expanduser(use_template)) as tf:
				return tf.read()
		return self.template_strings[type]

	def search(self, terms = {'text': ''}):
		return self.active_backend.search(terms).matches()
				
	def bug(self, bug_id):
		return self.active_backend.bug(bug_id)

def do_show(bugger, args):
	output = ''
	for id in args.id:
		bug = bugger.bug(id)
		if args.short:
			template = bugger.load_template('blurb')
		else:
			template = bugger.load_template('detailed', args.template)
		output += bug.render(template) + '\n'
	return output.strip()

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

	parser = argparse.ArgumentParser(description='Mechanized Mantis', formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog='https://github.com/catharsis/bugger')
	try:
		parser.set_defaults(**dict(configparser.items('bugger')))
	except NoSectionError:
		fallback_defaults = {
				'url': 'http://tracker.example.com',
				}
		parser.set_defaults(**fallback_defaults)
	parser.add_argument('--url', '-u', help='URL to issue tracker')
	parser.add_argument('--template', '-t', help='Path to rendering template for bugs')
	parser.add_argument('--username', help='Issue tracker username')
	parser.add_argument('--password', help='Issue tracker password')

	subparsers = parser.add_subparsers()
	search_parser = subparsers.add_parser('search', help='Search for bugs')
	search_parser.add_argument('term', help='Find bugs matching `term`')
	search_parser.set_defaults(func=do_search)

	bug_parser = subparsers.add_parser('show', help='View individual bug')
	bug_parser.add_argument('id', type=int, nargs='+', help='Show bug with id `id`')
	bug_parser.add_argument('--short', '-s', action='store_true', help='Show blurb for bug with id `id`')
	bug_parser.set_defaults(func=do_show)

	args = parser.parse_args()
	output = ''
	try:
		bugger = Bugger(args.url)
		if args.username and args.password:
			bugger.login(args.username, args.password)

		output = args.func(bugger, args)
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
