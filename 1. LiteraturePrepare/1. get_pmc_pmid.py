# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 10/05/2023 09:09
@Author: yao
"""

"""
2023-05-10 updated version for ID-Get-code
"""
import os
import re

import json
import requests

import argparse
from collections import defaultdict

import datetime

def read_keyword(keyword_file: str):
    # only one row
    # keyword1 syno1 syno2 syno3 ....
    # treat keyword1 as the save file name

    name_to_syno = defaultdict(set)
    with open(keyword_file) as f:
        for line in f:
            # l = line.strip().split('\t')
            # fixme: read keyword file
            l = line.strip().split(' ')
            name = l[0]
            name_to_syno[name].update([keyword.strip() for keyword in l if keyword])

    print(f'{len(name_to_syno.keys()):,} groups of keyword.')
    for keyword, syno_set in name_to_syno.items():
        print(f'Keyword: {keyword}\nSyno: \t{syno_set}.')
    print()
    return name_to_syno


def get_ids_for_single_keyword(query: str, db: str, start_year: str,
                               end_year: str):
    try:
        import xml.etree.cElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET

    query = query.replace(' ', '+')
    batch_size = 5000
    id_set = set()
    base = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    # get the total number of query result
    url = base + "esearch.fcgi?db=" + db + "&term=" + query \
          + f'+{start_year}[pdat]' + f'+{end_year}[pdat]' \
          + "&retmode=json"
    re = requests.get(url)
    result = json.loads(re.text)
    total = result["esearchresult"]["count"]
    iternum = int(int(total) / batch_size) + 1
    # add year limitation
    for i in range(iternum):
        retstart = 1 + batch_size * i
        # url = base + "esearch.fcgi?db=" + db + "&term=" + query + "&retmode=json" + "&retmax=100000"
        url = base + "esearch.fcgi?db=" + db + "&term=" + query \
              + f'+{start_year}[pdat]' + f'+{end_year}[pdat]' \
              + "&retmode=json" + f"&retmax={batch_size}" + f"&retstart={retstart}"
        re = requests.get(url)
        print(re)
        result = json.loads(re.text)
        idlist = result["esearchresult"]["idlist"]

        print(idlist)
        print(len(idlist))
        input()
        id_set.update(idlist)
        print(f'iter: {i}/{iternum}: updated: {len(id_set):,}/{int(total):,}')

    if db == 'pmc':
        id_set = {f'PMC{_id}' for _id in id_set}

    return id_set


def bulk_get_id(keyword_file, save_path, start_year=2008, last_year=''):

    if not os.path.exists(save_path):
        os.mkdir(save_path)

    if not last_year:
        # current year int
        now = datetime.datetime.now()
        last_year = now.year
    year_range = list(range(start_year, last_year))

    keyword_to_syno = read_keyword(keyword_file)

    prefix = keyword_file.split('.')[0]

    print(f'Year range: {start_year}-{last_year}')
    # only one group for keyword file.
    # means only one row in keyword file.
    pmid_set = set()
    pmc_set = set()
    for keyword, syno_set in keyword_to_syno.items():
        print(f'Processing keyword: {keyword}')
        # each year once, ensure the download number under the limitation
        for year in year_range:
            for syno in syno_set:
                print(f'Processing syno: {syno}, year: {year}-{year}')
                syno_pmid_set = get_ids_for_single_keyword(syno, 'pubmed', year, year)
                syno_pmc_set = get_ids_for_single_keyword(syno, 'pmc', year, year)

                pmid_set.update(syno_pmid_set)
                pmc_set.update(syno_pmc_set)


    pmid_save_file = f'{save_path}/{prefix}.pmid.txt'
    pmc_save_file = f'{save_path}/{prefix}.pmc.txt'
    with open(pmid_save_file, 'w') as wf:
        for pmid in pmid_set:
            wf.write(f'{pmid}\n')

    with open(pmc_save_file, 'w') as wf:
        for pmc in pmc_set:
            wf.write(f'{pmc}\n')

    print(f'{pmid_save_file} saved {len(pmid_set):,} pmids.')
    print(f'{pmc_save_file} saved {len(pmc_set):,} pmcs.')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Lit-GWAS Bayes model.')

    parser.add_argument('-kf', dest='keyword_file',
                        default='../data/APOE_dir/APOE.keyword.txt',
                        help='default: ../data/APOE_dir/APOE.keyword.txt')

    parser.add_argument('-sp', dest='id_save_path',
                        default='../data/APOE_dir/APOE_id_info',
                        help='default: ../data/APOE_dir/APOE_id_info')

    parser.add_argument('-sy', dest='start_year',
                        type=int, default=2008)
    parser.add_argument('-ey', dest='end_year',
                        type=int, default=0)


    args = parser.parse_args()

    print('get id')
    bulk_get_id(args.keyword_file, args.id_save_path, args.start_year, args.end_year)
