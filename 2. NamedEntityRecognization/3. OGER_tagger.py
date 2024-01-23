# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 09/11/2021 10:00
@Author: XINZHI YAO
"""

import os
import time
import shutil

import argparse


def read_tagging_file(tagging_file: str):

    sentence_set = set()
    with open(tagging_file) as f:
        for line in f:
            l = line.strip().split('\t')
            sentence_id = l[0]
            sentence = l[2]

            sentence_set.add((sentence, sentence_id))

    print(f'sentence count: {len(sentence_set):,}')
    return sentence_set


def read_id_file(id_file: str, id_col=1, head_line=True):

    id_set = set()

    with open(id_file) as f:
        if head_line:
            f.readline()
        for line in f:
            l = line.strip().split('\t')
            _id = l[id_col]
            _id_type = l[-1]
            id_set.add((_id, _id_type))
    print(f'id count: {len(id_set):,}')
    return id_set

def batch_sent_tagger(save_path: str, save_prefix: str,
                      sent_set: set, save_format: str,
                      delete_existed_file: bool):


    if os.path.exists(save_path) and delete_existed_file:
        shutil.rmtree(save_path)
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    start_time = time.time()
    for idx, (sent, sent_id) in enumerate(sent_set):

        if idx % 500 == 0:
            end_time = time.time()
            print(f'{idx} completed, cost: {end_time-start_time:.2f} s.')

        save_file = f'{save_path}/{save_prefix}.{sent_id}.{save_format}.txt'

        if os.path.exists(save_file) and (not delete_existed_file):
            continue

        commend_line = f'''curl --location \
                    --request POST 'https://oger.nlp.idsia.ch/upload/txt/{save_format}' \
                    --header 'Content-Type: text/plain' \
                    --data "{sent}" > {save_file} '''

        os.system(commend_line)

    end_time = time.time()
    print(f'Completed, cost: {end_time-start_time:.2f} s.')


def batch_fetch_tagger(save_path: str, save_prefix: str,
                       id_set: set, save_format='pubtator',
                       delete_existed_file=False):

    if not os.path.exists(save_path):
        os.mkdir(save_path)

    start_time = time.time()
    save_file = f'{save_path}/{save_prefix}.{save_format}.oger.txt'

    if os.path.exists(save_file):
        if delete_existed_file:
            os.remove(save_file)
        # while True:
            # remove_bool = input(f'{save_file} already existed, kill: Yes or No? \n')
            # if remove_bool == 'Yes':
            #     print('Delete file.')
            #     os.remove(save_file)
            #     break
            # elif remove_bool == 'No':
            #     print('Append write.')
            #     break
            # else:
            #     pass

    for idx, (_id, _id_type) in enumerate(id_set):

        if idx % 500 == 0:
            end_time = time.time()
            print(f'{idx} completed, cost: {end_time-start_time:.2f} s.')

        if _id_type == 'PMID':
            commend_line = f'curl https://oger.nlp.idsia.ch/fetch/pubmed/{save_format}/{_id} >> {save_file}'
        elif _id_type == 'PMC':
            commend_line = f'curl https://oger.nlp.idsia.ch/fetch/pmc/{save_format}/{_id} >> {save_file}'
        else:
            continue
            #raise ValueError(f'wrong id_type: {_id_type}.')

        os.system(commend_line)

        # empty line
        os.system(f'echo -e >> {save_file}')

    end_time = time.time()
    print(f'Completed, cost: {end_time-start_time:.2f} s.')


def main():


    parser = argparse.ArgumentParser(description='OGER tagger.')

    parser.add_argument('--tagger_mode', dest='tagger_mode', type=str,
                        default='id_tagger',
                        choices=['id_tagger', 'sent_tagger'],
                        help='default: id_tagger, choices: sent_tagger, id_tagger')

    parser.add_argument('--delete_existed_file', dest='delete_existed_file',
                        action='store_true', default=False,
                        help='delete_existed_file, default: False')

    parser.add_argument('--input_file', dest='input_file', type=str,
                        default='AlzheimerDisease.pmc-pmid.txt',
                        help='default: AlzheimerDisease.pmc-pmid.txt')

    parser.add_argument('--save_path', dest='save_path', type=str,
                        default='./output',
                        help='default: ./output')

    parser.add_argument('--save_prefix', dest='save_prefix', type=str,
                        default='AlzheimerDisease',
                        help='default: AlzheimerDisease')

    parser.add_argument('--save_format', dest='save_format',
                        choices=['tsv', 'pubtator'],
                        default='pubtator',
                        help='default: pubtator, choices: tsv, pubtator.')
    args = parser.parse_args()

    id_col = 1
    head_line = True

    if args.tagger_mode == 'id_tagger':
        id_set = read_id_file(args.input_file, id_col, head_line)
        batch_fetch_tagger(args.save_path, args.save_prefix, id_set, args.save_format, args.delete_existed_file)
    elif args.tagger_mode == 'sent_tagger':
        sent_set = read_tagging_file(args.input_file)
        batch_sent_tagger(args.save_path, args.save_prefix, sent_set, args.save_format, args.delete_existed_file)

if __name__ == '__main__':
    main()

