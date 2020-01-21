import vk_api, json, random, requests, os, urllib
from python3_anticaptcha import ImageToTextTask
from requests.adapters import HTTPAdapter


class user(object):

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
		user_id = user().own_id(vk)

		session = {'id': str(id(vk)), 'session': vk, 'user_id': user_id, 'login': login}

		user().sessions.append(session)
		user().session_objects.append(vk)

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
	 
	def collect_albums(self, session, donor, offset):
		album_list = session.photos.getAlbums(owner_id=donor, offset=offset, count=200)
		return [album_list['count'], album_list['items']]
	 
	def collect_photos(self, session, donor, offset):
		collected_photos = session.photos.getAll(owner_id=donor, offset=offset, count=200, photo_sizes=1, extended=1, no_service_albums=0)
		return [collected_photos['count'], collected_photos['items']]	
	 
	def profile_info(self, session):
		return session.account.getProfileInfo() 

	def group_join(self, session, group_id):
		session.groups.join(group_id=group_id)

	def wall_get(self, session, owner_id=None, offset=0):
		if owner_id == None:
			print("Curent user")
			session.wall.get(owner_id=owner_id, offset=offset, count=100, filter='owner')
		else:
			print("By owner id")
			session.wall.get(owner_id=owner_id, offset=offset, count=100, filter='owner')


