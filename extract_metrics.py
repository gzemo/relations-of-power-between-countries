import os
import sys
import pandas as pd
from graph import YearManager

def extract_year_metrics(year, filepath_country_codes):
	"""
	After having all daily events extracted and processed into single days graph
	this function computes the montly metrics and generates the global/nodal csv in which 
	results are stored in the "graph_record" folder.
	Args:
		year: (str) years in digits (ex: "2021")
	"""
	country_codes = pd.read_csv(filepath_country_codes, sep="\t")
	country_codes = country_codes[country_codes.Alpha3_code.notnull()].Alpha3_code.tolist()
	y = YearManager(str(year), country_codes)
	y.estimate_metrics()
	y.into_dataframe()


if __name__ == "__main__":

	print(sys.argv)
	if not len(sys.argv)==3:
		print("Example usage:\npython process_month.py \"202012\" ./country_codes_clean.csv")
		raise Exception
	date, filepath_country_codes = sys.argv[1],sys.argv[2]
	extract_year_metrics(date, filepath_country_codes)