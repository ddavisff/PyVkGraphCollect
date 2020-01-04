import vk_api, json, random, requests, os, urllib
from python3_anticaptcha import ImageToTextTask
from requests.adapters import HTTPAdapter


class __user__(object):

	sessions = []
	session_objects = []
	current_path = os.path.dirname(os.path.abspath(__file__))

	if not os.path.exists(current_path + "/captcha/"):
		os.mkdir(current_path + "/captcha/")

	 
	def own_id(self, session):
		return session.getViewerId()

	
	def auth(self, login, password, current_path=current_path):

		def solve_captcha(file_name, current_path=current_path):
			f = current_path + "/captcha/" + file_name

			answer = ImageToTextTask.ImageToTextTask(anticaptcha_key = "5ff9d58f18ef2972875d74ca4a7af528").captcha_handler(captcha_file = f)

			return answer['solution']['text']

		def captcha_handler(captcha, path=current_path):
			def generate_filename():
				file_name = str(random.getrandbits(32)) + '.jpg'
				return file_name

			file_name = generate_filename()

			urllib.request.urlretrieve(captcha.get_url(), current_path + "/captcha/" + file_name)
			key = solve_captcha(file_name)

			return captcha.try_again(key)

		def proxy(vk_session, max_retries):
			vk_session.http.proxies = {
				'http': 'socks5://127.0.0.1:9050/', 
				'https': 'socks5://127.0.0.1:9050/'
			}

			vk_session.http.mount('https://', HTTPAdapter(max_retries=max_retries))


		vk_session = vk_api.VkApi(login, password, 'oEpGzRwQ6qi1smmZ5zsA', captcha_handler=captcha_handler)
		proxy(vk_session, 3)

		try:
			vk_session.auth()
			print(login + " logged in")
		except vk_api.AuthError as error_msg:
			print(login, error_msg)

		vk = vk_session.get_api()
		user_id = __user__().own_id(vk)

		session = {'id': str(id(vk)), 'session': vk, 'user_id': user_id, 'login': login}

		__user__().sessions.append(session)
		__user__().session_objects.append(vk)

		return session

	@staticmethod
	def session_list(sessions=sessions):
		return sessions

	@staticmethod
	def session_objects_list(session_objects=session_objects):
		return session_objects

	def resolve_name(self, session, screen_name):
		return  str(session.utils.resolveScreenName(screen_name=screen_name)['object_id'])
	 
	def subscriptions(self, session):
		return session.users.getSubscriptions()
		
	def annoying_friends_subscribe(self, session, recipient, **kwargs):

		if 'message' in kwargs:
			try:
				session.friends.delete(user_id=recipient)
				session.messages.send(user_id=recipient, message=kwargs['message'])
			except vk_api.exceptions.ApiError as e:
				session.friends.add(user_id=recipient, text=kwargs['message'])

		else:
			try:
				session.friends.delete(user_id=recipient)
			except vk_api.exceptions.ApiError as e:
				session.friends.add(user_id=recipient)

	 
	def upload_profile_photo(self, session, recipient, donor, current_path=current_path):
		photo = open(current_path + '/photos/avatars/' + donor + '.jpg', 'rb')
		vk_api.upload.VkUpload(session).photo_profile(photo=photo, owner_id=user_id)

	 
	def upload_album_photos(self, session, album_title, donor, current_path=current_path):
		session.photos.createAlbum(title=album_title, privacy_view='all', privacy_comment='nobody')

		upload = vk_api.VkUpload(session)

		photos = upload.photo(
		        '/photos/albums/' + donor + '/*.jpg',
		        album_id=200851098,
		        group_id=74030368
		)

	 
	def collect_albums(self, session, donor, offset):
		album_list = session.photos.getAlbums(owner_id=donor, offset=offset, count=200)
		return [album_list['count'], album_list['items']]

	 
	def collect_photos(self, session, donor, offset):
		collected_photos = session.photos.getAll(owner_id=donor, offset=offset, count=200, photo_sizes=1, extended=1, no_service_albums=0)
		return [collected_photos['count'], collected_photos['items']]	

	 
	def profile_info(self, session):
		return session.account.getProfileInfo() 

	 
	def profile_info_set(self, session, **kwargs):
		variables = ['first_name', 'last_name', 'maiden_name', 'screen_name', 'sex', 'relation', 'relation_partner_id', 'bdate', 'bdate_visibility', 'home_town', 'status']

		for variable in variables:
			if variable in kwargs:		
				session.account.saveProfileInfo(variable + '=' + kwargs[variable])

	 
	def join_chat(self, session, chat_id):
		session.messages.addChatUser(chat_id=chat_id, user_id=user().own_id(session))

	 
	def leave_chat(self, session, chat_id):
		session.messages.removeChatUser(chat_id=chat_id, user_id=user().own_id(session))

	 
	def send_message_chat(self, session, chat_id, message):
		session.messages.send(chat_id=chat_id, message=message)

	 
	def group_join(self, session, group_id):
		session.groups.join(group_id=group_id)

	 
	def wall_get(self, session, owner_id=None, offset=0):
		if owner_id == None:
			print("Curent user")
			session.wall.get(owner_id=owner_id, offset=offset, count=100, filter='owner')
		else:
			print("By owner id")
			session.wall.get(owner_id=owner_id, offset=offset, count=100, filter='owner')

	 
	def wall_repost(self, session, object_, message=None):
		if message == None:
			session.wall.repost(object=object_)
		else:
			session.wall.repost(object=object_, message=message)

