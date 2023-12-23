import os
import sys
import pandas as pd
from builder import *

""" 
The following is supposed to work as a python executable to download files from GDELT
project given a current date
"""

def perform_month(date, filepath_country_codes, filepath_masterfiles):
	"""
	Download all month's graphs gathered from GDELT project given:
	Args:
		date: (str) year+month in digits (like "202012" for Dec, 2020)
		filepath_country_codes: (str) path to file of the country code converter
		filepath_masterfiles: (str) path to file of the latest masterfile
	
	Example usage:
		python process_month.py "202012" ./country_codes_clean.csv ./masterfiles/2023XXXX_mf_filtered.txt"
	"""
	country_codes = pd.read_csv(filepath_country_codes, sep="\t")
	country_codes = country_codes[country_codes.Alpha3_code.notnull()].Alpha3_code.tolist()
	masterfiles = pd.read_csv(filepath_masterfiles, sep="\t", header=None)
	M = MonthEstimator(date, country_codes, masterfiles)
	M.process_month()


if __name__ == "__main__":

	print(sys.argv)
	if not len(sys.argv)==4:
		print("Example usage:\npython process_month.py \"202012\" ./country_codes_clean.csv ./masterfiles/2023XXXX_mf_filtered.txt")
		raise Exception
	date, filepath_country_codes, filepath_masterfiles = sys.argv[1],sys.argv[2],sys.argv[3]
	perform_month(date, filepath_country_codes, filepath_masterfiles)