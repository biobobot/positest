import copy
import hashlib 
import html
from datetime import datetime
from urllib.parse import urlparse
from gridfs import GridFS
from pymongo import MongoClient
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.renderers import render

from pyramid.view import (
	view_config,
	view_defaults
	)

def hash(x):
	m = hashlib.md5()
	m.update(x.encode())
	return m.digest()

def xssprotect(value):
	return html.escape(value)
	
class  Collision():
	all_ok = 0    
	must_login = 1
	must_regist = 2
	user_already_exist = 3
	user_is_not_exist = 4
	confirm_is_not_equals = 5
	poor_request = 6
	login_pass_incorrect = 7
	already_friend = 8

	def render(collision):
		if collision == Collision.must_login:
			return render('templates/oops.pt',{
				'message' : 'WARNING!',
				'descr' : "To do this you must login first",
				'ref' : '/login',
				'ref_desc' : 'Login'
			})
		if collision == Collision.must_regist:
			return render('templates/oops.pt',{
				'message' : 'WARNING!',
				'descr' : "To do this you must take registration first",
				'ref' : '/login',
				'ref_desc' : 'Login'
			})
		if collision == Collision.user_already_exist:
			return render('templates/oops.pt',{
				'message' : 'OOPS!',
				'descr' : "Such user already exists",
				'ref' : 'login?reg',
				'ref_desc' : 'Try again'
			})
		if collision == Collision.user_is_not_exist:
			return render('templates/oops.pt',{
				'message' : 'OOPS!',
				'descr' : "Such user is not  exists",
				'ref' : '/friends',
				'ref_desc' : 'Try again'
			})
		if collision == Collision.confirm_is_not_equals:
			return render('templates/oops.pt',{
				'message' : 'OOPS!',
				'descr' : "Password is notequals to confirm",
				'ref' : '',
				'ref_desc' : ''
			})
		if collision == Collision.poor_request:
			return render('templates/oops.pt',{
				'message' : 'ATTENSION!',
				'descr' : 'Poor request!',
				'ref' : '',
				'ref_desc' : ''
			})
		if collision == Collision.login_pass_incorrect:
			return render('templates/oops.pt',{
				'message' : 'OOPS!',
				'descr' : "Can't enter site. Check your login/password to be correct",
				'ref' : '/login',
				'ref_desc' : 'Try again'
			})
		if collision == Collision.already_friend:
			return render('templates/oops.pt',{
				'message' : 'OOPS!',
				'descr' : "You already have him in friends list",
				'ref' : '/friends',
				'ref_desc' : 'More friends'
			})
		return ''

