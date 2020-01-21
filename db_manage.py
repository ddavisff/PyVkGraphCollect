from db import couchdb as db
import numpy as np

class merge:

	def UFG(client, group, non_merged_data=None):
		#user-friends-group creates intersection database of user's friends who have a subscription to the same group

		db.create_database(client, group, '_ufg')

		members = db.read(client, group, '_members')[0:][0]['doc']['members']
		friends_db = db.read(client, group, '_friends')

		if non_merged_data == None: 
			friends = friends_db[0:]

			for row in friends:
				data = {}
				data[row['doc']['_id']] = list(set(row['doc']['friends']).intersection(set(members)))
				db.write(db, client, group, '_ufg', [data])

		else: 
			friends = non_merged_data

			for friend_id in friends:
				data = {}
				if friends_db[str(friend_id)][0]['doc']['friends'] != 'account is deleted or hidden':
					data[friends_db[str(friend_id)][0]['doc']['_id']] = \
					list(set(np.asarray(np.array(friends_db[str(friend_id)][0]['doc']['friends']).astype(int))).intersection(set(members)))
					
					db.write(db, client, group, '_ufg', [data])

class compare:

	def data_with_database(client, group, location, data, doc_value):
		db_data = []
		for value in db.read(client, group, location, docs=False)[0:]: db_data.append(value[doc_value])

		diff = np.asarray(np.setdiff1d(np.array(data).astype(int), np.array(db_data).astype(int))).tolist()

		return diff

	def db_friends_and_users(client, group):
		try:
			friends_endpoint = '{0}/{1}'.format(client.server_url, group + '_friends')
			users_endpoint = '{0}/{1}'.format(client.server_url, group + '_users')
			friends_db_length = client.r_session.get(friends_endpoint).json()['doc_count']
			user_data_db_length = client.r_session.get(users_endpoint).json()['doc_count']
			return {'friends': friends_db_length, 'user_data': user_data_db_length}
		except:
			return {'friends': 0, 'user_data': 0}

	def db_merge_type(client, group, merge_type):
		try:
			merge_type_endpoint = '{0}/{1}'.format(client.server_url, group + '_' + merge_type)
			return client.r_session.get(merge_type_endpoint).json()['doc_count']
		except: return 0