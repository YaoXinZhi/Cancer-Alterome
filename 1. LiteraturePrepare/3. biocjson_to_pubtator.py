# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 23/01/2023 23:27
@Author: yao
"""

import argparse

import os
from multiprocessing import Manager, Process

import re
from collections import defaultdict


"""
该代码只把biocjson格式转换为pubtator
不做关键词筛选等操作
该代码实现了多线程标注
"""

def annotation_parser(annotations:dict):

    annotation_set = set()
    for ann in annotations:
        ann_type = ann[ 'infons' ][ 'type' ]
        ann_id = ann[ 'infons' ][ 'identifier' ] if ann[ 'infons' ][ 'identifier' ] else 'None'
        ann_text = ann[ 'text' ]
        ann_start = ann[ 'locations' ][ 0 ][ 'offset' ]
        ann_end = ann_start + ann[ 'locations' ][ 0 ][ 'length' ]
        ann_offset = (ann_start, ann_end)
        annotation_set.add((ann_offset, ann_text, ann_type, ann_id))
    return annotation_set

def get_offset(doc: str, annotation_set: set, search_start:int=0):
    """
    ((ann_start, ann_end), ann_text, ann_type, ann_id)
    """

    annotation_off_set = set()
    for (_, ann_text, ann_type, ann_id) in annotation_set:
        start = search_start
        while True:

            ann_start = doc.find(ann_text, start)

            if ann_start == -1:
                break

            ann_end = ann_start + len(ann_text)
            start = ann_end

            annotation_off_set.add(((ann_start, ann_end), ann_text, ann_type, ann_id))

    return annotation_off_set


def keyword_count(doc: str, keyword_set: set, lower: bool):

    if lower:
        doc = doc.lower()
        keyword_set = set(map(lambda x:x.lower(), keyword_set))

    count = 0
    for _key in keyword_set:
        count += len(re.findall(r'\b{0}\b'.format(_key), doc))

    return count

def if_including(offset_1: tuple, offset_2: tuple):

    start_1, end_1 = offset_1
    start_2, end_2 = offset_2

    if start_1 >= start_2 and end_1 <= end_2:
        return True
    return False

def if_overlapping(offset_1: tuple, offset_2: tuple):

    start_1, end_1 = offset_1
    start_2, end_2 = offset_2

    if end_1 == start_2:
        return True
    return False

def pmc_annotation_combine(annotation_set: set):

    ann_cp_set = annotation_set.copy()
    for ann_1 in ann_cp_set:
        offset_1, ann_text1, ann_type1, ann_id1 = ann_1
        for ann_2 in ann_cp_set:

            if ann_1 == ann_2:
                continue

            offset_2, ann_text2, ann_type2, ann_id2 = ann_2

            if if_overlapping(offset_1, offset_2):
                if ann_1 in annotation_set:
                    annotation_set.remove(ann_1)
                if ann_2 in annotation_set:
                    annotation_set.remove(ann_2)
                break

            if if_including(offset_1, offset_2):
                if ann_1 in annotation_set:
                    annotation_set.remove(ann_1)
                break
    return annotation_set


def read_key_syno(syno_file: str):
    syno_dic = defaultdict(set)

    with open(syno_file) as f:
        for line in f:
            l = line.strip().split('\t')
            syno_dic[l[0]].update(l)

            for _key in l:
                if 'carcinoma' in _key.lower().split(' '):
                    syno_dic[l[0]].add(_key.lower().replace('carcinoma', 'cancer'))

    return syno_dic


def BiocJson_convert_pmc(lines: list, convert_result: list):
    null = 'None'
    _id_set = set()

    line_count = 0
    filter_doc = set()
    for line in lines:

        convert_line = ''

        line_count += 1
        if line_count % 100 == 0:
            print(line_count)

        doc = eval(line.strip())

        pmid = doc[ 'pmid' ]
        _id_set.add(pmid)

        title = ''
        text = ''
        body = ''
        title_annotation_set = set()
        body_annotation_set = set()

        save_block = {'abstract', 'paragraph'}
        for info in doc[ 'passages' ]:
            block_type = info['infons']['type']
            if block_type == 'front':
                title = info['text']
                text = title
                title_annotation_set.update(annotation_parser(info['annotations']))
            elif block_type in save_block:
                text += ' '
                text += info['text']
                body += ' '
                body += info['text']
                body_annotation_set.update(annotation_parser(info['annotations']))
                # annotation_set.update(annotation_parser(info['annotations']))
            else:
                continue

        # if len(body_annotation_set) > 5000:
        #     continue

        body_annotation_set = get_offset(text, body_annotation_set,
                                         search_start=len(title)-1)


        # wf.write(f'{pmid}|t|{title}\n')
        # wf.write(f'{pmid}|a|{body.strip()}\n')

        convert_line += f'{pmid}|t|{title}\n'
        convert_line += f'{pmid}|a|{body.strip()}\n'

        body_annotation_set = pmc_annotation_combine(body_annotation_set)

        annotation_set = title_annotation_set | body_annotation_set

        sorted_ann = sorted(annotation_set, key=lambda x: x[0][0])

        for ((ann_start, ann_end), ann_text, ann_type, ann_id) in sorted_ann:
            # if text[ann_start: ann_end] != ann_text:
            #     # offset check
            #     print(f'{text[ann_start: ann_end]}, {ann_text}, {ann_type}')
            #     print('wrong offset.')
            #     input()
            # wf.write(f'{pmid}\t{ann_start}\t{ann_end}\t'
            #          f'{ann_text}\t{ann_type}\t{ann_id}\n')

            convert_line += f'{pmid}\t{ann_start}\t{ann_end}\t{ann_text}\t{ann_type}\t{ann_id}\n'


        # wf.write('\n')
        convert_line += '\n'

        convert_result.append(convert_line)



def BiocJson_convert_pubmed(lines: list, convert_result: list):

    _id_set = set()
    # wf = open(save_file, 'w', encoding='utf-8')

    null = 'null'
    # with open(json_file) as f:
    for line in lines:
        convert_line = ''

        title = ''
        abstract = ''
        annotation_set = set()
        doc = eval(line.strip())

        pmid = doc['pmid']
        _id_set.add(pmid)

        for info in doc['passages']:
            if info['infons']['type'] == 'title':
                title = info['text']
                annotation_set.update(annotation_parser(info['annotations']))
            elif info['infons']['type'] == 'abstract':
                abstract = info['text']
                annotation_set.update(annotation_parser(info['annotations']))
            else:
                print(info['infons'])
                exit()

        # wf.write(f'{pmid}|t|{title}\n')
        # wf.write(f'{pmid}|a|{abstract}\n')

        convert_line += f'{pmid}|t|{title}\n'
        convert_line += f'{pmid}|a|{abstract}\n'

        sorted_ann = sorted(annotation_set, key=lambda x: x[0][0])
        for ((ann_start, ann_end), ann_text, ann_type, ann_id) in sorted_ann:
            # wf.write(f'{pmid}\t{ann_start}\t{ann_end}\t'
            #          f'{ann_text}\t{ann_type}\t{ann_id}\n')

            convert_line += f'{pmid}\t{ann_start}\t{ann_end}\t{ann_text}\t{ann_type}\t{ann_id}\n'


        # wf.write('\n')
        convert_line += '\n'

        convert_result.append(convert_line)



def batch_BiocJson_convert(json_path: str, save_path: str, process_num: int):
    # single_file = False
    if os.path.isdir(json_path):
        file_list = os.listdir(json_path)
    else:
        file_list = [json_path]
        # single_file = True
    prefix = ''
    save_file_list = []
    for _file in file_list:
        print(f'{_file} Start to process.')
        # if not single_file:
        file_path = os.path.join(json_path, _file)
        prefix = _file.split('.')[0]

        if _file.endswith('pmc.txt'):
            suffix = 'pmc'
            pmc_format = True
        elif _file.endswith('pmid.txt'):
            suffix = 'pmid'
            pmc_format = False
        else:
            print(f'wrong file name: {_file}')
            print(f'pleases endswith "pmid.txt" or "pmc.txt".')
            continue
            # raise ValueError(f'_file is PMCID or PMID?')

        save_file = f'{save_path}/{prefix}.pubtator.{suffix}.txt'
        #  multi process
        with open(file_path, 'r') as f:
            lines = f.readlines()
        if pmc_format:
            with Manager() as manager:
                pmc_convert_result = manager.list()

                process_list = []
                for i in range(process_num):

                    batch_data = lines[i::process_num]
                    process = Process(target=BiocJson_convert_pmc,
                                      args=(batch_data, pmc_convert_result))
                    process.start()
                    process_list.append(process)
                    print(f'PMC Process {i+1} started, batch: {len(batch_data):,}.')

                for process in process_list:
                    process.join()

                with open(save_file, 'w') as wf:
                    for convert_line in pmc_convert_result:
                        wf.write(f'{convert_line}')
                print(f'{save_file} saved.')
                save_file_list.append(save_file)

            #save_file = f'{save_path}/{prefix}.pubtator.pmc.txt'
            # BiocJson_convert_pmc(file_path, save_file,)
        else:
            with Manager() as manager:
                pmid_convert_result = manager.list()

                process_list = []
                for i in range(process_num):

                    process = Process(target=BiocJson_convert_pubmed,
                                      args=(lines[i::process_num], pmid_convert_result))
                    process.start()
                    process_list.append(process)
                    print(f'PMID Process {i+1} started.')

                for process in process_list:
                    process.join()
                print('All process completed.')

                with open(save_file, 'w') as wf:
                    for convert_line in pmid_convert_result:
                        wf.write(f'{convert_line}')
                print(f'{save_file} saved.')
                save_file_list.append(save_file)

    if len(save_file_list) == 2:
        cat_file = f'{save_path}/{prefix}.pubtator.pmid-pmc.txt'

        # 连接两个文件 并在中间加一个空行
        cat_commend = f'cat {save_file_list[0]} {save_file_list[1]} | sed G > {cat_file}'
        print(cat_commend)
        os.system(cat_commend)
        print(f'connected file: {cat_file} saved.')



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='BioJson to PubTator.')
    parser.add_argument('-b', dest='biocjson_path', default='../data/AlzheimerDisease_BiocJson',
                        help='default: ../data/AlzheimerDisease_BiocJson')
    parser.add_argument('-s', dest='save_path', default='../data/pubtator_info',
                        help='default: ../data/pubtator_info')

    parser.add_argument('-pn', dest='process_num', default=8, type=int)

    args = parser.parse_args()

    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)

    batch_BiocJson_convert(args.biocjson_path, args.save_path, args.process_num)


