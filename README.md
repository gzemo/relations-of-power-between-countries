# Addressing the Mutual Relation of Power Between Countries with GDELT data

The current work address an the mutual influence between most influencial countries in the worldwide scenario. This is part of the M.Sc. Computational Social Science final project (University of Trento, a.y. 2023/2024) 

---

## Context
Social Science research is currently living an un-precedented golden era due to the availability of maintained high quality open platforms that allows to exploit massive historical data to shed lights on nowadays existing assets between communities of countries. The present work provides an evaluation on events data to detect whether the leading role of the most influential countries over the past 5 years can be predicted by competitors and allied changes in centrality by implementing a community detection approach and a graph-based measure time
series analysis.

---

## Project description
The current project aims at unravelling the past 5 years information on worldwide event and foreign policy exchange in order to map inter-state relationships as fully connected graphs to further address how the most central actors had mutually influenced themselves through time in their community of interest. By doing so, a community detection approach has been set to take trace of the emerging cluster of countries whose exchange pattern had been found to be more segregated for further investigate the mutual influence of the leading communities’ nodes over time.

Full report available at: [report](https://github.com/gzemo/relations-of-power-between-countries/blob/main/report.pdf)

---

## Data
GDELT project: https://www.gdeltproject.org/

---

## Example usage:

Install requirements: 
```shell
pip install -r requirements.txt
```

To download the monthly averaged graph representing the mutual relationship between countries you need to run in a dedicated shell specifing the month (in a YYYYMM string format), the csv of country codes and the masterfile which stores the complete list of 15 mins updated over the period under examination.

```shell
python process_month.py "202012" ./country_codes_clean.csv ./masterfiles/20230808_mf_filtered.txt
```
The resulting month graph will be saved in `timestepnet` (already provided).

A more stable and reliable way of downloading data from the GDELT project you may want to directly use the python `gdeltPyR` library: https://linwoodc3.github.io/gdeltPyR/

---

# Credits:
- *GDELT event data 2.0*: https://www.gdeltproject.org/about.html#termsofuse
- *CAMEO code*: Schrodt, P. A., Yilmaz, O., Gerner, D. J., & Hermreck, D. (2008, March). The CAMEO (conflict and mediation event observations) actor coding framework. In 2008 Annual Meeting of the International Studies Association. CC-BY-NC-SA-3.0
- *Countries ISO code*: Wikipedia® https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
