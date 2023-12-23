import os
import datetime

"""
This class is aimed at having a Masterfile retriever in which the needed 
dates for the corresponding GDELT csv link is handled

Example usage for retrieving all past information up to the latest presented
master = MasterfileRetriever(
			start_date = "2017010100",
		)

"""

class MasterfileRetriever():

	def __init__(self, start_date, end_date=None):
		"""
		start_date: (str) in the format YYMMDDDD, initial date
		end_date: (str) (default: None = Current Date) 
		"""
		assert int(start_date) > 20150301, "No data available for that period"
		self.start_date = start_date
		if not end_date:
			curr_date = datetime.datetime.now()
			year  = str(curr_date.year)
			month = str(curr_date.month) if curr_date.month>10 else '0'+str(curr_date.month)
			day   =	str(curr_date.day) if curr_date.day>10 else '0'+str(curr_date.day)
			self.end_date = f"{year}{month}{day}"
		else:
			self.end_date = end_date
		self.gdelt_url = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
		self.filename = None

	def _retrieve(self):
		"""
		Retrieve the whole masterfile and save into a txt into ./masterfiles
		"""
		self.filename = f"./masterfiles/{self.end_date}_mf.txt" 
		print(f"Retrieving and saving masterfiles into: {self.filename}")
		os.system(f"curl {self.gdelt_url} >> {self.filename}")


	def _filter_records(self):
		"""
		Filter the original complete list of GDELT Events 2.0 retaining
		only those records belonging to a certain date onwards.
		"""
		output = f"./masterfiles/{self.end_date}_mf_filtered.txt"
		print(output)
		print(f"Filtering records from: {self.filename}")

		to_save = []
		with open(self.filename, "r", encoding="utf-8") as f:
			found = False
			for record in f.readlines():
				record = record.strip()

				if record == "\n":
					continue
				curr_url = record.split(" ")[-1].strip()
				curr_date = curr_url.split("/")[-1].split(".")[0][0:8]
				condition = ("export" in curr_url) and (not "gkg" in curr_url or not "mentions" in curr_url)

				if (curr_date == self.start_date):
					found = True
				if found and condition:
					to_save.append(f"{str(curr_date)}\t{str(curr_url)}")

		os.system(f"touch {output}")
		print(f"Now saving into: {output}")
		with open(output, "w", encoding="utf-8") as f:
			for record in to_save:
				f.write(record)
				f.write("\n")

		print("Deleting raw list of entries...")
		os.system(f"rm {self.filename}")
		self.filename = output


	def call(self):
		"""
		Complete process
		"""
		self._retrieve()
		self._filter_records()