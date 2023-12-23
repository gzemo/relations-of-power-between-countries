import os
import numpy as np
import pandas as pd
import networkx as nx
from cdlib import algorithms


class CommunityManager():
	"""
	Compute the extraction of communities for a given year
	
	Example usage
	country_list = pd.read_csv("./country_codes_clean.csv", sep='\t').Alpha3_code.array.tolist()
	cm = CommunityManager(country_list)
	cm.all(algorithm="walktrap", outname="2023_walktrap_communities.csv")
	"""
	def __init__(self, country_list):
		self.timestepnet_folder = "./timestepnet"
		self.country_list = country_list
		self.communities = dict() # unstructured, json like format to use 
		self.graphs = dict() # raw graphs
		self.alliance = dict()
		self.hostility = dict()
		self.min_number_of_elements = 5
		self.are_communities_estimated = False

	def _initial_loader(self, verbose=True):
		"""
		Load the matrices as they are from "./timestepnet"
		"""
		if verbose:
			print(f"Now loading adjacency matrices...")

		# generate all years first
		for item in sorted(os.listdir(self.timestepnet_folder)):
			year = item.split("_")[0][0:4]
			if not year in self.graphs:
				self.graphs[year] = dict()

		# then populate it with months
		for item in sorted(os.listdir(self.timestepnet_folder)):
			year, month = item.split("_")[0][0:4], item.split("_")[0][4:6]
			self.graphs[year][month] = np.load(f"{self.timestepnet_folder}/{item}")

	def _normalize_matrices(self, verbose=True):
		"""
		Helper function to normalize the adjacency matrices weights according to the 
		yearly higher or lower connectivity value:
		Negative and positive weights are normalized independently by rescaling each value
		according to the min/max edge value of the year (across month)
		"""
		if verbose:
			print("Normalizing weights...")

		for year in self.graphs.keys():

			# populate the structure
			self.alliance[year] = dict()
			self.hostility[year] = dict()

			# initialize year matrix
			year_matrix = np.zeros((len(list(self.graphs[year].keys())),
									len(self.country_list),
									len(self.country_list)))

			# retrieve the monthly graphs by putting into a 12-dim matrix
			for i, month in enumerate(self.graphs[year].keys()):
				year_matrix[(i), :, :] = self.graphs[year][month]

			# rescale
			neg_factor, pos_factor = abs(year_matrix.min()), year_matrix.max()
			year_matrix_alliance = np.where(year_matrix>0, year_matrix/pos_factor, 0)
			year_matrix_hostility  = np.where(year_matrix<0, year_matrix/neg_factor, 0)

			for i,month in enumerate(self.graphs[year].keys()):
				self.alliance[year][month]  = year_matrix_alliance[i, :,:]
				self.hostility[year][month] = year_matrix_hostility[i, :,:]

	def _count_communities(self, community_list):
		c = 0
		for community in community_list:
			c+= 1 if len(community) >= self.min_number_of_elements else 0
		return c

	def _filter_community(self, community_list):
		re = []
		for item in community_list:
			if len(item) >= self.min_number_of_elements:
				re.append(item)
		return re

	def community_detector(self, algorithm = "Louvain", verbose = True):
		"""
		Args:
			algorithm: (str) allowed: "Louvain", "walktrap")
			(default "Louvain" for optimization based algorithm) (from networkx)
			verbose: (bool) whether to display the process

		"""
		available_alg = ("Louvain", "walktrap")
		assert algorithm in available_alg, f"Algorithm not found: available: {available_alg}"

		for year in self.graphs.keys():
			
			self.communities[year] = dict()

			for month in self.graphs[year].keys():

				if verbose:
					print(f"Extracting most centered node for: {year}/{month}")

				self.communities[year][month] = dict()

				# loading into graph object
				curr_graph_obj = nx.Graph(self.alliance[year][month])

				# estimating the community entities according to the chosen algorithm
				if algorithm=="Louvain":
					current_community = nx.community.louvain_communities(curr_graph_obj)

				if algorithm=="walktrap":
					current_community = algorithms.walktrap(curr_graph_obj).communities

				# estimating the current Centrality measure (Betweenness Centrality)
				bc = nx.betweenness_centrality(curr_graph_obj)

				# filtering those communities presenting a number of elements below the threshold
				self.communities[year][month]["communities"] = dict()
				self.communities[year][month]["communities"]["all"] = self._filter_community(current_community)
				
				for i,community in enumerate(self.communities[year][month]["communities"]["all"]):
					
					# estimate the most centered node
					subset = [(k, bc[k]) for k in community]
					maximum = sorted(subset, key=lambda x: x[1], reverse=True)[0]
					
					# extract current alliance graph obj
					curr_comm_graph_obj = nx.Graph(self.alliance[year][month][np.ix_(list(community), list(community))])

					# pupulate the structure
					self.communities[year][month]["communities"][f"community_{i+1}"] = dict()
					self.communities[year][month]["communities"][f"community_{i+1}"]["n_items"] = len(community)
					self.communities[year][month]["communities"][f"community_{i+1}"]["elements"] = community
					self.communities[year][month]["communities"][f"community_{i+1}"]["graph_obj"] = curr_comm_graph_obj
					self.communities[year][month]["communities"][f"community_{i+1}"]["top_center_node_name"] = self.country_list[maximum[0]]
					self.communities[year][month]["communities"][f"community_{i+1}"]["top_center_node"] = maximum[0]
					self.communities[year][month]["communities"][f"community_{i+1}"]["top_center_value"] = maximum[1]

		self.are_communities_estimated = True
	
	def retrieve_all_top_centered(self, time_interval = None):
		"""
		Returns a list of all centered node for each year x month community
		Args:
			time_interval: (iterative) of years (e.g. range(2018, 2023))
		"""
		assert self.are_communities_estimated, "Communities have not been estimated yet!" 
		top_centered = []
		
		if not time_interval:
			time_interval = self.communities.keys()

		for y in time_interval:
			for m in self.communities[y].keys():
				m = f"0{str(m)}" if len(str(m))==1 else str(m)
				for c in self.communities[str(y)][m]["communities"].keys():
					if c != "all":
						top_centered.append(self.communities[str(y)][m]["communities"][c]["top_center_node_name"])

		return top_centered

	def into_dataframe(self, outname = None, time_interval = None):
		"""
		Returns the community structure into tabular form
		Args:
			outname: (str) optional: .csv filename to be specified before saving 
			the resulting dataframe
			time_interval: (list) range of years item to loop (leave None if you want to compute
			the whole set of years )
		"""
		assert self.are_communities_estimated, "Communities have not been estimated yet!" 

		sub_df_list = []

		if not time_interval:
			time_interval = self.communities.keys()

		for y in time_interval:
			for m in self.communities[y].keys():
				m = f"0{str(m)}" if len(str(m))==1 else str(m)
				for c in self.communities[str(y)][m]["communities"].keys():
					if c != "all":
						sub_df_list.append(
							pd.DataFrame({
								"year":y,
								"month":m,
								"node_id":self.communities[str(y)][m]["communities"][c]["top_center_node"],
								"node_name":self.communities[str(y)][m]["communities"][c]["top_center_node_name"],
								"metric":"BC",
								"value":self.communities[str(y)][m]["communities"][c]["top_center_value"]},
							index=[0]))

		# concatenate the existing set of data into a single one
		df = pd.concat(sub_df_list, axis = 0)
		
		if outname:
			df.to_csv(f"./communities_records/{outname}", index=False)
		else:
			df.to_csv(f"./communities_records/{str(list(self.communities.keys())[-1])}_communities.csv", index=False)

		return df


	def all(self, algorithm, outname, save_results = True):
		self._initial_loader()
		self._normalize_matrices()
		self.community_detector(algorithm=algorithm)
		if save_results:
			self.into_dataframe(outname=outname)	

