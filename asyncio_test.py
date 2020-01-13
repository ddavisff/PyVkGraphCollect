import asyncio

from vk_api.execute import VkFunction
from user import __user__
from db import __couchdb__ as db
from math import ceil
from delta import __normalization__
from credentials import *
import numpy as np

from statistics import *


class init_asyncio:

	def __init__(self, login, password, group, db_login, db_password, merge_type):

		if group == None: group = GROUP
		if db_login == None: db_login = DB_LOGIN
		if db_password == None: db_password = DB_PASSWORD

		self.login = login
		self.password = password
		self.group = group

		self.db_login, self.db_password = db_login, db_password
		self.client = db.connect(user=self.db_login, password=self.db_password)

		db.create_database(self.client, self.group, '_members')
		db.create_database(self.client, self.group, '_friends')
		db.create_database(self.client, self.group, '_users')

		self.group_list = db.create_database(self.client, '', 'group_list')

		if 'groups' not in self.group_list:
			print('creating a doc')
			data = {
				'_id': 'groups',
				'groups': []
			}
			self.roup_list.create_document(data)

		self.session = __user__().auth(login=self.login, password=self.password)['session']

	def collect_members(self):

		try: self.members = db.read(self.client, self.group, '_members')[0][0]['doc']['members']
		except: self.members = []

		self.friends_db_recordings = db.read(self.client, self.group, '_friends')[0:]
		self.user_data_db_recordings = db.read(self.client, self.group, '_users')[0:]

		if len(self.members) == 0: self.members = collect.members(self.client, self.session, self.group)

	def compare_data_with_database(self, location, data, doc_value):
		db_data = []
		for value in db.read(self.client, self.group, location, docs=False)[0:]: db_data.append(value[doc_value])
		print('compare in process')
		print(type(db_data), type(data))

		diff = np.asarray(np.setdiff1d(np.array(data).astype(int), np.array(db_data).astype(int))).tolist()

		return diff


	def members_friends_diff(self): return self.compare_data_with_database('_friends', self.members, 'id')

	def collect_friends(self, members_splitted_list): collect.friends(self.client, self.session, self.group, members_splitted_list)

	def user_data_collect(self, members_splitted_list): 
		if len(user_data_db_recordings) == 0: collect.user_data(self.client, self.session, self.group, members_splitted_list)

	def db_list_record(self, friends_db_recordings, user_data_db_recordings):
		if len(friends_db_recordings) != 0 and len(user_data_db_recordings) != 0: 
			if self.group not in self.group_list['groups']['groups']:                
				previous_record = self.group_list['groups']['groups']
				document = self.group_list['groups']
				previous_record.append(self.group)      
				document['groups'] = previous_record
				document.save()

logins = ['lion_kennedy@mail.ru', 'ddavis@firemail.cc']
passwords = ['Resident_212_Evil_235', 'Resident_Evil_2']
db_login = 'ellionel'
db_password = 'Resident_Evil_235'
group = 'antifeminismlgbt'

users = []
arrays = []

def init():

	user_1 = init_asyncio(logins[0], passwords[0], group, db_login, db_password, merge_type=None)
	user_2 = init_asyncio(logins[1], passwords[1], group, db_login, db_password, merge_type=None)

	user_1.collect_members()
	print('order')

	users = [user_1, user_2]

	members = user_1.members_friends_diff()

	arrays.append(members[:len(members)//2])
	arrays.append(members[len(members)//2:])


async def req(user_number, array_number):
	users[user_number].collect_friends(arrays[array_number])

	await asyncio.sleep(0.0001)

async def main():
	init()

	await asyncio.gather(*(req(number) for number in range(len(users))))

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())