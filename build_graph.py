import networkx as nx

class build_graph:

	def use_networkx(client, group, merge_type):

		graph = nx.Graph()

		data = db.read(client, group, '_' + merge_type)
		nodes = []

		for user in data[0:]:
			nodes.append(int(user['doc']['_id']))

		graph.add_nodes_from(nodes)

		for user in nodes:
			for target in data[str(user)][0]['doc']['edges']:
				graph.add_edge(user, int(target))

		return graph