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
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict


def read_gold_file(gold_file: str):

    """
    Sent-0: PMC2777185 One such mutation, MEK1(P124L), was identified in a resistant metastatic focus that emerged in a melanoma patient treated with AZD6244.
    Other-0: P124L
    """
    print(f'reading gold file: {gold_file}')

    gold_sent_id_set = set()
    sent_id_to_relation = {}

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

                relation = l[1].strip()
                sent_id_to_relation[sent_id] = relation

    print(f'{len(gold_sent_id_set):,} in gold_set.')
    return gold_sent_id_set, sent_id_to_relation

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

            relation = l[1].strip()

            sent_id_to_result[sent_id] = relation

    return sent_id_to_result


def print_prf(tp: float, tn: float, fp: float, fn: float):
    precision = tp / (tp + fp)

    recall = tp / (tp + fn)

    f1 = 2 * precision * recall / (precision + recall)

    acc = (tp + tn) / (tp + tn + fp + fn)

    print(f'accuracy: {acc:.4f}')
    print(f'precision: {precision:.4f}, recall: {recall:.4f}, f1: {f1:.4f}')


def get_data(eval_type):
    gold_path = '/Users/yao/Nutstore Files/Mac2PC/PanCancer-PNRLE/ScientificData大修意见/chat_gpt_dataset'
    result_path = '/Users/yao/Nutstore Files/Mac2PC/PanCancer-PNRLE/ScientificData大修意见/gpt_result'

    if eval_type == 'agac-re':
        # gold_file = f'{gold_path}/oger-go.pos.txt'
        gold_file = f'{gold_path}/agac-re.pos.txt'
        result_file = f'{result_path}/agac-re.2024-01-23 10:02:14.txt'
    else:
        raise ValueError(f'wrong task: {eval_type}')
    return gold_file, result_file

def get_classification_metrics(sent_id_to_relation: dict, sent_id_to_result: dict):

    gold_id_set = set(sent_id_to_relation.keys())
    pred_id_set = set(sent_id_to_result.keys())

    both_id_list = list(gold_id_set&pred_id_set)

    print(f'{len(both_id_list):,} id in both gold and pred.')

    gold_theme_labels = []
    gold_cause_labels = []

    pred_theme_labels = []
    pred_cause_labels = []
    for _id in both_id_list:
        gold_label = sent_id_to_relation[_id]
        pred_label = sent_id_to_result[_id]
        if gold_label in {'ThemeOf', 'NoRelation'}:
            gold_theme_labels.append(gold_label)
            pred_theme_labels.append(pred_label)
        elif gold_label in {'CauseOf', 'NoRelation'}:
            gold_cause_labels.append(gold_label)
            pred_cause_labels.append(pred_label)
        else:
            raise ValueError(f'wrong: {gold_label}')

    print(f'ThemeOf')
    get_metrics(gold_theme_labels, pred_theme_labels)
    print()
    print(f'CauseOf')
    get_metrics(gold_cause_labels, pred_cause_labels)

def get_metrics(gold_labels: list, pred_labels: list):

    label_to_idx = {
        'ThemeOf': 0,
        'CauseOf': 1,
        'NoRelation': 2
    }

    gold_encoded = [label_to_idx[label] for label in gold_labels]
    pred_encoded = [label_to_idx[label] for label in pred_labels]

    # label_encoder = LabelEncoder()
    # gold_encoded = label_encoder.fit_transform(gold_labels)
    # pred_encoded = label_encoder.transform(pred_labels)


    # 计算 Precision、Recall 和 F1 Score
    precision = precision_score(gold_encoded, pred_encoded, average='macro')
    recall = recall_score(gold_encoded, pred_encoded, average='macro', zero_division=1)
    f1 = f1_score(gold_encoded, pred_encoded, average='macro')

    print(f'Precision: {precision:.4f}')
    print(f'Recall: {recall:.4f}')
    print(f'F1 Score: {f1:.4f}')

def main(eval_type):

    gold_file, result_file = get_data(eval_type)

    gold_sent_id_set, sent_id_to_relation = read_gold_file(gold_file)
    sent_id_to_result = read_result_file(result_file)

    # ic(sent_id_to_relation)
    # input()
    # ic(sent_id_to_result)
    # input()
    # exit()

    get_classification_metrics(sent_id_to_relation, sent_id_to_result)

    # strict
    # get_strict_metrics(sent_id_to_relation, sent_id_to_result)
    # # loose
    # get_loose_metrics(sent_id_to_relation, sent_id_to_result)

if __name__ == '__main__':
    # pubtator-snp, agac-var, agac-trigger, oger-go
    # task = 'pubtator-snp'
    task = 'agac-re'
    print(f'------task: {task}-----')

    main(task)


