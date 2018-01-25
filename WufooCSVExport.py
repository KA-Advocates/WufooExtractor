#!/usr/bin/env python3
# coding: utf-8
import requests
from collections import namedtuple
import concurrent.futures
from requests.auth import HTTPBasicAuth
import csv
from tqdm import tqdm
import itertools
import xlsxwriter
from toolz.itertoolz import groupby
import operator
from concurrent.futures import ThreadPoolExecutor

with open("apikey.txt") as infile:
    auth = HTTPBasicAuth(infile.read().strip(), "")

forms = requests.get("https://khanacademy.wufoo.com/api/v3/forms.json", auth=auth).json()
theform = next(form for form in forms["Forms"] if form["Url"] == "khan-academy-translator-application")

# Get field ID => field mapping
fieldinfo = requests.get(theform["LinkFields"], auth=auth).json()
fieldTitleMap = {}
countryID = None
for field in fieldinfo["Fields"]:
    if "Page" in field or field["ID"] == 'DateCreated': # Not a meta entry
        if "SubFields" in field:
            for subfield in field["SubFields"]:
                fieldTitleMap[subfield["ID"]] = field["Title"].strip() + ' / ' + subfield["Label"].strip()
        else: # 
            fieldTitleMap[field["ID"]] = field["Title"].strip()
            if field["Title"] == "Native Language":
                countryID = field["ID"]

fieldlist = ["EntryId"] + sorted(list(fieldTitleMap.keys()))
# Add title map after to prevent duplicate EntryId
fieldTitleMap["EntryId"] = "Entry ID"
Entry = namedtuple("Entry", fieldlist)

def fetch_page(n):
    response = requests.get(theform["LinkEntries"], params={"pageSize": 100, "pageStart": n * 100},
                             auth=auth)
    entryInfo = response.json()
    return [Entry(*(try_parse_int(entry[field]) for field in fieldlist)) for entry in entryInfo["Entries"]]

def try_parse_int(s):
    if s is None:
        return None
    try: return int(s)
    except ValueError: return s

def tqdm_parallel_map(executor, fn, *iterables, **kwargs):
    """
    Equivalent to executor.map(fn, *iterables),
    but displays a tqdm-based progress bar.
    
    Does not support timeout or chunksize as executor.submit is used internally
    
    **kwargs is passed to tqdm.
    """
    futures_list = []
    for iterable in iterables:
        futures_list += [executor.submit(fn, i) for i in iterable]
    for f in tqdm(concurrent.futures.as_completed(futures_list), total=len(futures_list), **kwargs):
        yield f.result()
        
nentries = int(requests.get("https://khanacademy.wufoo.com/api/v3/forms/zysv1sm1k64lf6/entries/count.json", auth=auth).json()["EntryCount"])
npages = int((nentries*1.2)//100)

with ThreadPoolExecutor(32) as executor:
    entries = list(itertools.chain(*tqdm_parallel_map(executor, fetch_page, range(npages))))
    
print("Found {} entries".format(len(entries)))

sortedEntries = sorted(set(entries), key=lambda e: e.EntryId)[::-1]

# Export CSV
header = [fieldTitleMap[field] for field in Entry._fields]
with open("wufoo.csv", "w") as outfile:
    writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    for entry in sortedEntries:
        writer.writerow(entry)

# Export XLSX
def xlsx_write_rows(filename, rows):
    """
    Write XLSX rows from an iterable of rows.
    Each row must be an iterable of writeable values.
    Returns the number of rows written
    """
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    # Write values
    nrows = 0
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            worksheet.write(i, j, val)
        nrows += 1
    # Cleanup
    workbook.close()
    return nrows

# Write complete XLSX
xlsx_write_rows("Wufoo.xlsx", [header] + sortedEntries)

# Write XLSX by lang
langGroups = groupby(lambda entry: entry._asdict()[countryID], sortedEntries)
for lang, entries in langGroups.items():
    print("Exporting {}".format(lang))
    xlsx_write_rows("Wufoo {}.xlsx".format(lang.replace("/", "-")), [header] + entries)

