import os
import io
import zipfile
import requests
import numpy as np
import pandas as pd

"""
Set of utility classes used to gather and build adiacency matrices from GDELT datase
"""

class DayEstimator():

	def __init__(self, date, country_list, masterfile):
		assert isinstance(date, str) and len(date)==8, "Not a valid input date!"
		self.date = date
		self.country_list = country_list
		self.masterfile = masterfile # must be a pandas DF
		self.record_list = []
		self.theta1 = 0.025
		self.theta2 = 0.01
		self.theta3 = 0.01
		self.matrix = None
		self.pattern = "|".join(self.country_list).replace(" ","")
		
	def _initialize_adiacency_matrix(self):
		self.matrix = np.zeros((len(self.country_list), len(self.country_list)))

	def _retrieve_daily_records(self):
		self.record_list = self.masterfile[self.masterfile[0]==int(self.date)][1].array.tolist()

	def _download_process_single(self, single_record_url, clean_after_computation=True):
		"""
		Single timestamp (15min records) download, extraction, filtering and processing
		to have the current 15min graph 
		Args:
			single_record_url: (str) url for that given endpoint
			clean_after_computation: (bool) whether to delete the 15min timestamp csv after
				computations
		"""
		single_record_url = single_record_url.strip()
		tmp = single_record_url.split("/")[-1].lower().split(".")
		date, spec = tmp[0], tmp[1]

		print(f"Downloading: {date[0:4]}/{date[4:6]}/{date[6:8]} - {date[8:10]}:{date[10:12]} {spec}", end="  ")
		#print(f"File: *** {single_record_url}")
		
		# performing request and check integrity
		r = requests.get(single_record_url)
		if not r.ok:
			print(f"*** Warning: no valid response gathered!")
			return 

		# zip extraction 
		z = zipfile.ZipFile(io.BytesIO(r.content))
		z.extractall(f"./rawdata/")
		
		# address the empty file condition
		try:
			current = pd.read_csv(f"./rawdata/{date}.{spec}.CSV", sep="\t", header=None)
		except Exception:
			print("*** Warning: something wrong in the process of reading the current file!")
			return 

		current = current[(current[5].notnull()) & (current[15].notnull())]
		current_filtered = current[(current[5].str.fullmatch(self.pattern)) &\
			(current[15].str.fullmatch(self.pattern))]

		print(f"Found: {current_filtered.shape[0]} valid events: now parsing records...")
		
		for i in range(current_filtered.shape[0]):

			current_row = current_filtered.iloc[i]

			# parameter extraction
			actor1, actor2 = current_row[5], current_row[15]
			actor1_idx, actor2_idx = self.country_list.index(actor1), self.country_list.index(actor2)
			G, n_sources, n_articles, avg_tone = current_row[30], current_row[32], current_row[33], current_row[34]
			
			# edge estimation
			if G>0:
				edge = G + self.theta1*n_sources + self.theta2*n_articles + self.theta3*avg_tone
			elif G<0:
				edge = G + (-1)*(self.theta1*n_sources + self.theta2*n_articles) + self.theta3*avg_tone
			else:
				if avg_tone>0:
					edge = self.theta1*n_sources + self.theta2*n_articles + self.theta3*avg_tone
				elif avg_tone<0:
					edge = (-1)*(self.theta1*n_sources + self.theta2*n_articles) + self.theta3*avg_tone
				else:
					edge = 0
			# assuming undirect graph both edges must be equal
			self.matrix[actor1_idx, actor2_idx] += edge
			self.matrix[actor2_idx, actor1_idx] += edge

		# remove file
		if clean_after_computation:
			os.system(f"rm ./rawdata/{date}.{spec}.CSV")


	def process_day(self):
		"""
		Single day matrix estimation by additive process
		"""
		self._initialize_adiacency_matrix()
		self._retrieve_daily_records()
		for record in self.record_list:
			self._download_process_single(record)
		print(f"Saving into ./networks ...")
		np.save(f"./networks/{self.date}_network.npy", self.matrix)
		print(f"Completed!", end="\n")

		

class MonthEstimator():

	def __init__(self, date, country_list, masterfile):
		"""
		Args:
			date: (str) a valid month date (ex "202306", June 2023)
		"""
		assert isinstance(date, str) and len(date)==6, \
			"Not a valid input month! (usage ex: '202306', for June 2023)"
		self.date = date
		self.country_list = country_list
		self.masterfile = masterfile # must be a pandas DF
		self.day_list = []

	def _retrieve_montly_records(self):
		self.masterfile["month"] = self.masterfile[0].apply(lambda	x: str(x)[0:6])
		self.day_list = self.masterfile[self.masterfile.month == self.date][0].unique().tolist()

	def _process_all_days(self):
		"""
		Estimate each day adiacency matrix and store in the ./networks folder
		"""
		self._retrieve_montly_records()
		for day in self.day_list:
			print(f"\nNow performing {day}.")
			estimator = DayEstimator(str(day), self.country_list, self.masterfile)
			estimator.process_day()

	def process_month(self, excluding_zero_edge=True):
		"""
		Final computation: average each non-zero edge over the month
		"""
		self._process_all_days()

		# select each file belonging to the current month
		print("Now averaging:")
		tmp = pd.Series(os.listdir("./networks"))
		current_month_list = tmp[tmp.str.startswith(self.date)]

		month_matrix = np.zeros((len(current_month_list), len(self.country_list), len(self.country_list)))

		for i, day_file in enumerate(current_month_list):
			day_mat = np.load(f"./networks/{day_file}")

			# converting each zero file as nan
			month_matrix[i,:,:] = np.where(day_mat!=0, day_mat, np.nan) \
			 if excluding_zero_edge else day_mat

		# now averaging across slices
		month_matrix = np.nanmean(month_matrix, axis=0) if excluding_zero_edge \
			else np.mean(month_matrix, axis=0)

		# now saving monthly average:
		if excluding_zero_edge:
			np.nan_to_num(month_matrix, 0)

		print(f"Now saving for {self.date}")
		np.save(f"./timestepnet/{self.date}_network.npy", month_matrix)
