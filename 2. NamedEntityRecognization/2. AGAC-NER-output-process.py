# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 11/05/2021 9:05
@Author: XINZHI YAO
"""

import os

import re
import argparse

from itertools import permutations

def read_sentence_to_idx(sentence_idx_file: str):

    idx2sentence = {}
    idx2tag = {}
    with open(sentence_idx_file) as f:
        f.readline()
        for line in f:
            l = line.strip().split('\t')
            idx, pmid, sentence = l[0], l[1], l[2]
            pubtator_tag = l[3:]
            tag_set = {eval(tag) for tag in pubtator_tag}
            idx2sentence[idx] = sentence
            idx2tag[idx] = tag_set

    return idx2sentence, idx2tag


def tag_process(data_list: list, label_list: list):
    """
    :param data_list: list of tokens.
    :param label_list: list of labels.
    :return: tag_set, sentence
    """
    sentence = ' '.join(data_list)

    start = 0
    tag_set = set()
    for idx, token in enumerate(data_list):

        token_start = sentence.find(token, start)
        token_end = token_start + len(token)
        start = token_end
        label = label_list[idx]
        if label == 'O' or label.startswith('I-'):
            continue
        if label.startswith('B-'):

            phrase_list = []
            offset_list = []
            tag = label.split('-')[1]
            phrase_list.append(token)
            offset_list.append((token_start, token_end))
            _start = 0
            for _idx, _token in enumerate(data_list[idx+1:]):

                _idx = _idx + idx + 1
                _label = label_list[_idx]

                if len(_label.split('-')) > 1:
                    _tag = _label.split('-')[1]
                else:
                    _tag = ''

                if _label == 'O' or _tag != tag:
                    phrase = ' '.join(phrase_list)
                    offset = (offset_list[0][0], offset_list[-1][1])
                    tag_set.add((phrase, tag, offset))
                    break

                _token_start = sentence.find(_token, _start)
                _token_end = _token_start + len(_token)
                phrase_list.append(_token)
                offset_list.append((_token_start, _token_end))
    return tag_set, sentence



def tag_process_pubtator(data_list: list, label_list: list, sentence: str):

    if len(data_list) != len(label_list):
        raise ValueError('Difference length.')

    data_pointer = -1
    model_tag_set = set()
    for token_info, label in zip(data_list, label_list):
        token, pub_tag, tag_id, (token_start, token_end) = token_info
        data_pointer += 1

        if pub_tag == 'O' and label == 'O':
            continue

        # some label start with 'I-', but it's correct.
        # label start with 'B-'
        if label.startswith('B-'):
            label_class = label.split('-')[1]
            temp_phrase = [token]
            temp_offset = [(token_start, token_end)]

            for _token_info, _label in zip(data_list[data_pointer:], label_list[data_pointer:]):
                _token, _, _, (token_start, token_end) = _token_info

                if _label == 'O':
                    offset = (temp_offset[0][0], temp_offset[-1][1])
                    # sentence(offset)
                    # model_tag_set.add((' '.join(temp_phrase), label_class, offset))
                    model_tag_set.add((sentence[offset[0]: offset[1]], label_class, offset))
                    break

                _label_class = _label.split('-')[1]
                # word-piece
                if _token == token and label_class == _label_class:
                    continue
                # offset
                if _token != token and _token != temp_phrase[-1]:
                    if _label_class == label_class:
                        temp_phrase.append(_token)
                        temp_offset.append((token_start, token_end))
                    else:
                        offset = (temp_offset[ 0 ][ 0 ], temp_offset[ -1 ][ 1 ])
                        # model_tag_set.add((' '.join(temp_phrase), label_class, offset))
                        model_tag_set.add((sentence[offset[0]: offset[1]], label_class, offset))
                        break


    return model_tag_set

def re_in(token_1, token_2):

    if re.findall(r'\b{0}\b'.format(token_1), token_2):
        return True
    else:
        return False

# Integrate fully nested entities
def tagging_merge(pubtator_set: set, model_tag_set: set):

    pubtator_label_to_agac = {
        # Pubtator
        'Disease': 'Disease',
        'DNAMutation': 'Var',
        'Gene': 'Gene',
        'ProteinMutation': 'Var',
        'SNP': 'Var',
        # SETH
        'SUBSTITUTION': 'Var',
        'DBSNP_MENTION': 'Var',
        'DELETION': 'Var',
        'FRAMESHIFT': 'Var',
        'INSERTION': 'Var',
    }

    special_save = {'p.M239V', 'AD'}
    pubtator_tag_set = {(tag[0], pubtator_label_to_agac[tag[1]], tag[-1]) for tag in pubtator_set
                        if pubtator_label_to_agac.get(tag[1])}

    pubtator_token2label = {token: label for token, label, _ in pubtator_tag_set}

    # 2021 05 25
    # if a token appears in both pubtator and model labels,
    # but has a different label,
    # keep pubtator label.
    # Avoid nested entities
    merge_tag_set = pubtator_tag_set.copy()

    for m_token, m_label, m_offset in model_tag_set:
        (m_start, m_end) = m_offset
        save_flag = True
        for p_token, p_label, p_offset in pubtator_tag_set:
            (p_start, p_end) = p_offset
            # m_token in p_token
            if m_start >= p_start and m_end <= p_end:
                save_flag = False
                continue
            # p_token in m_token
            if p_start >= m_start and p_end <= m_end:
                # do not replace 527
                # if (p_token, p_label, p_offset) in merge_tag_set:
                #     merge_tag_set.remove((p_token, p_label, p_offset))
                # merge_tag_set.add((m_token, m_label, m_offset))
                save_flag = False
                continue

            # m_token cross p_token and m_token is in front of p_token
            if m_start <= p_start and (p_start <= m_end <= m_end):
                save_flag = False
                continue

            # p_token cross m_token and p_token is in front of m_token
            if p_start <= m_start and (m_start <= p_end <= m_end):
                save_flag = False
                pass

        if save_flag:
            merge_tag_set.add((m_token, m_label, m_offset))

    # merge label to pubtator label
    merge_tag_set_cp = merge_tag_set.copy()
    for token, label, offset in merge_tag_set_cp:
        if pubtator_token2label.get(token):
            if label == pubtator_token2label[token]:
                continue
            else:
                merge_tag_set.remove((token, label, offset))
                merge_tag_set.add((token, pubtator_token2label[token], offset))

    merge_tag_set_cp = merge_tag_set.copy()

    # tagging filter
    for info in merge_tag_set_cp:
        (token, label, (start, end)) = info
        if token in special_save:
            continue
        if len(token) <= 2:
            if info in merge_tag_set:
                merge_tag_set.remove(info)
                continue

        if '(' == token[0] \
                and ')' == token[-1] \
                and label in ['Protein', 'Gene', 'Var']:
            merge_tag_set.remove(info)
            merge_tag_set.add((token[1:-1], label, (start+1, end-1)))
            continue

        if '(' == token[0] \
                and label in ['Protein', 'Gene', 'Var'] \
                and len(token) >= 3:
            merge_tag_set.remove(info)
            merge_tag_set.add((token[1:], label, (start+1, end)))
            continue

        if ')' == token[-1] and label in ['Protein', 'Gene', 'Var'] and len(token) >= 3:
            merge_tag_set.remove(info)
            merge_tag_set.add((token[:-1], label, (start, end-1)))
            continue

        if ';' == token[-1] or ':' == token[-1]:
            merge_tag_set.remove(info)
            token = token[:-1]
            end -= 1
            info = (token, label, (start, end))
            merge_tag_set.add(info)
            continue

        if "'s" == token[-2:]:
            merge_tag_set.remove(info)
            token = token[:-2]
            end -= 2
            info = (token, label, (start, end))
            merge_tag_set.add(info)
            continue

        if '(' in token \
                or ')' in token \
                or ',' in token \
                or ' and ' in token \
                or len(token)> 50:
            if '(' in token \
                    and ')' in token \
                    and label in ['Protein', 'Gene', 'Var']\
                    and 'and' not in token\
                    and 3 <=len(token) <= 30:
                continue
            merge_tag_set.remove(info)
            continue

    merge_tag_set_cp = merge_tag_set.copy()
    # tagging merge
    for info_1 in merge_tag_set_cp:
        for info_2 in merge_tag_set_cp:
            (token_1, label_1, (start_1, end_1)) = info_1
            (token_2, label_2, (start_2, end_2)) = info_2

            if token_1 in special_save:
                continue

            if len(token_1.split()) == 1 and label_1 in ['Protein', 'Gene', 'Var', 'Disease']:
                continue

            if (start_1>=start_2 and end_1<=end_2) \
                    and info_1 != info_2:

                if start_1 == start_2 and end_1 == end_2:
                    if label_1 == 'Protein' and label_2 == 'Gene':
                        if info_1 in merge_tag_set:
                            merge_tag_set.remove(info_1)
                    if label_2 == 'Protein' and label_1 == 'Gene':
                        if info_2 in merge_tag_set:
                            merge_tag_set.remove(info_2)
                else:
                    if info_1 in merge_tag_set:
                        merge_tag_set.remove((token_1, label_1, (start_1, end_1)))
    return merge_tag_set

def get_token_offset(data_list: list, sentence: str):

    last_token = ''
    offset_data_list = []
    token_start = 0
    token_end = 0
    for token_info in data_list:
        token, p_label, p_id = token_info
        if token == last_token:
            offset_data_list.append((token, p_label, p_id, (token_start, token_end)))
            continue

        token_start = sentence.find(token, token_end)
        token_end = token_start + len(token)
        offset_data_list.append((sentence[token_start:token_end], p_label, p_id, (token_start, token_end)))
        last_token = token

    return offset_data_list


def tagging_to_re_input_wordpiece(infer_result: str, output_path: str, prefix: str, idx2sentence: dict,
                                  idx2pubtator: dict, only_mutation:bool=False):

    non_self_label = {'Protein', 'Gene', "Enzyme"}

    wf_re_file = os.path.join(output_path, f'{prefix}.re.txt')
    wf_tagging_file = os.path.join(output_path, f'{prefix}.tagging.txt')

    wf_re = open(wf_re_file, 'w', encoding='utf-8')
    wf_tagging = open(wf_tagging_file, 'w', encoding='utf-8')

    reg_set = {'Reg', 'PosReg', 'NegReg'}

    data_list = []
    label_list = []
    sent_idx = ''
    save_count = 0
    sent_count = 0
    total_sent_count = 0
    with open(infer_result) as f:
        for line in f:
            l = line.strip().split('\t')

            if l == ['']:

                total_sent_count += 1

                pubtator_tag_set = idx2pubtator[sent_idx]
                sentence = idx2sentence[sent_idx]

                # try to get offset here.
                offset_data_list = get_token_offset(data_list, sentence)

                model_tag_set = tag_process_pubtator(offset_data_list, label_list, sentence)

                data_list = [ ]
                label_list = [ ]

                merge_tag_set = tagging_merge(pubtator_tag_set, model_tag_set)

                # todo: mutation sentence filter
                if only_mutation:
                    save_flag = False
                    for (_token, _type, _offset) in merge_tag_set:
                        if _type == 'Var':
                            save_flag = True
                            break
                    if not save_flag:
                        continue

                # print(sent_idx)
                # print(pubtator_tag_set)
                # print(merge_tag_set)
                # print(save_flag)
                # input()

                # print(merge_tag_set)
                # exit()
                # print('pubtator:')
                # print(pubtator_tag_set)
                # input('continue')
                # print('model:')
                # print(model_tag_set)
                # input('continue')
                # print('merge:')
                # print(merge_tag_set)
                # input('continue')
                # exit()
                if len(merge_tag_set) < 2:
                    continue
                sent_count += 1
                # print(pmid)
                tag_set_wf = '\t'.join(map(str, merge_tag_set))
                pub_tag_wf = '\t'.join(map(str, pubtator_tag_set))
                wf_tagging.write(f'{sent_idx}\t{pmid}\t'
                                 f'{sentence}\t{tag_set_wf}\t'
                                 f'{pub_tag_wf}\n')

                for (tag1, tag2) in permutations(merge_tag_set, 2):

                    token1, label1, offset1 = tag1
                    token2, label2, offset2 = tag2

                    if label1 in non_self_label and label2 in non_self_label and label1 == label2:
                        continue

                    if label1 == 'Var' and label1 == label2:
                        continue

                    save_count += 1

                    if label1 in reg_set and label2 not in reg_set:
                        # print(label1, label2)
                        # input('continue')
                        continue
                    wf_re.write(f'{token1}\t{label1}\t{offset1}\t'
                             f'{token2}\t{label2}\t{offset2}\t'
                             f'None\t{sentence}\t{pmid}\t{sent_idx}\n')

                sent_idx = ''
            else:
                sent_idx, pmid = l[0], l[1]
                token_info = (l[2], l[3], l[4])
                label = l[-1]

                data_list.append(token_info)
                label_list.append(label)

    wf_re.close()
    wf_tagging.close()

    print(f'Sentence Count: {sent_count:,}/{total_sent_count:,}.')
    print(f'{wf_tagging_file} save done.')
    print(f'{wf_re_file} save done, save count: {save_count:,}.')


def tagging_to_re_input(infer_result: str, save_file: str):

    wf = open(save_file, 'w')
    wf.write(f'Token1\tLabel1\tOffset1\t'
             f'Token2\tLabel2\tOffset2\t'
             f'Relation\tSentence\n')
    data_list = []
    label_list = []

    save_count = 0
    with open(infer_result) as f:
        for line in f:
            l = line.strip().split('\t')
            if l == ['']:
                has_label = False
                for label in label_list:
                    if label != 'O':
                        has_label = True

                if not has_label:
                    continue

                # add pubtator tagging
                tag_set, sentence = tag_process(data_list, label_list)

                data_list = []
                label_list = []

                # save RelationExtract input format
                if len(tag_set) < 2:
                    continue
                for (tag1, tag2) in permutations(tag_set, 2):

                    token1, label1, offset1 = tag1
                    token2, label2, offset2 = tag2
                    save_count += 1
                    wf.write(f'{token1}\t{label1}\t{offset1}\t'
                             f'{token2}\t{label2}\t{offset2}\t'
                             f'None\t{sentence}\n')
            else:
                if len(l) < 2:
                    continue
                data_list.append(l[0])
                label_list.append(l[1])

    wf.close()
    print(f'{save_count:,} evidence saved.')
    print(f'{save_file} save done.')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='NER infer result process.')
    parser.add_argument('-i', dest='infer_result_file', type=str, default='None',
                        help='default: None')
    parser.add_argument('-m', dest='sentence_mapping_file', type=str, required=True)
    parser.add_argument('-s', dest='save_path', type=str,
                        default='../infer_result/RE_input',
                        help='default: ../infer_result/RE_input')
    parser.add_argument('-p', dest='save_prefix', type=str,
                        default='ad.seth.pmc',
                        help='default: ad.seth.pmc')
    parser.add_argument('-b', dest='batch_process', action='store_true',
                        default=False,
                        help='batch_process default: False')
    parser.add_argument('-a', dest='infer_input_path', default='../infer_result/AD_batch_infer',
                        help='default: ../infer_result/AD_batch_infer')

    parser.add_argument('-v', dest='only_mutation_sentence', action='store_false',
                        default=True,
                        help='only_mutation_sentence default: True')
    parser.add_argument('-w', dest='word_piece', action='store_false',
                        default=True,
                        help='word_piece default: True')


    args = parser.parse_args()

    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)


    print('Running.')
    if not args.word_piece:
        print('No Word-piece')
        re_input_file = f'{args.save_path}/{args.save_prefix}.re.txt'
        tagging_to_re_input(args.infer_result_file, re_input_file)
    else:
        print('Word-piece')
        print('reading sentence_idx_file.')
        idx_to_sentence, idx_to_pubtator_tag = read_sentence_to_idx(args.sentence_mapping_file)

        if args.batch_process:
            print('Batch Process.')
            file_list = os.listdir(args.infer_input_path)
            for _file in file_list:
                save_prefix = _file.split('.')[0 ]
                infer_file = f'{args.infer_input_path}/{_file}'
                print(f'tagging to RE input {_file}.')
                tagging_to_re_input_wordpiece(infer_file, args.save_path,
                                              save_prefix, idx_to_sentence,
                                              idx_to_pubtator_tag, args.only_mutation_sentence)
        else:
            print('No Batch Process')
            print('tagging to RE input.')
            tagging_to_re_input_wordpiece(args.infer_result_file, args.save_path,
                                          args.save_prefix, idx_to_sentence,
                                          idx_to_pubtator_tag, args.only_mutation_sentence)

