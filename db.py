from cloudant.client import CouchDB
from cloudant.result import Result

from unqlite import UnQLite

import motor.motor_tornado
import tornado.web

class __operations__:

	def write(self, client, group, location, data):
		if location == '_members':
			data = {
				'group': group,
				'members': data
			}
			self.record_data(client, group, location, data)

		elif location == '_users':
			for user in data:
				data = {
					'_id': str(user['id']),
					'name': user['last_name'] + ' ' + user['first_name'],
					'sex': 'female' if user['sex'] == 1 else 'male'
					#'bdate': user['bdate'] if 'bdate' in user.keys(),
					#'country': user['country']['title'] if 'country' in user.keys(),
					#'city': user['city'] if 'city' in user.keys(),
					#'university': user['universities'][0]['name'] if 'universities' in user.keys()
				}
				self.record_data(client, group, location, data)

		elif location == '_friends':
			for record in data:
				data = {
					'_id': str(list(record.keys())[0]),
					'friends': list(record.values())[0] if type(list(record.values())[0]) is list else 'account is deleted or hidden'
				}
				self.record_data(client, group, location, data)

		elif location == '_ufg':
			for record in data:
				if len(list(record.values())[0]) != 0:
					data = {
						'_id': str(list(record.keys())[0]),
						'edges': list(record.values())[0]
					}
					self.record_data(client, group, location, data)


class __unqlite__(__operations__):

	def connect(db_name):
		return UnQLite(filename=db_name)

	def create_database(client, group, location):
		database = client.collection(group + location)

		if database.exists(): pass
		else:
			database.create()
			print("database " + group + location + " was created")

		return database

	def record_data(client, group, location, data):
		database = client.collection(group + location)
		database.store(data)

	def read(client, group, location):
		return client.collection(group + location)


class __couchdb__(__operations__):

	def connect(user, password):
		return CouchDB(user, password, url='http://127.0.0.1:5984/', connect=True)

	def create_database(client, group, location):
		database = client.create_database(group + location)

		if database.exists(): database = client[group + location]
		else: print("Database " + group + location + " wasn't created")

		return database

	def record_data(client, group, location, data):
		database = client[group + location]
		create_document = database.create_document(data)

	def read(client, group, location, docs=True):
		database = client[group + location]
		return Result(database.all_docs, include_docs=docs)



class __mongodb__(__operations__):

	async def tornado_server(server='mongodb://localhost:27017', database='test', port=8888):

		class MainHandler(tornado.web.RequestHandler):
			def get(self):
				db = self.settings['db']

		client = motor.motor_tornado.MotorClient(server)
		db = await client[database]

		application = tornado.web.Application([
			(r'/', MainHandler)
		], db=db)

		application.listen(port)
		tornado.ioloop.IOLoop.current().start()


