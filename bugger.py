import sys
import mechanize
from bug import Bug
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
	url = 'http://tracker.nagios.org/'
	bug_id = 504

	print Bugger(url).bug(bug_id)
