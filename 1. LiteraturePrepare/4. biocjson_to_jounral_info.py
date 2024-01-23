# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 05/06/2023 17:07
@Author: yao
"""

import argparse

import os
from multiprocessing import Manager, Process

"""
改代码从biocson文件中提取pmid-期刊信息
并保存为tsv文件
"""

def BiocJson_to_journal(lines: list, pmid_to_journal_dict: dict):

    _id_set = set()
    # wf = open(save_file, 'w', encoding='utf-8')

    null = 'null'
    # with open(json_file) as f:
    for line in lines:

        doc = eval(line.strip())

        pmid = doc[ 'pmid' ]
        pmcid = doc['pmcid'] if doc['pmcid'] else '-'
        journal = doc['journal']
        year = doc['year']
        # authors = doc['authors']

        pmid_to_journal_dict[pmid] = (pmid, pmcid, journal, year)

def batch_bioc_to_jounral_info(json_path: str, save_file: str, process_num: int):
    # single_file = False
    if os.path.isdir(json_path):
        file_list = os.listdir(json_path)
    else:
        file_list = [ json_path ]

    pmid_journal_dict = {}
    for _file in file_list:

        if os.path.isdir(_file):
            continue

        if not _file.endswith('pmc.txt') and not _file.endswith('pmid.txt'):
            continue

        print(f'"{_file}" Start to process.')
        # if not single_file:
        file_path = os.path.join(json_path, _file)

        with open(file_path, 'r') as f:
            lines = f.readlines()
        with Manager() as manager:
            pmid_to_journal = manager.dict()

            process_list = []
            for i in range(process_num):

                batch_data = lines[i::process_num]
                process = Process(target=BiocJson_to_journal,
                                  args=(batch_data, pmid_to_journal))
                process.start()
                process_list.append(process)
                print(f'PMC Process {i+1} started, batch: {len(batch_data):,}.')

            for process in process_list:
                process.join()
            print(f'pmid_to_journal: {len(pmid_to_journal):,}')

            pmid_journal_dict = pmid_to_journal.copy()

    # save pmid-journal_info tsv file
    with open(save_file, 'w') as wf:
        wf.write('PMID\tPMCID\tJournal\tYear\n')
        for pmid, journal_info in pmid_journal_dict.items():
            pmid, pmcid, journal, year = journal_info
            wf.write(f'{pmid}\t{pmcid}\t'
                     f'{journal}\t{year}\n')
    print(f'{len(pmid_journal_dict):,} pmid-journal saved in {save_file}.')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='BioJson to PubTator.')
    parser.add_argument('-b', dest='biocjson_path', default='../data/AlzheimerDisease_BiocJson',
                        help='bioc_info folder of pubtator file.')
    parser.add_argument('-sf', dest='save_file', required=True)

    parser.add_argument('-pn', dest='process_num', default=8, type=int)

    args = parser.parse_args()

    batch_bioc_to_jounral_info(args.biocjson_path, args.save_file, args.process_num)



