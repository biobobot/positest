from positest.posi import posi
from positest.posi import Watcher as wtcr
from positest.posi import Collision as clsn
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid.renderers import render_to_response

class PosiViews:
	message = ''
	
	def __init__(self, request):
		self.request = request

	def render_navigation_bar(self):
		if 'login' in self.request.session and self.request.session['login']:
			login = self.request.session['login']
			return render('templates/nav.pt',{
				'items':[
					{'cap':'Home', 'ref':'/?user='+login, 'sel':''},
					{'cap':'About', 'ref':'/about', 'sel':''},
					{'cap':'Friends', 'ref':'/friends', 'sel':''},
					{'cap':'Add note', 'ref':'/addnote', 'sel':''},
					{'cap':'Edit', 'ref':'/edit', 'sel':''},
					{'cap':'Statistics', 'ref':'/stat', 'sel':''},
					{'cap':'Logout', 'ref':'/?logout', 'sel':''}
				]})	
		return render('templates/nav.pt',{
			'items':[
				{'cap':'Home', 'ref':'/', 'sel':''},
				{'cap':'Login', 'ref':'/login', 'sel':''},
				{'cap':'Registration', 'ref':'/login?reg', 'sel':''}
			]})

	def render_message_bar(self):	
		content = ''		
		if self.message:
			content = render('templates/message.pt',{
				'message' : self.message
			})
			self.message = ''
		return content

	def render_nodes(self, request):
		notes = posi.select_notes(request)
		if notes.count():
			return render('templates/nodes.pt',{
				'items' : notes
			})
		else :
			return 'No notes yet'
	
	def render_about(self, request):
			 render('templates/about.pt',{
					'login' : result.get('login'),						
					'about' : result.get('about')
				})	

	def render_page(self, content, request):
		navigation = self.render_navigation_bar()
		messagebar = self.render_message_bar()
		return render_to_response('templates/index.pt', {
			'navigation' : navigation,
			'messagebar' : messagebar,
			'content' : content
		},request)

	@view_config(route_name='home')
	def home(self):
		wtcr.log('home', self.request)
		fail = clsn.all_ok

		if 'logout' in self.request.GET:
			self.request.session['login'] = ""
			self.message = 'You heve just logout'
	
		if 'login.submitted' in self.request.POST:
			fail = posi.login_as_user(self.request)
			if not fail:
				wtcr.log('login', self.request)
				self.message = 'Hello '+ self.request.session['login'] + 'It is good to see you again!'

		if 'reg.submitted' in self.request.POST:
			fail = posi.reg_new_user(self.request)
			if not fail:
				self.message = 'HELLO WELCOME TO OUR FAMILY DEAR '+ self.request.session['login'];

		if 'addnote.submitted' in self.request.POST:
			fail= posi.add_new_note(self.request)

		if 'edit.submitted' in self.request.POST:
			fail= posi.edit_users_profile(self.request)

		if 'friend.submitted' in self.request.POST:
			fail= posi.add_friend(self.request)
			if not fail:
				self.message = 'Now you have new friend '+ self.request.POST['friend'];

		return self.render_page( fail and clsn.render(fail) or self.render_nodes(self.request),self.request)		

	@view_config(route_name='login')
	def login(self):
		if 'reg' in self.request.GET:
			content = render('templates/regform.pt', {})
		else:
			content	= render('templates/loginform.pt', {})
		return self.render_page(content, self.request)

	@view_config(route_name='addnote')
	def addnote(self):
		wtcr.log('addnote', self.request)
		return self.render_page(render('templates/addnoteform.pt', {}), self.request)

	@view_config(route_name='about')
	def about(self):
		wtcr.log('about', self.request)
		(result, fail) = posi.select_user_by_GET(self.request)
		content = ''		
		if not fail:
			content = render('templates/about.pt',{
				'login' : result.get('login'),
				'about' : result.get('about')
			})
		return self.render_page(content and content or clsn.render(fail), self.request)	

	@view_config(route_name='edit')
	def edit(self):
		wtcr.log('edit', self.request)
		(result, fail) = posi.select_user(self.request)
		content =''
		if not fail:
			content = render('templates/editform.pt',{
				'login' : result.get('login'),						
				'about' : result.get('about')
			})
		return self.render_page(content and content or clsn.render(fail), self.request)

	@view_config(route_name='friends')
	def friends(self):
		wtcr.log('friends', self.request)
		content = render('templates/friendsform.pt',{})
		(result, fail) = posi.select_frends(self.request)		
		if not fail and result.count():
			content += render('templates/friends.pt',{
					'items' : result
			})
		elif not fail:
			content += "No Friends yet"
		return self.render_page(content and content or clsn.render(fail), self.request)

	@view_config(route_name='statistics')
	def statistics(self):
		wtcr.log('edit', self.request)
		(result, fail) = posi.select_actions(self.request)
		content =''
		if not fail:
			content = render('templates/statistics.pt',{
				'home' : result.get('home'),
				'addnote' : result.get('addnote'),
				'about' : result.get('about'),
				'edit' : result.get('edit'),
				'friends' : result.get('friends'),
				'statistics' : result.get('statistics'),
				'previsit' : result.get('previsit'),
		})
		return self.render_page(content and content or clsn.render(fail), self.request)


