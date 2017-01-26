import sys,getopt,urllib
from html.parser import HTMLParser
from urllib.request import urlopen
from urllib.parse import urljoin

class Crawler():
	parser = None 
	cookie = ''
	rake = None
	base = ''
	login_form = None
	
	class Parser(HTMLParser):
		tag_filter = []
		stack = []
		current = {}
		ignore_data = True

		def handle_starttag(self, tag, attrs):
			if tag in self.tag_filter or self.tag_filter==[]:
				self.stack += [self.current]
				self.current = {}
				self.current['name'] = tag;
				self.current['atts'] = attrs
				self.current['data'] = ''
				self.current['tags'] = []
				self.ignore_data = False
			else:
				self.ignore_data = True

		def handle_endtag(self, tag):
			if tag in self.tag_filter or self.tag_filter==[]:
				ended = self.current
				self.current = self.stack.pop()
				self.current['tags'] += [ended]
			ignore_data = True

		def handle_data(self, data):
			if not self.ignore_data:
				self.current['data'] = data

		def parce(self, text, tag_filter):
			self.tag_filter = tag_filter;
			self.stack = []
			self.current = {}
			self.current['name'] = 'root'
			self.current['tags'] = []
			self.feed(text)	

	def find_links(self, tag, links, tag_filter):
		if ('name' in tag) and ( (tag['name'] in tag_filter) or (tag_filter == []) ):		
			if 'atts' in tag and tag['atts'] != []:
				for (key,value) in tag['atts']:
					if key == 'href':
						ref = urljoin(self.base, value)
						links += [ref]	
		if 'tags' in tag and tag['tags'] != []:
			for inertag in tag['tags']:
				self.find_links(inertag, links, tag_filter)

	def crawl(self, url, deep, tag_filter):
		#print ("scanning ", url )		
		deep -= 1
		req = urllib.request.Request(url)
		if self.cookie:
			req.add_header('Cookie', self.cookie)
		response = urllib.request.urlopen(req)
		if 'text/html' in response.getheader('Content-Type'):
			html_bytes = response.read()
			html_string = html_bytes.decode("utf-8")
			if not self.parser:
				self.parser = self.Parser()	
			self.parser.parce(html_string, tag_filter)
			if self.rake :
				self.rake(self.parser.current)				
			if not deep:
				return			
			links = []
			self.find_links(self.parser.current, links, tag_filter)
			
			for url in links:
				if self.rake == None:
					return
				self.crawl(url, deep, tag_filter)

	def find_tags(self, tag, output, tag_name):
		if 'name' in tag and tag['name'] == tag_name:		
			output+=[tag]
		if 'tags' in tag and tag['tags'] != []:
			for inertag in tag['tags']:
				self.find_tags(inertag, output, tag_name)

	def form_diagnostics(self, form):
		password_feild_name = ''
		login_feild_name = ''
		other_feilds = {} 
		other_name = ''
		action = ''
		if 'atts' in  form  and form['atts'] != []:
			for (key,value) in form['atts']:
				if key =='action':
					action = value
		if 'tags' in form and form['tags'] != []:
			for tag in form['tags']:
				if ('name' in tag and tag['name'] == 'input') and ('atts' in tag and tag['atts'] != []):
					current_name = ''					
					for (key, value) in tag['atts']:
						if key == 'type':
							current_name = value
						if key == 'name' and current_name == 'text':
							if login_feild_name:
								return False
							else:
								login_feild_name = value									
						elif key == 'name' and current_name == 'password':
							if password_feild_name:
								return False
							else:
								password_feild_name = value
						elif key == 'name': 
							other_name = value
						elif key == 'value' and other_name:
							other_feilds[other_name] =value
		if password_feild_name and login_feild_name:
			form['password_feild_name'] = password_feild_name
			form['login_feild_name'] = login_feild_name
			form['other_feilds'] = other_feilds
			form['action'] = action		
			return True
		return False					

	def submit_form(self, form, login, password):		
		post_data={
			form['login_feild_name'] : login,
			form['password_feild_name'] : password,
		}
		post_data.update(form['other_feilds'])		
		post_data = urllib.parse.urlencode(post_data)
		post_data = post_data.encode('UTF-8')	
		req = urllib.request.Request(urljoin(self.base, form['action']), post_data)
		response = urllib.request.urlopen(req)
		return response.getheader('Set-Cookie')

	def rake_loginform(self, tag):
		forms = []
		self.find_tags(tag, forms, 'form')
		for form in forms:
			if self.form_diagnostics(form):
				self.login_form = form			
				self.rake = None

	def table_diagnostics(self, table):
		extract = {}
		current_row_header =' '
		keywords =['Visit', 'Home', 'AddNote', 'About', 'Edit', 'Friends', 'Statistics']
		if 'tags' in table and table['tags'] != []:
			for row in table['tags']:
				if 'name' in row and row['name'] == 'tr':
					if 'tags' in row and row['tags'] != []:
						for cell in row['tags']:
							if ('name' in cell and cell['name'] == 'td'):
								if not current_row_header and cell['data'] and cell['data'] in keywords:
									current_row_header=cell['data']
								if current_row_header and cell['data'] and cell['data']not in keywords:
									extract[current_row_header] = cell['data']
									current_row_header = ''
		print ('-------------------------------------')
		for row, cell in extract.items():
			print ('! %-10s ! %-20s !' % (row, cell))
		print ('-------------------------------------')

	def rake_statis(self, tag):
		tables = []
		self.find_tags(tag, tables, 'table')
		for table in tables:
			self.table_diagnostics(table)

	def grub(self, tasks, host):
		self.base = host
		self.rake = self.rake_loginform;
		self.crawl(host,2,['a', 'form', 'input'])
		if not self.login_form:
			print("Sorry can't find login form")
			return
		for task in tasks:

			self.cookie = self.submit_form(self.login_form, task['login'], task['pass'])		
			if not self.cookie:
				print("Login as ", task['login']," FAIL")
			else:
				print("Login as ", task['login'])
				self.rake = self.rake_statis;
				self.crawl(host,2,['a', 'table', 'tr','td'])	

def useage():
	print('usage: python3 crawler.py -H <host> [user:pass..]')

def incorrect_usage():
	useage()
	sys.exit(2)

def main():
	tasks = []
	hostname = ''
	try:
		optlist, args = getopt.getopt(sys.argv[1:], 'H:')
	except getopt.GetoptError as err:
		incorrect_usage()
	for income in args:
		if ':' in income:
			parsed = income.split(':') 
			if len(parsed) ==2 and parsed[0] and parsed[1]:
				task={'login': parsed[0],'pass':parsed[1]}
				tasks += [task] 
	if optlist and optlist[0][1]:
		hostname = optlist[0][1]
	if not len(tasks) or not hostname:
		incorrect_usage()
	else:
		Crawler().grub(tasks,hostname)

if __name__ == "__main__":
	main()
