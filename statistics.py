from vk_api.execute import VkFunction
from user import __user__
from db import __couchdb__ as db
from math import ceil
from delta import __normalization__
from credentials import *

import time


from vk_api.exceptions import ApiError

class collect:

	def members(client, session, group, retry=3, interval=3, record=True):

		group_get_members = VkFunction(args={'group_id', 'frame'}, code='''

			var count = API.groups.getMembers({"group_id":%(group_id)s, "offset":0, "count":0})["count"];

			var members = count;
			var frames = parseInt(members / 1000 / 24 + 1);
			var frame = %(frame)s;

			var responses = [];

			var i = frame*24;
			var last = i + 24;
			while(i != last){
			    var offset = i*1000;
			    responses = responses + API.groups.getMembers({"group_id":%(group_id)s, "offset":offset, "count":1000})["items"];
			    i = i + 1;
			}

			return {"summary_members":members, "summary_frames":frames, "response":responses};

		''')

		for i in range(retry):
			try:
				members_count = int(group_get_members(session, group, 0)['summary_frames'])
				members = []

				for frame in range(members_count):
					members = members + group_get_members(session, group, frame)['response']
			except ApiError:
				start = time.time()
				end = start + interval
				print('Attempt ' + str(i) + '. Will retry to get members after ' + str(round(end - start)) + ' seconds.')
				time.sleep(3)
				continue
			break
		if record == True:
			db.write(client, group, '_members', members)
			return members
		else: return members


	def user_data(client, session, group, members, record=True):

		user_data = VkFunction(args={'user_ids'}, code='''

			return API.users.get({'user_ids':%(user_ids)s, 'fields':'sex,bdate,country,city,universities', 'name_case':'nom'});

		''')

		user_data_list = []

		frames = ceil(len(members) / 1000)

		frame = 0

		for frame in range(frames):
			user_data_list = user_data_list + user_data(session, members[frame*1000:(frame+1)*1000])

		if record == True: db.write(client, group, '_nodes', user_data_list)
		else: return user_data_list

	def friends(client, session, group, members, record=True):

		subject_friends = VkFunction(args={'user_id', 'offset'}, code='''

			return API.friends.get({"user_id": %(user_id)s, "count": 5000, "offset": %(offset)s})["items"];

		''')

		users_friends = []
		users_friends_encoded = []

		for user in members:
			current = []
			friends = {}
			friends[user] = subject_friends(session, user, 0)
			current.append(friends)

			print(friends.values())
			if record == True: 
				db.write(client, group, '_friends', current)
			
			users_friends.append(friends)

			# friends_encoded = {}
			# friends_encoded[user] = friends
			# users_friends_encoded.append(friends_encoded)

		return users_friends



class merge:

	def UFG(client, group):
		#user-friends-group creates intersection database of user's friends who have a subscription to the same group

		members = db.read(client, group, '_members')[0:]
		print(members)
		friends = db.read(client, group, '_friends')[0:]

		db.create_database(client, group, '_ufg')

		for row in friends:
			data = {}
			data[row['doc']['_id']] = list(set(row['doc']['friends']).intersection(set(members[0]['doc']['members'])))
			db.write(client, group, '_ufg', [data])


class init:

	def __init__(self, login=LOGIN, password=PASSWORD, db_login=DB_LOGIN, db_password=DB_PASSWORD, group=GROUP):
		self.login, self.password = login, password

		self.db_login, self.db_password = db_login, db_password

		self.group = group

		self.session = __user__().auth(login=self.login, password=self.password)['session']
		#for data storing in CouchDB
		self.client = db.connect(user=self.db_login, password=self.db_password)

		#create databases
		# db.create_database(self.client, self.group, '_members')
		# db.create_database(self.client, self.group, '_nodes')
		# db.create_database(self.client, self.group, '_friends')

		# members = collect.members(self.client, self.session, self.group)
		# collect.user_data(self.client, self.session, self.group, members)
		# collect.friends(self.client, self.session, self.group, members)

		merge.UFG(self.client, self.group)

init()

