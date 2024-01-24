# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 22/01/2024 16:33
@Author: yao
"""

from collections import defaultdict
import os
import re
from icecream import ic

from collections import defaultdict


def read_gold_file(gold_file: str):

    """
    Sent-0: PMC2777185 One such mutation, MEK1(P124L), was identified in a resistant metastatic focus that emerged in a melanoma patient treated with AZD6244.
    Other-0: P124L
    """
    print(f'reading gold file: {gold_file}')

    gold_sent_id_set = set()
    sent_id_to_mentions = {}

    sent_id = ''
    with open(gold_file) as f:
        for line in f:
            l = line.strip().split(':')

            if not line.strip():
                continue

            if line.startswith('sentence-'):
                sent_id = l[0].strip()
                gold_sent_id_set.add(sent_id)
            else:
                if len(l) < 2:
                    continue
                mention_set = set([ann.strip() for ann in l[1].split('\t')])

                sent_id_to_mentions[sent_id] = mention_set

    print(f'{len(gold_sent_id_set):,} in gold_set.')
    return gold_sent_id_set, sent_id_to_mentions

def read_result_file(result_file: str):
    """
    格式控制有时候不稳定 会出现逗号，tab分隔
    Sent-1: P124L
    Sent-2: P124L, Q56
    """
    print(f'reading result file: {result_file}')
    sent_id_to_result = defaultdict(set)

    with open(result_file) as f:
        for line in f:
            if not line.strip():
                continue

            l = line.strip().split(':')

            sent_id = l[0].strip()

            if len(l) < 2:
                continue

            if ',' in l[1]:
                mention_set = set([mention.strip() for mention in l[1].strip().split(',')])
            elif '\t' in l[1]:
                mention_set = set([mention.strip() for mention in l[1].strip().split('\t')])
            else:
                mention_set = {l[ 1 ].strip()}

            mention_set_cp = mention_set.copy()
            for mention in mention_set_cp:
                if len(mention.strip()) == 0 or len(mention.split()) >= 5 \
                    or 'no' in mention.lower().strip() or 'none' in mention.lower().split() or not mention:
                    mention_set.remove(mention)

            sent_id_to_result[sent_id].update(mention_set)

    return sent_id_to_result


def print_prf(tp: float, tn: float, fp: float, fn: float):
    precision = tp / (tp + fp)

    recall = tp / (tp + fn)

    f1 = 2 * precision * recall / (precision + recall)

    acc = (tp + tn) / (tp + tn + fp + fn)

    print(f'accuracy: {acc:.4f}')
    print(f'precision: {precision:.4f}, recall: {recall:.4f}, f1: {f1:.4f}')


def get_strict_metrics(sent_id_to_mentions: dict,
                       sent_id_to_result: dict):
    """
    :param sent_id_to_mentions: sent_id: mention_set
    :param sent_id_to_result: sent_id: mention_set

    TP 测试集里有，预测有
    TN 测试集没有，预测也没有 （难搞）
    FP 测试集没有，预测有
    FN 测试集里有，预测没有
    """

    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for sent_id, result_set in sent_id_to_result.items():
        if sent_id_to_mentions.get(sent_id):
            gold_mention_set = sent_id_to_mentions[sent_id]
        else:
            gold_mention_set = set()

        if len(gold_mention_set) == 0 and len(result_set) == 0:
            tn += 1

        fp += len(result_set - gold_mention_set)
        tp += len(result_set & gold_mention_set)
        fn += len(gold_mention_set - result_set)

    print(f'strict metrics.')
    print(f'tp: {tp}, tn: {tn}')
    print(f'fp: {fp}, fn: {fn}')

    print_prf(tp, tn, fp, fn)


def get_loose_metrics(sent_id_to_mentions: dict,
                       sent_id_to_result: dict):
    """
    :param sent_id_to_mentions: sent_id: mention_set
    :param sent_id_to_result: sent_id: mention_set

    TP 测试集里有，预测有
    TN 测试集没有，预测也没有 （难搞）
    FP 测试集没有，预测有
    FN 测试集里有，预测没有
    """

    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for sent_id, result_set in sent_id_to_result.items():
        if sent_id_to_mentions.get(sent_id):
            gold_mention_set = sent_id_to_mentions[sent_id]
        else:
            gold_mention_set = set()

        if len(gold_mention_set) == 0 and len(result_set) == 0:
            tn += 1

        for pred in result_set:
            pred_in_gold = False
            for gold in gold_mention_set:
                pred_words = set(pred.strip().split())
                gold_words = set(gold.strip().split())

                overlap = pred_words.intersection(gold_words)

                if overlap:
                    pred_in_gold = True
                    break

            # gold有，预测有
            if pred_in_gold:
                tp += 1
            # gold没有，预测有
            else:
                fp += 1

        for gold in gold_mention_set:
            gold_in_pred = False
            for pred in result_set:
                pred_words = set(pred.strip().split())
                gold_words = set(gold.strip().split())

                overlap = pred_words.intersection(gold_words)

                if overlap:
                    gold_in_pred = True
                break

            if not gold_in_pred:
                fn += 1

    print(f'loose metrics.')
    print(f'tp: {tp}, tn: {tn}')
    print(f'fp: {fp}, fn: {fn}')

    print_prf(tp, tn, fp, fn)


def get_data(eval_type):
    gold_path = '/Users/yao/Nutstore Files/Mac2PC/PanCancer-PNRLE/ScientificData大修意见/chat_gpt_dataset'
    result_path = '/Users/yao/Nutstore Files/Mac2PC/PanCancer-PNRLE/ScientificData大修意见/gpt_result'

    if eval_type == 'pubtator-snp':
        gold_file = f'{gold_path}/BRONCO_pos_set.txt'

        result_file = f'{result_path}/pubtator-snp.2024-01-22 17:58:44.txt'
    elif eval_type == 'agac-var':
        gold_file = f'{gold_path}/agac-var.pos.txt'
        result_file = f'{result_path}/agac-var.2024-01-22 20:15:22.txt'
    elif eval_type == 'agac-trigger':
        gold_file = f'{gold_path}/agac-trigger.pos.txt'
        result_file = f'{result_path}/agac-trigger.2024-01-22 20:42:12.txt'
    elif eval_type == 'oger-go':
        # gold_file = f'{gold_path}/oger-go.pos.txt'
        gold_file = f'{gold_path}/oger-go.pos-1200.txt'
        result_file = f'{result_path}/oger-go.2024-01-22 22:02:50.txt'
    else:
        raise ValueError(f'wrong task: {eval_type}')
    return gold_file, result_file


def main(eval_type):

    gold_file, result_file = get_data(eval_type)

    gold_sent_id_set, sent_id_to_mentions = read_gold_file(gold_file)
    sent_id_to_result = read_result_file(result_file)

    # strict
    get_strict_metrics(sent_id_to_mentions, sent_id_to_result)
    # loose
    get_loose_metrics(sent_id_to_mentions, sent_id_to_result)

if __name__ == '__main__':
    # pubtator-snp, agac-var, agac-trigger, oger-go
    # task = 'pubtator-snp'
    task = 'oger-go'
    print(f'------task: {task}-----')

    main(task)


