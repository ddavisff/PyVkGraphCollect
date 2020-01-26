from vk_api.execute import VkFunction
from vk_api.exceptions import ApiError
from db import couchdb as db

from math import ceil
import time

import concurrent.futures

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

		##users_friends = []
		##users_friends_encoded = []

		def request(user):	
			current = []
			friends = {}
			friends[user] = subject_friends(session, user, 0)
			current.append(friends)

			#print(friends.values())
			#print(current)
			if record == True:
				print(members.index(user))
				db.write(db, client, group, '_friends', current)
			
			##users_friends.append(friends)

			# friends_encoded = {}
			# friends_encoded[user] = friends
			# users_friends_encoded.append(friends_encoded)

			##return users_friends

		def request_future(index):
			for user in members[index*25:index*25+25]: request(user)

		members_frame_length = ceil(len(members) / 25)

		#def processes(): 
			#for index in range(0, members_frame_length): request_future(index)

		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor: 
			for index in range(0, members_frame_length): executor.submit(request_future, index)

		#loop = asyncio.get_event_loop()

		#loop.run_until_complete()
