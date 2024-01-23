# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 27/05/2022 9:52
@Author: XINZHI YAO
"""

import os
import re
import argparse

from collections import defaultdict


def read_oger_file(oger_file: str, save_origin: list=['Gene Ontology']):
    tag_set = set()
    with open(oger_file) as f:
        f.readline()
        for line in f:
            l = line.strip().split('\t')

            tag_type = l[ 0 ]
            start = l[ 1 ]
            end = l[ 2 ]
            mention = l[ 3 ]
            preferred = l[ 4 ]
            entity_id = l[ 5 ]
            zone = l[ 6 ]
            origin = l[ 8 ]
            umls_cui = l[ 9 ]

            if origin in save_origin:
                # print(tag_type, mention, preferred, entity_id, origin, umls_cui)

                # print(mention, preferred, entity_id)
                tag_set.add((mention, preferred, tag_type, entity_id, (start, end)))
    return tag_set

def read_sent_file(sent_file: str):
    sent_set = set()
    with open(sent_file) as f:
        for line in f:
            l = line.strip().split('\t')
            sent_id, pmid, sentence = l[ 0 ], l[ 1 ], l[ 2 ]

            sent_set.add((sent_id, pmid, sentence))
    return sent_set

def result_process(sent_file: str, sent_tagging_path: str, save_file: str):
    pmid_to_tag = defaultdict(set)

    sent_set = read_sent_file(sent_file)

    save_id_type = False

    miss_count = 0
    with open(save_file, 'w') as wf:
        for (sent_id, pmid, sentence) in sent_set:
            tag_file = f'{sent_tagging_path}/oger.{sent_id}.tsv.txt'
            if os.path.exists(tag_file):
                tag_result = read_oger_file(tag_file)
                if not save_id_type:
                    sent_id = sent_id.split(':')[ 1 ]
                if tag_result:
                    pmid_to_tag[ pmid ].update(tag_result)
                    tag = str(tag_result)
                    wf.write(f'{sent_id}\t{pmid}\t{sentence}\t{tag}\n')
            else:
                miss_count += 1
    print(f'{save_file} save done.')


def main():

    parser = argparse.ArgumentParser(description='OGER result process.')
    parser.add_argument('--sent_file', dest='sent_file',
                        required=True)
    parser.add_argument('--sent_tagging_path', dest='sent_tagging_path',
                        required=True)
    parser.add_argument('--save_file', dest='save_file',
                        required=True)
    args = parser.parse_args()


    result_process(args.sent_file, args.sent_tagging_path, args.save_file)



if __name__ == '__main__':
    main()



