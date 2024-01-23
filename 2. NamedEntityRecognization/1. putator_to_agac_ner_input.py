# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 30/01/2023 10:44
@Author: yao
"""

"""
该代码为Data_preprocessing.py多进程版本
将PubTator文件转换为任务一的Bio文件和Sent文件
"""

import argparse

import os
from multiprocessing import Manager, Process

import re
from collections import defaultdict

from nltk import word_tokenize, sent_tokenize

from nltk import tokenize


def get_sent_offset(doc: str):
    sent_list = tokenize.sent_tokenize(doc)
    sent_to_offset = {}
    sent_to_id = {}
    for sent in sent_list:
        begin = doc.find(sent)
        end = begin + len(sent)
        sent_to_offset[sent] = (begin, end)
        sent_to_id[sent] = len(sent_to_id)

    for sent, (begin, end) in sent_to_offset.items():
        if doc[begin: end]!= sent:
            print('Warning: Position calculation error.')
            print(doc)
            print(doc[begin: end], sent)
    return sent_to_offset, sent_to_id


def denotation_sent_map(denotation_set: set, sent_to_offset: dict):

    sent_to_denotation = defaultdict(set)

    for sentence, (s_start, s_end) in sent_to_offset.items():
        for (mention, _type, _id, (t_start, t_end)) in denotation_set:

            if t_start >= s_start and t_end <= s_end:
                # find token offset in sentence
                start = 0
                while 1:
                    new_t_start = sentence.find(mention, start)
                    if new_t_start == -1:
                        break
                    new_t_end = new_t_start + len(mention)

                    if sentence[new_t_start: new_t_end] != mention:
                        print('Warning: Position calculation error.')
                    sent_to_denotation[sentence].add((mention, _type, _id, (new_t_start, new_t_end)))
                    start = new_t_end
    return sent_to_denotation


def get_token_offset(sentence: str):
    token_to_offset = {}
    offset_to_token = {}
    start = 0
    for token in word_tokenize(sentence):

        token_start = sentence.find(token, start)
        token_end = token_start + len(token)
        start = token_end
        offset_to_token[(token_start, token_end)] = token
        token_to_offset[token] = (token_start, token_end)
    return token_to_offset, offset_to_token


def read_seth_tagging(tagging_file: str):
    print(f'Reading SETH tagging file.')
    pmid_to_tag = {}
    with open(tagging_file) as f:
        for line in f:
            l = line.strip().split('\t')
            # print(l)
            pmid = l[0]
            abstract = l[1]
            tagging_set = set(map(lambda x: eval(x), l[2:]))

            tagging_set_cp = tagging_set.copy()
            for seth_tag in tagging_set_cp:
                text, tag_type, (start, end) = seth_tag
                if text != abstract[int(start): int(end)]:
                    tagging_set.remove(seth_tag)
                    # delete those tagging
                    # ('Val717 to Lys', 'SUBSTITUTION', ('509', '532'))
                    # Val717 to Lys, Ser, Glu
            pmid_to_tag[pmid] = tagging_set
            continue

    return pmid_to_tag


def if_overlap(offset_1: tuple, offset_2: tuple):
    m_start, m_end = offset_1
    p_start, p_end = offset_2

    m_start, m_end = int(m_start), int(m_end)
    p_start, p_end = int(p_start), int(p_end)
    # m in p
    if m_start >= p_start and m_end <= p_end:
        return True
    # p in m
    if p_start >= m_start and p_end <= m_end:
        return True
    # m cross p and m is in front of p
    if m_start <= p_start and (p_start <= m_end <= p_end):
        return True
    # p cross m and p is in front of m
    if p_start <= m_start and (m_start <= p_end <= m_end):
        return True
    return False


def seth_pubtator_tagging_merge(seth_tag_set: set, pubtator_tagging_set: str):
    merged_tag_set = set()

    for seth_tag in seth_tag_set:
        tag, tag_type, (start, end) = seth_tag
        merged_tag_set.add((tag, tag_type, 'None', (int(start), int(end))))

    merged_tag_set_cp = merged_tag_set.copy()
    for pubtator_tag in pubtator_tagging_set:
        p_tag, p_type, p_id, p_offset = pubtator_tag
        save_flag = True
        for seth_tag in merged_tag_set_cp:
            s_tag, s_type, _, s_offset = seth_tag
            # total same, keep pubtator tagging for mutation id
            if p_offset == s_offset:
                merged_tag_set.remove(seth_tag)
                merged_tag_set.add(pubtator_tag)
                break
            if if_overlap(p_offset, s_offset):
                save_flag = False
        if save_flag:
            merged_tag_set.add(pubtator_tag)
    return merged_tag_set

def single_pubtator_part_process(pubtator_part: str, pmid_to_seth_tag: dict,
                                 bio_result: list, sent_result: list):
    """
    输入为部分地pubtator文档 根据\n\n分割 又用\n\n拼接
    """

    doc = ''
    sent_to_idx = {}
    processed_count = 0
    denotation_set = set()
    skip_count = 0
    pmid = ''
    for line in pubtator_part.split('\n'):
        l = line.strip()
        if '|t|' in l or '|a|' in l:
            pmid, text_type, text = l.split('|')
            if text_type == 't':
                processed_count += 1
                doc = ''
                doc += text

                if processed_count % 500 == 0:
                    print(f'{processed_count} pubtator processed.')

            elif text_type == 'a':
                doc += f' {text}'
            continue
        l_split = l.split('\t')
        if l_split == [ '' ]:

            sent_to_offset, sent_to_id = get_sent_offset(doc)

            if pmid_to_seth_tag.get(pmid):
                denotation_set = seth_pubtator_tagging_merge(pmid_to_seth_tag[ pmid ], denotation_set)

            sent_to_denotation = denotation_sent_map(denotation_set, sent_to_offset)
            for sentence, denotation_set in sent_to_denotation.items():

                if sent_to_idx.get(sentence):
                    sentence_idx = sent_to_idx[ sentence ]
                else:
                    sentence_idx = len(sent_to_idx)
                    sent_to_idx[ sentence ] = sentence_idx

                wf_denotation = '\t'.join(map(str, denotation_set))
                # wf_sent.write(f'{sentence_idx}\t{pmid}\t{sentence}\t{wf_denotation}\n')
                sent_result.append(f'{sentence_idx}\t{pmid}\t{sentence}\t{wf_denotation}\n')
                token_offset, offset_to_token = get_token_offset(sentence)
                # for token, (t_start, t_end) in token_offset.items():
                for (t_start, t_end), token in offset_to_token.items():
                    save_flag = False
                    for mention, _type, _id, (d_start, d_end) in denotation_set:
                        if t_start >= d_start and t_end <= d_end:
                            save_flag = True
                            # wf.write(f'{sentence_idx}\t{pmid}\t{token}\t{_type}\t{_id}\n')
                            bio_result.append(f'{sentence_idx}\t{pmid}\t{token}\t{_type}\t{_id}\n')
                    if not save_flag:
                        # wf.write(f'{sentence_idx}\t{pmid}\t{token}\tO\tNone\n')
                        bio_result.append(f'{sentence_idx}\t{pmid}\t{token}\tO\tNone\n')

                # wf.write('\n')
                bio_result.append('\n')

            denotation_set = set()
        else:
            try:
                try:
                    _, start, end, mention, _type, _id = l_split
                except:
                    _, start, end, mention, _type = l_split
                    _id = 'None'
            except:
                continue

            start, end = int(start), int(end)

            # check the denotation
            if doc[ int(start): int(end) ] != mention:
                skip_count += 1
                if doc.find(mention) != -1:
                    denotation_set.add((mention, _type, _id, (doc.find(mention), doc.find(mention) + len(mention))))
            else:
                denotation_set.add((mention, _type, _id, (start, end)))
                # input()
    return bio_result, sent_result


def pubtator_to_bio_multi_process(pubtator_file: str, output_path: str,
                                  seth_file: str, prefix: str= 'pubtator',
                                  process_num:int=10):
    bio_save_file = os.path.join(output_path, f'{prefix}.bio.txt')
    sent_save_file = os.path.join(output_path, f'{prefix}.sent.txt')

    if not seth_file is None:
        pmid_to_seth_tag = read_seth_tagging(seth_file)
    else:
        pmid_to_seth_tag = {}

    print(f'Reading PubTator file.')
    docs_list = open(pubtator_file).read().split('\n\n')

    # todo: add multi process
    with Manager() as manager:
        bio_result = manager.list()
        sent_result = manager.list()

        process_list = []
        for i in range(process_num):

            batch_data = docs_list[i::process_num]
            process = Process(target=single_pubtator_part_process,
                             args=('\n\n'.join(batch_data), pmid_to_seth_tag,
                                   bio_result, sent_result))
            process.start()
            process_list.append(process)
            print(f'Process {i + 1} started, batch: {len(batch_data):,}.')

        for process in process_list:
            process.join()

        with open(bio_save_file, 'w') as wf:
            for line in bio_result:
                wf.write(line)

        with open(sent_save_file, 'w') as wf:
            for line in sent_result:
                wf.write(line)

        print(f'{bio_save_file} and {sent_save_file} saved.')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='PubTator and SETH 2 Bio format.')
    parser.add_argument('-p', dest='pubtator_file', required=True)
    parser.add_argument('-e', dest='seth_tagging_file', required=False,
                        default=None,
                        help='default: None')
    parser.add_argument('-s', dest='save_path', default='../data/tagging_file',
                        help='default: ../data/tagging_file')
    parser.add_argument('-f', dest='save_prefix', default='ad',
                        help='default: ad')
    parser.add_argument('-pn', dest='process_num', default=10, type=int)
    args = parser.parse_args()

    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)


    # ad_pubtator_file = '../data/pubtator_file/ad.pubtator_central.txt'
    # ad_pubtator_file = '../data/pubtator_file/AlzheimerDisease.pubtator.txt'
    #
    # save_path = '../data/pubtator_file'
    # save_prefix = 'AlzheimerDisease.pmc'#
    # seth_tagging_file = '../data/pubtator_file/ad.seth.pmc.txt'

    # pubtator_to_bio(ad_pubtator_file, save_path, seth_tagging_file, save_prefix)
    pubtator_to_bio_multi_process(args.pubtator_file, args.save_path,
                    args.seth_tagging_file, args.save_prefix,
                    args.process_num)



