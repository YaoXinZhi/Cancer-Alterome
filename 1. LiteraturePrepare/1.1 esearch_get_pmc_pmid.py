# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 10/05/2023 16:42
@Author: yao
"""

"""
改代码通过读取keyword文件 并批量使用esearch工具获取pmid和pmcid
"""

import os

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
            l = line.strip().split('\t')
            name = l[0]
            name_to_syno[name].update([keyword.strip() for keyword in l if keyword])

    print(f'{len(name_to_syno.keys()):,} groups of keyword.')
    for keyword, syno_set in name_to_syno.items():
        print(f'Keyword: {keyword}\nSyno: \t{syno_set}.')
    print()
    return name_to_syno

def commend_generation(keyword_file, id_save_path, start_year: int, last_year: int,
                       commend_save_file: str):

    # esearch -db pmc -query "cancer AND (2000[PDAT] 2000[PDAT])" | efetch -format uid > pmcid_2000.txt
    if not os.path.exists(id_save_path):
        os.mkdir(id_save_path)

    if not last_year:
        # current year int
        now = datetime.datetime.now()
        last_year = now.year
    year_range = list(range(start_year, last_year+1))

    print(f'year range: {year_range}')

    keyword_to_syno = read_keyword(keyword_file)

    commend_count = 0
    with open(commend_save_file, 'w') as wf:
        for keyword, syno_set in keyword_to_syno.items():

            for syno in syno_set:
                for year in year_range:
                    pmid_save_file = f'{os.path.abspath(id_save_path)}/{keyword}-{syno}-{year}.pmid.txt'
                    pmc_save_file = f'{os.path.abspath(id_save_path)}/{keyword}-{syno}-{year}.pmc.txt'

                    if os.path.exists(pmid_save_file):
                        print(f'Exists: {pmid_save_file}')
                    else:
                        pmid_commend = f'esearch -db pubmed -query "{syno} AND ({year}[PDAT] :{year}[PDAT])" | efetch -format uid > "{pmid_save_file}"'
                        wf.write(f'{pmid_commend}\n')
                        commend_count += 1

                    if os.path.exists(pmc_save_file):
                        print(f'Exist: {pmc_save_file}')
                    else:
                        pmc_commend = f'esearch -db pmc -query "{syno} AND ({year}[PDAT] :{year}[PDAT])" | efetch -format uid > "{pmc_save_file}"'
                        wf.write(f'{pmc_commend}\n')
                        commend_count += 1

    print(f'{commend_save_file} saved, total {commend_count:,} commends saved.')



if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-cf', dest='commend_save_file', required=True)

    parser.add_argument('-kf', dest='keyword_file',
                        default='../data/APOE_dir/APOE.keyword.txt',
                        help='default: ../data/APOE_dir/APOE.keyword.txt')

    parser.add_argument('-sp', dest='id_save_path',
                        default='../data/APOE_dir/APOE_id_info',
                        help='default: ../data/APOE_dir/APOE_id_info')

    parser.add_argument('-sy', dest='start_year',
                        type=int, default=2008,
                        help='default: 2008')
    parser.add_argument('-ey', dest='end_year',
                        type=int, default=0,
                        help='default: current year.')

    args = parser.parse_args()

    commend_generation(args.keyword_file, args.id_save_path, args.start_year, args.end_year, args.commend_save_file)
