from vk_api.execute import VkFunction
from user import __user__
from db import __couchdb__ as db
from math import ceil
from delta import __normalization__
from credentials import *
import numpy as np

if LOGIN=='' or PASSWORD=='' or DB_LOGIN=='' or DB_PASSWORD=='' or GROUP=='': from _credentials import *

import argparse
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
			db.write(db, client, group, '_members', members)
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

		if record == True: db.write(db, client, group, '_users', user_data_list)
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

			#print(friends.values())
			#print(current)
			if record == True: 
				db.write(db, client, group, '_friends', current)
			
			users_friends.append(friends)

			# friends_encoded = {}
			# friends_encoded[user] = friends
			# users_friends_encoded.append(friends_encoded)

		return users_friends



class merge:

	def UFG(client, group):
		#user-friends-group creates intersection database of user's friends who have a subscription to the same group

		members = db.read(client, group, '_members')[0:]
		friends = db.read(client, group, '_friends')[0:]

		db.create_database(client, group, '_ufg')

		for row in friends:
			data = {}
			data[row['doc']['_id']] = list(set(row['doc']['friends']).intersection(set(members[0]['doc']['members'])))
			db.write(db, client, group, '_ufg', [data])


class __initialize__:

	def __init__(self, login, password, group, db_login, db_password, merge_type):

		if login == None: login = LOGIN
		if password == None: password = PASSWORD
		if group == None: group = GROUP
		if db_login == None: db_login = DB_LOGIN
		if db_password == None: db_password = DB_PASSWORD

		self.login, self.password = login, password
		self.db_login, self.db_password = db_login, db_password
		self.group = group
		self.client = db.connect(user=self.db_login, password=self.db_password)

		try: self.members = db.read(self.client, self.group, '_members')[0][0]['doc']['members']
		except: self.members = []

		if merge_type == None:
			self.db_check_friends_and_users()
			if self.friends_db_length == len(self.members) and self.user_data_db_length == len(self.members):
				self.make_group_list_record()
			else:
				self.collect()
				self.make_group_list_record()

		else: 
			if merge_type == 'ufg': 
				merge.UFG(self.client, self.group)
				self.make_group_list_record('ufg')

	def compare_data_with_database(self, client, group, location, data, doc_value):
		db_data = []
		for value in db.read(client, group, location, docs=False)[0:]: db_data.append(value[doc_value])

		diff = np.asarray(np.setdiff1d(np.array(data).astype(int), np.array(db_data).astype(int))).tolist()

		return diff

	def db_check_friends_and_users(self):
		try:
			friends_endpoint = '{0}/{1}'.format(self.client.server_url, self.group + '_friends')
			users_endpoint = '{0}/{1}'.format(self.client.server_url, self.group + '_users')
			self.friends_db_length = self.client.r_session.get(friends_endpoint).json()['doc_count']
			self.user_data_db_length = self.client.r_session.get(users_endpoint).json()['doc_count']
		except:
			self.friends_db_length = 0
			self.user_data_db_length = 0

	def collect(self):

		self.session = __user__().auth(login=self.login, password=self.password)['session']
		
		#creates databases if not exists
		db.create_database(self.client, self.group, '_members')
		db.create_database(self.client, self.group, '_friends')
		db.create_database(self.client, self.group, '_users')

		if len(self.members) == 0: self.members = collect.members(self.client, self.session, self.group)

		print('finished to collect friends and members from db')

		if self.friends_db_length == 0: collect.friends(self.client, self.session, self.group, self.members)
		elif self.friends_db_length > 0:
			members_diff = self.compare_data_with_database(self.client, self.group, '_friends', self.members, 'id')

			collect.friends(self.client, self.session, self.group, members_diff)

		if self.user_data_db_length == 0: collect.user_data(self.client, self.session, self.group, members)

	def make_group_list_record(self, method=None):
		group_list = db.create_database(self.client, '', 'group_list')

		def check_group_document():
			if self.group not in group_list:
				data = {
					'_id': self.group,
					'methods': []
				}
				group_list.create_document(data)

		def update_group_list_record(method=None):
			previous_record = group_list[self.group]['methods']

			if method not in previous_record:
				modified_record = previous_record.append(method)		
				current_record = modified_record
				current_record.save()

		check_group_document()
		if method != None: update_group_list_record(method)

parser = argparse.ArgumentParser(description='VK group and user information collector.')

parser.add_argument('--l', metavar='login', type=str, help='VK login')
parser.add_argument('--p', metavar='password', type=str, help='VK password')
parser.add_argument('--g', metavar='group', type=str, help='VK group')
parser.add_argument('--db_l', metavar='db_login', type=str, help='Database login')
parser.add_argument('--db_p', metavar='db_password', type=str, help='Database password')
parser.add_argument('--merge_type', metavar='merge_type', type=str, help='Merge type when merging databases')

args = parser.parse_args()

__initialize__(login=args.l, password=args.p, group=args.g, db_login=args.db_l, db_password=args.db_p, merge_type=args.merge_type)