class Watcher():
	def log(page, request):
		if 'login' in request.session and request.session['login']:
			login = request.session['login']
			db = Posi().db
			document = db.actions.find_one({'user':login})
			if not document:
				document = {
					'user' : login,
					'previsit' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					'lastvisit' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					'home' : 0,
					'addnote' : 0,
					'about' : 0,
					'edit' : 0,	
					'friends' : 0,
					'statistics' : 0,
					'login' : 0
				}
				db.actions.insert_one(document)
			document[page] += 1;
			if page == 'login':
				document['previsit'] = document['lasttime']
			document['lasttime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			db.actions.update({'user':login}, document)
			result = db.actions.find()

class Posi(object):
	obj = None
	db = None
	settings = None
	message = ''
	def __new__(cls, *dt, **mp):
		if cls.obj is None:
			cls.obj = object.__new__(cls, *dt, **mp)
		return cls.obj

	def login_as_user(self, request):
		try:
			login = xssprotect(request.POST['login'])
			password = xssprotect(request.POST['password'])
		except:
			return Collision.poor_request			
		result = self.db.users.find_one({'login' : login, 'password' : hash(password)})
		if result:
			request.session['login'] = login
		else:
			return Collision.login_pass_incorrect
		return Collision.all_ok

	def reg_new_user(self, request):
		try:		
			login = xssprotect(request.POST['login'])
			password = xssprotect(request.POST['password'])
			confirm = xssprotect(request.POST['confirm'])
			about = xssprotect(request.POST['about'])
		except:
			return Collision.poor_request
		if password != confirm:
			return Collision.confirm_is_not_equals
		result = self.db.users.find_one({'login' : login})
		if result:
			return Collision.user_already_exist 
		self.db.users.insert_one(
			{
				'login' : login,
				'password' : hash(password),
				'about' :about
			})
		request.session['login'] = login
		return Collision.all_ok

	def add_new_note(self, request):
		try:		
			caption = xssprotect(request.POST['caption'])
			topic = xssprotect(request.POST['topic'])
		except:
			return Collision.poor_request
		if 'login' in request.session and request.session['login']:
			login = request.session['login']
			self.message = 'Note added to tape of'+login
			self.db.notes.insert_one(
				{
					'login' : login,
					'caption' : request.POST['caption'],
					'topic' : request.POST['topic']
				})
		else:
			return Collision.must_login
		return Collision.all_ok

	def edit_users_profile(self, request):
		if 'login' in request.session and request.session['login']:
			login = request.session['login']
			try:
				password = xssprotect(request.POST['password'])
				confirm = xssprotect(request.POST['confirm'])
				about = xssprotect(request.POST['about'])
				newpassord = xssprotect(request.POST['newpassord'])
			except:
				return Collision.poor_request

			if confirm != newpassord:
				return Collision.confirm_is_not_equals

			result = self.db.users.find_one({'login' : login, 'password' : hash(password)})
			if result:
				newprofile = copy.deepcopy(result)
				newprofile['password'] = hash(newpassord)
				newprofile['about'] = about
				self.db.users.update({'login':login, 'password':hash(password)}, newprofile)
				self.message = "Profile has been changed"
			else:
				return Collision.login_pass_incorrect
		else:
			return Collision.must_login
		return Collision.all_ok

	def add_friend(self, request):
		if 'login' in request.session and request.session['login']:
			login = request.session['login']
			friend = request.POST['friend']
			result = self.db.friends.find_one({'login' : login, 'friend' : friend})
			if result:
				return Collision.already_friend			
			result = self.db.users.find_one({'login' : friend})
			if result:
				self.db.friends.insert_one(
					{
						'login' : login,
						'friend' : friend,
					})
				self.messge = 'You have new frend: '+friend
			else:
				return Collision.user_is_not_exist
		else:	
			return Collision.must_login
		return Collision.all_ok

	def select_notes(self, request):
		notes=None
		print("HELLO")
		if 'user' in request.GET and request.GET['user']:
			login = request.GET['user']
			notes = self.db.notes.find({'login':login})
		else:
			notes = self.db.notes.find()
			
		return notes	

	def select_user_by_GET(self, request):
		result = None
		if 'user' in request.GET and request.GET['user']:
			login = request.GET['user']
		elif 'login' in request.session and request.session['login']:
			login = request.session['login']
		if login:
			result  = self.db.users.find_one({'login' : login})
			if not result:
				return result, Collision.must_login
		else:
			return result, Collision.must_regist
		return result, Collision.all_ok

	def select_user(self, request):
		result = None
		if 'login' in request.session and request.session['login']:
			login = request.session['login']						
			result = self.db.users.find_one({'login':login})
		else:
			return result,Collision.must_login
		return result, Collision.all_ok 
		

	def select_frends(self, request):
		result = None
		if 'login' in request.session and request.session['login']:
			login = request.session['login']						
			result = self.db.friends.find({'login':login})
		else:
			return result, Collision.must_login
		return result, Collision.all_ok
	
	def select_actions(self, request):
		result = None
		if 'login' in request.session and request.session['login']:
			login = request.session['login']						
			result = self.db.actions.find_one({'user':login})
		else:
			return result, Collision.must_login
		return result, Collision.all_ok

	def start_pyramid(self):
		session_factory = SignedCookieSessionFactory('FIQ>>>9zs')
		config = Configurator(session_factory=session_factory)
		config.include('pyramid_chameleon')
		config.add_static_view(name='static', path='positest:static')
		config.add_route('home', '/')
		config.add_route('login', '/login')
		config.add_route('addnote', '/addnote')
		config.add_route('about', '/about')
		config.add_route('edit', '/edit')
		config.add_route('friends', '/friends')
		config.add_route('statistics', '/stat')
		config.scan('positest.views')
		return config.make_wsgi_app()

	def start_pymongo(self):
		db_url = urlparse(self.settings['mongo_uri'])
		client = MongoClient(
			host = db_url.hostname,
			port = db_url.port
		)
		return client[db_url.path[1:]]
	
	def	start(self, settings):
		self.settings = settings
		self.db = self.start_pymongo()
		app = self.start_pyramid()
		return app

posi = Posi()	

