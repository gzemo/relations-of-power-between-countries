import os
import json
import numpy as np
import pandas as pd
import networkx as nx



class YearManager():
	"""
	Given a year it estimate the nodal metrics of each monthly time step (month graph)
	Example usage: 

	y = YearManager("2022", country_list)
	y.estimate_metrics()
	y.into_dataframe()
	"""

	def __init__(self, date, country_list):
		assert type(date)==str and len(date)==4,\
			"Not a valid input date (usage ex: 2023)"
		self.date = date
		self.country_list = country_list
		self.year_matrix = None
		self.year_matrix_A = None
		self.year_matrix_H = None
		self.retrieved = False
		self.isinitialized = False
		self.G = dict() # utility data structures to store graph attributes and metrics


	def _retrieve_matrices(self):
		"""
		Helper function to build the year adjacency matrix of shape (n_months, n_nodes, n_nodes)
		"""
		tmp = pd.Series(os.listdir("./timestepnet/"))
		current_month_list = sorted(tmp[tmp.str.startswith(self.date)].array.tolist())
		self.year_matrix = np.zeros((len(current_month_list), len(self.country_list), len(self.country_list)))
		for i, month_file in enumerate(current_month_list):
			month_mat = np.load(f"./timestepnet/{month_file}")
			self.year_matrix[i,:,:] = month_mat
		self.retrieved = True


	def _normalize_matrices(self):
		"""
		Helper function to normalize the adjacency matrices weights:
		Negative and positive weights are normalized independently by rescaling each value
		according to the min/max edge value of the year (across month)
		"""
		neg_factor = abs(self.year_matrix.min())
		pos_factor = self.year_matrix.max()
		self.year_matrix = np.where(self.year_matrix<0, self.year_matrix/neg_factor, self.year_matrix)
		self.year_matrix = np.where(self.year_matrix>0, self.year_matrix/pos_factor, self.year_matrix)

	def _split_according_to_weights(self):
		"""
		Helper function that split the current adjacency matrix into two distinct matrices
		depicting the Alliance and Hostile score
		Monthly Allies/Hostile adjacency matrices of shape (12, N_node, N_nodes)
		"""
		self.year_matrix_A = np.where(self.year_matrix>0, self.year_matrix, 0)
		self.year_matrix_H = np.where(self.year_matrix<0, abs(self.year_matrix), 0)

	def _estimate_sparsity_rate(self, month, spec):
		"""
		Return the ratio of zero entry excluding main diagonal for a given month adj matrix
		Args: 
			month: (int) [1:12] given month
			spec: (str) either "A" or "H" for Allied or Hostile respectively
		"""
		assert spec in ("A", "H"), "Not a valid input matrix (allowed: 'A' or 'H')"
		
		if not self.retrieved:
			raise Exception("Year adiacency matrix not loaded yet!")

		curr_mat = self.year_matrix_A if spec=="A" else self.year_matrix_H
		tmp = np.add(curr_mat, np.eye((curr_mat.shape[1])))
		condition = (tmp[(month-1), :, :]==0)
		return (condition.sum() / (tmp.shape[1]**2 - tmp.shape[1]))

	def get_graph(self, month, spec):
		try:
			return self.G[month][spec]["graph"]
		except KeyError:
			print("Not initialized yet!")
			return

	def get_edges(self, month, spec):
		try:
			return self.G[month][spec]["edges"]
		except KeyError:
			print("Not initialized yet!")
			return


	def initialize(self):
		"""
		Initialize self.G data structure for further global/nodal metric estimation
		"""
		self._retrieve_matrices()
		self._normalize_matrices()
		self._split_according_to_weights()

		for i in range(self.year_matrix.shape[0]):
			month = i+1
			self.G[month] = dict()
			for spec in ("A", "H"):
				self.G[month][spec] = dict()
				self.G[month][spec]["graph"] = nx.Graph(self.year_matrix_A[i,:,:] if spec=="A" else self.year_matrix_H[i,:,:])
				self.G[month][spec]["edges"] = self.G[month][spec]["graph"].edges
				self.G[month][spec]["sparsity_ratio"] = self._estimate_sparsity_rate(month, spec)
				self.G[month][spec]["global_metrics"] = dict()
				self.G[month][spec]["nodal_metrics"] = dict()
		self.isinitialized = True

	def _estimate_global_metrics_single(self, month):
		"""
		"""
		for spec in ("A", "H"):
			self.G[month][spec]["global_metrics"]["trans"] = nx.transitivity(self.get_graph(month, spec))
			self.G[month][spec]["global_metrics"]["avg_clustering"] = nx.average_clustering(self.get_graph(month, spec))


	def _estimate_nodal_metrics_single(self, month):
		"""
		Return the nodal metrics of interest of each country for a given month months and update 
		the current G datastructure
		Args:
			month: (int) [1:12] 
		"""
		for spec in ("A", "H"):
			self.G[month][spec]["nodal_metrics"]["BC"] = nx.betweenness_centrality(self.get_graph(month, spec))
			self.G[month][spec]["nodal_metrics"]["CC"] = nx.closeness_centrality(self.get_graph(month, spec))
			self.G[month][spec]["nodal_metrics"]["HC"] = nx.harmonic_centrality(self.get_graph(month, spec))
			self.G[month][spec]["nodal_metrics"]["clustering"] = nx.clustering(self.get_graph(month, spec))

	def estimate_metrics(self):
		"""
		Estimate for each month's graph the resulting global and nodal metrics involved
		in the current analysis and save into a dedicated .json
		"""

		# initialize structure:
		if not self.initialize:
			self.initialize()

		# estimate for all month 
		for month in self.G:
			print(f"Now processing month: {month}")
			self._estimate_global_metrics_single(month)
			self._estimate_nodal_metrics_single(month)

		# filter 
		tmp = self.G.copy()
		for month in tmp:
			for spec in ("A", "H"):
				tmp[month][spec].pop("graph")
				tmp[month][spec].pop("edges")

		# save to file
		filename = f"{self.date}_graph_metrics.json"
		os.system(f"touch ./graph_records/{filename}")
		with open(f"./graph_records/{filename}", "w") as f:
			json.dump(tmp, f)

	def into_dataframe(self):
		"""
		Save locally a .csv file in which each global/nodal metrics are saved 
		{year, month, graph_type, metric_type, metric_name, value}
		"""
		#df = pd.DataFrame()
		sub_df_list_nodal = []
		sub_df_list_global = []
		for i in range(self.year_matrix.shape[0]):
			month = i+1
			for spec in ("A", "H"):
				for metric_type in ("global_metrics", "nodal_metrics"):

					for metric_name in self.G[month][spec][metric_type]:

						if metric_type == "global_metrics":
							node = "global"
							value = self.G[month][spec][metric_type][metric_name]
							sub_df_list_global.append(
								pd.DataFrame({"year":str(self.date),
										"month":str(month),
										"graph_type":spec,
										"metric_type":metric_type,
										"metric_name":metric_name,
										"node":node,
										"value":value},
										index=[0]))

						elif metric_type == "nodal_metrics":
							node = list(self.G[month][spec][metric_type][metric_name].keys())
							value = list(self.G[month][spec][metric_type][metric_name].values())
							sub_df_list_nodal.append(
								pd.DataFrame({"year":str(self.date),
											"month":str(month),
											"graph_type":spec,
											"metric_type":metric_type,
											"metric_name":metric_name,
											"node":node,
											"value":value}))

		df_global = pd.concat(sub_df_list_global, axis=0)
		df_nodal = pd.concat(sub_df_list_nodal, axis=0)
		df_global.to_csv(f"./graph_records/{self.date}_global_graph_metrics.csv", index=False)
		df_nodal.to_csv(f"./graph_records/{self.date}_nodal_graph_metrics.csv", index=False)

