from user import user

from collect import collect

from db import couchdb as db
from db_manage import merge, compare

from math import ceil

from delta import normalization
from build_graph import build_graph

from credentials import *

if LOGIN=='' or PASSWORD=='' or DB_LOGIN=='' or DB_PASSWORD=='' or GROUP=='': from _credentials import *

import argparse

from networkx_viewer import Viewer

import matplotlib.pyplot as plt


class __initialize__:

	def __init__(self, login, password, group, db_login, db_password, db_address, merge_type, build, collect, plot, viewer):

		if login == None: login = LOGIN
		if password == None: password = PASSWORD
		if group == None: group = GROUP
		if db_login == None: db_login = DB_LOGIN
		if db_password == None: db_password = DB_PASSWORD
		if db_address == None: db_address = 'http://127.0.0.1:5984/'

		self.login, self.password = login, password
		self.group = group
		self.client = db.connect(db_login, db_password, db_address)

		try: self.members = db.read(self.client, self.group, '_members')[0][0]['doc']['members']
		except: self.members = []

		self.compare_db_length = compare.db_friends_and_users(self.client, self.group) #returns {'friends': friends_db_length, 'user_data': user_data_db_length}

		if collect == True:
			print('k')
			if self.compare_db_length['friends'] == len(self.members) and self.compare_db_length['user_data'] == len(self.members):
				db.write(db, self.client, self.group, 'group_list')
			else:
				self.collect_data()
				db.write(db, self.client, self.group, 'group_list')

		elif merge_type != None: 
			if merge_type == 'ufg':
				if compare.db_merge_type(self.client, self.group, merge_type) != 0:
					print(0)
					non_merged_data = compare.data_with_database(self.client, self.group, '_' + merge_type, self.members, 'id')
					if len(non_merged_data) != 0: merge.UFG(self.client, self.group, non_merged_data)
				else: 
					print(1)
					merge.UFG(self.client, self.group)

				db.write(db, self.client, self.group, 'group_list', merge_type)
		
		elif build != None: 
			print('b')
			if build == 'ufg': graph = build_graph.use_networkx(self.client, self.group, build)

			print(graph.number_of_nodes())
			clusters_l = [len(c) for c in sorted(nx.connected_components(graph), key=len, reverse=True)]
			print(clusters_l[:20])

			if plot == True:
				little_v = list(sorted(nx.connected_components(self.graph), key=len, reverse=True)[1])
				little = graph.subgraph(little_v)

				plt.figure()
				pos = nx.kamada_kawai_layout(little_v)
				nx.draw(little, node_size=200, dpi=100)
				plt.show()

			elif viewer == True:
				little_v = list(sorted(nx.connected_components(self.graph), key=len, reverse=True)[1])
				little = graph.subgraph(little_v)

				alg = nx.kamada_kawai_layout(little_v)
				app = Viewer(alg)
				app.mainloop()


	def collect_data(self):

		self.session = user().auth(login=self.login, password=self.password)['session']
		
		#creates databases if not exists
		db.create_database(self.client, self.group, '_members')
		db.create_database(self.client, self.group, '_friends')
		db.create_database(self.client, self.group, '_users')

		if len(self.members) == 0: self.members = collect.members(self.client, self.session, self.group)

		if self.compare_db_length['friends'] == 0: collect.friends(self.client, self.session, self.group, self.members)
		elif self.compare_db_length['friends'] > 0:
			members_diff = compare.data_with_database(self.client, self.group, '_friends', self.members, 'id')

			collect.friends(self.client, self.session, self.group, members_diff)

		if self.compare_db_length['user_data']== 0: collect.user_data(self.client, self.session, self.group, members)


parser = argparse.ArgumentParser(description='VK group and user information collector.')

parser.add_argument('-l', '--login', metavar='login', type=str, help='VK login')
parser.add_argument('-p', '--password', metavar='password', type=str, help='VK password')
parser.add_argument('-g', '--group', metavar='group', type=str, help='VK group')
parser.add_argument('-db_l', '--db_login', metavar='db_login', type=str, help='Database login')
parser.add_argument('-db_p', '--db_password', metavar='db_password', type=str, help='Database password')
parser.add_argument('-db_a', '--db_address', metavar='db_address', type=str, help='Database address (localhost:5984 by default)')
parser.add_argument('-c', '--collect', help='Collect data', action='store_true')
parser.add_argument('-m', '--merge_type', metavar='merge_type', type=str, help='Merging databases with merge type')
parser.add_argument('-b', '--build', metavar='build', type=str, help='Build graph')
parser.add_argument('--plot', help='Plot network', action='store_true')
parser.add_argument('--viewer', help='Plot network in viewer', action='store_true')


args = parser.parse_args()

__initialize__(login=args.login, password=args.password, group=args.group, db_login=args.db_login, db_password=args.db_password, \
	db_address=args.db_address, collect=args.collect, merge_type=args.merge_type, build=args.build, plot=args.plot, viewer=args.viewer)