# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 08/05/2021 13:12
@Author: XINZHI YAO
"""

import os
from collections import defaultdict

from tqdm import tqdm

import argparse

def read_tagging_file(input_file: str):
    print('Read tagging file.')
    sent_to_norm_tagging = defaultdict(set)
    with open(input_file) as f:
        for line in f:
            l = line.strip().split('\t')
            sent_idx = l[0]
            # tag have id. ('human', 'Species', '9606', (25, 30))
            tag_list = [eval(tag) for tag in l[3:] if len(eval(tag)) == 4]

            sent_to_norm_tagging[sent_idx].update(set(tag_list))
    return sent_to_norm_tagging



def sentence_filter(infer_file: str, save_file: str,
                    tagging_input_file: str, only_norm_var:bool=False):

    sent_to_norm_tag = read_tagging_file(tagging_input_file)

    var_label = {'DNAMutation', 'ProteinMutation', 'SNP', 'SUBSTITUTION',
                 'DBSNP_MENTION', 'DELETION', 'FRAMESHIFT', 'INSERTION'}

    # 1. Sentence filter. Var -- CauseOf -- Reg/PosReg/NegReg
    #       normalized mutation tag. --> SETH, PubTator
    #       All Mutation tag.
    var_sentence = set()
    norm_var_sent_id = set()
    reg_set = {'Reg', 'NegReg', 'PosReg'}
    with open(infer_file, encoding='utf-8') as f:
        for line in f:
            l = line.strip().split('\t')
            sub, sub_type, sub_off = l[0], l[1], l[2]
            obj, obj_type, obj_off = l[3], l[4], l[5]
            _, sent, pmid, sent_idx, relation = l[6], l[7], l[8], l[9], l[10]

            if sent_to_norm_tag.get(sent_idx):
                norm_var_set = {tag[0] for tag in sent_to_norm_tag[sent_idx]
                                if tag[1] in var_label}
                if (sub_type == 'Var' and sub in norm_var_set) \
                        and obj_type in reg_set \
                        and relation == 'CauseOf':
                    norm_var_sent_id.add(sent_idx)
            if sub_type == 'Var' and obj_type in reg_set and relation == "CauseOf":
                var_sentence.add(sent)
    print(f'Standardized mutation sentence: {len(norm_var_sent_id):,}.')
    print(f'Sentences containing mutations: {len(var_sentence):,}.')

    # 2. save all result of sentences including Var-CauseOf-Reg.
    save_count = 0
    wf = open(save_file, 'w', encoding='utf-8')
    with open(infer_file, encoding='utf-8') as f:
        for line in f:
            l = line.strip().split('\t')
            sub, sub_type, sub_off = l[0], l[1], l[2]
            obj, obj_type, obj_off = l[3], l[4], l[5]
            _, sent, pmid, sent_idx, relation = l[6], l[7], l[8], l[9], l[10]

            if only_norm_var:
                if sent_idx not in norm_var_sent_id:
                    continue

                norm_var_set = {tag[0] for tag in sent_to_norm_tag[sent_idx]
                                if tag[1] in var_label}

                if sub_type == 'Var':
                    if obj_type == 'Var':
                        if sub in norm_var_set and obj in norm_var_set:
                            wf.write(f'{line.strip()}\n')
                            save_count += 1
                    else:
                        if sub in norm_var_set:
                            wf.write(f'{line.strip()}\n')
                            save_count += 1
                    continue
                else:
                    if obj_type == 'Var':
                        if obj in norm_var_set:
                            wf.write(f'{line.strip()}\n')
                            save_count += 1
                        continue
                    else:
                        wf.write(f'{line.strip()}\n')
                        save_count += 1
            else:
                if sent in var_sentence:
                    wf.write(f'{line.strip()}\n')
                    save_count += 1
    wf.close()
    print(f'{save_file} save done. (filted sentence.), save count: {save_count:,}')
    return sent_to_norm_tag

# Determine whether the ThemeOf relation is separated by punctuation
def if_punc_separated(offset_1: tuple, offset_2: tuple, sentence: str):
    min_start = min(min(offset_1), min(offset_2))
    max_end = max(max(offset_1), max(offset_2))
    # comma separated add other ; . et.al.
    # ThemeOf filter
    interval_sent = sentence[min_start: max_end]
    interval_sent_split = interval_sent.split()
    if ',' in interval_sent\
            or 'and' in interval_sent_split\
            or ';' in interval_sent\
            or '.' in interval_sent:
        # print(offset_1, offset_2)
        # print(sentence[offset_1[0]: offset_1[1]])
        # print(sentence[offset_2[0]: offset_2[1]])
        # print(sentence[min_start: max_end])
        # input('continue')
        return True
    else:
        return False

def log_line_extraction(filter_file: str, log_line_save_file: str,
                        cytoscape_save_dir: str, cytoscape_save_prefix: str,
                        only_save_log_theme:bool=True,
                        ):

    # data statistics
    sent_to_triple = defaultdict(set)

    # 1. Read filter sentence file.
    with open(filter_file, encoding='utf-8') as f:
        for line in f:
            l = line.strip().split('\t')
            sub, sub_type, sub_off = l[0], l[1], l[2]
            obj, obj_type, obj_off = l[3], l[4], l[5]
            _, sent, pmid, sent_idx, relation = l[6], l[7], l[8], l[9], l[10]
            sub_off = tuple(map(int, eval(sub_off)))
            obj_off = tuple(map(int, eval(obj_off)))

            if relation == 'NoRelation':
                continue

            sent_to_triple[(sent, pmid, sent_idx)].add((sub, sub_type, sub_off, obj, obj_type, obj_off, relation, line.strip()))

    # 2. Save Cytoscape file.
    if not cytoscape_save_prefix:
        node_file = os.path.join(cytoscape_save_dir, 'node.tsv')
        edge_file = os.path.join(cytoscape_save_dir, 'edge.tsv')
    else:
        node_file = os.path.join(cytoscape_save_dir, f'{cytoscape_save_prefix}.node.tsv')
        edge_file = os.path.join(cytoscape_save_dir, f'{cytoscape_save_prefix}.edge.tsv')

    node_count = defaultdict(int)
    node_to_type = defaultdict(set)

    edge_count = defaultdict(int)

    node_set = set()
    edge_set = set()

    edge_to_pmid = defaultdict(set)
    reg_edge_to_tagger = defaultdict(set)


    var_theme_edge_set = set()
    var_theme_count = defaultdict(int)

    # adjust node type for draw.
    yellow_type = {'Protein', 'Gene', 'Enzyme'}
    green_type = {'MPA', 'CPA'}
    blue_type = {'Pathway', 'Interaction', 'Disease'}
    reg_set = {'Reg', 'NegReg', 'PosReg'}
    save_count = 0

    ## log file.
    wf_log = open(log_line_save_file, 'w', encoding='utf-8')
    wf_log.write('Entity1\tEntity1 Type\tRelation1\t'
             'Entity2\tEntity2 Type\tRelation2\t'
             'Entity3\tEntity3 Type\t'
             'Sentence\tPMID\tSentenceIdx\t'
             'RuleType\n')

    for (sent, pmid, sent_idx), triple_set in tqdm(sent_to_triple.items()):
    # for (sent, pmid, sent_idx), triple_set in sent_to_triple.items():
        var_2_themeof = defaultdict(set)
        sentence_save_flag = False
        additional_info = set()

        # Rule based Semantic Role Chains Extraction
        for triple_1 in triple_set:
            sub1, sub_type1, sub_off1, obj1, obj_type1, obj_off1, relation1, _ = triple_1
            # Rule3 Var ← ThemeOf — Protein/Gene/Enzyme
            if obj_type1 == 'Var' \
                    and sub_type1 in yellow_type \
                    and relation1 == 'ThemeOf':
                # ThemeOf is one-way relation.
                if (sub1, obj1, 'Theme') not in var_theme_edge_set|additional_info \
                        and (obj1, sub1, 'Theme') not in var_theme_edge_set|additional_info :

                    if not if_punc_separated(sub_off1, obj_off1, sent):
                        additional_info.add((sub1, sub_type1, obj1, obj_type1))
                        var_2_themeof[obj1].add(sub1)

            # Rule4 * (Protein/Gene/Enzyme/CPA/MPA/Pathway/Interaction, No-SELF)
            # ← ThemeOf — Protein/Gene/Enzyme/Pathway/Interaction
            if (((sub_type1 in yellow_type)
                 and (obj_type1 in yellow_type | green_type | blue_type)
                 and obj_type1 != sub_type1)
                or ((sub_type1 in blue_type)
                # 5.26 Pathway/Interaction can not ThemeOf Protein/Gene/Enzyme
                    and (obj_type1 in green_type | blue_type)
                    and sub_type1 != obj_type1)) \
                    and relation1 == 'ThemeOf':

                if (sub1, obj1, 'Theme') not in var_theme_edge_set|additional_info \
                        and (obj1, sub1, 'Theme') not in var_theme_edge_set|additional_info:
                    if not if_punc_separated(sub_off1, obj_off1, sent):
                        additional_info.add((sub1, sub_type1, obj1, obj_type1))
                        var_2_themeof[obj1].add(sub1)

            # Rule5
            # *(Protein/Gene/Enzyme/CPA/MPA/Pathway/Interaction)
            # ← ThemeOf — CPA/MPA

            # update: 5.26 del Protein/Gene/Enzyme in Rule5
            # if (sub_type1 in green_type and obj_type1 in yellow_type | green_type | blue_type) \
            if (sub_type1 in green_type
                    and obj_type1 in green_type | blue_type) \
                    and relation1 == 'ThemeOf':

                if (sub1, obj1, 'Theme') not in var_theme_edge_set|additional_info \
                        and (obj1, sub1, 'Theme') not in var_theme_edge_set|additional_info:

                    if not if_punc_separated(sub_off1, obj_off1, sent):
                        additional_info.add((sub1, sub_type1, obj1, obj_type1))
                        var_2_themeof[obj1].add(sub1)

            # Rule1
            # Var—CauseOf→Reg/PosReg/NegReg
            # ←ThemeOf—Protein/Gene/Enzyme/CPA/MPA/Pathway/Interaction
            if (sub_type1 == 'Var') \
                    and (obj_type1 in reg_set) \
                    and relation1 == 'CauseOf':

                for triple_2 in triple_set:

                    if triple_2 == triple_1:
                        continue

                    sub2, sub_type2, sub_off2, obj2, obj_type2, obj_off2, relation2, _ = triple_2
                    if (sub_type2 in yellow_type|green_type|blue_type) \
                            and (obj1 == obj2) \
                            and relation2 == 'ThemeOf':

                        save_count += 1
                        sentence_save_flag = True
                        wf_log.write(f'{sub1}\t{sub_type1}\t{relation1}\t'
                                 f'{obj1}\t{obj_type1}\t{relation2}\t'
                                 f'{sub2}\t{sub_type2}\t'
                                 f'{sent}\t{pmid}\t{sent_idx}\t'
                                 f'1\n')

                        node_count[sub1] += 1
                        node_count[sub2] += 1

                        node_set.add(sub1)
                        node_set.add(sub2)

                        node_to_type[sub1].add(sub_type1)
                        node_to_type[sub2].add(sub_type2)

                        edge_count[(sub1, sub2, obj_type1)] += 1
                        edge_set.add((sub1, sub2, obj_type1))

                        # update 7-15: add tagger to edge_to_pmid
                        # edge_to_pmid[(sub1, sub2, obj_type1)].add(f'{pmid}-{sent_idx}')
                        edge_to_pmid[(sub1, sub2, obj_type1)].add((f'{pmid}-{sent_idx}', obj1))
                        reg_edge_to_tagger[(sub1, sub2, obj_type1)].add(obj1)

                        # print('Rule 1:')
                        # print(pmid, sent_idx)
                        # print(sent)
                        # print(sub1, sub_type1, relation1, obj1, obj_type1)
                        # # print(sub2, sub_type2, relation2, obj2, obj_type2)
                        # print(obj2, obj_type2, relation2, sub2, sub_type2)
                        # print()
                        # input('Type anything for Rule2 or additional information.')

                        if len(triple_set) < 4:
                            continue

                        # Rule2
                        # Reg/PosReg/NegReg in ① — CauseOf →
                        # Reg/PosReg/NegReg
                        # ← ThemeOf — Protein/Gene/Enzyme/CPA/MPA/Pathway/Interaction
                        for triple_3 in triple_set:

                            if triple_3 in {triple_1, triple_2}:
                                continue

                            sub3, sub_type3, sub_off3, obj3, obj_type3, obj_off3, relation3, _ = triple_3
                            # Reg/PosReg/NegReg in ① — CauseOf → Reg/PosReg/NegReg
                            if (sub3 == obj2) \
                                    and relation3 == 'CauseOf':

                                for triple_4 in triple_set:
                                    if triple_4 in {triple_1, triple_2, triple_3}:
                                        continue
                                    # Reg/PosReg/NegReg ←ThemeOf — Protein/Gene/Enzyme/CPA/MPA/Pathway/Interaction
                                    sub4, sub_type4, sub_off3, obj4, obj_type4, obj_off3, relation4, _ = triple_4

                                    if sub2 == sub4:
                                        continue

                                    if (sub_type4 in yellow_type|blue_type|green_type) \
                                        and (obj4 == obj3) \
                                            and relation4 == 'ThemeOf':

                                        save_count += 1
                                        wf_log.write(f'{sub2}\t{sub_type2}\t{relation3}\t'
                                                 f'{obj3}\t{obj_type3}\t{relation4}\t'
                                                 f'{sub4}\t{sub_type4}\t'
                                                 f'{sent}\t{pmid}\t{sent_idx}\t'
                                                 f'2\n')


                                        node_count[sub2] += 1
                                        node_count[sub4] += 1

                                        node_set.add(sub2)
                                        node_set.add(sub4)

                                        node_to_type[sub2].add(sub_type2)
                                        node_to_type[sub4].add(sub_type4)

                                        edge_count[(sub2, sub4, obj_type4)] += 1
                                        edge_set.add((sub2, sub4, obj_type4))
                                        # update 7-15: add tagger to edge_to_pmid
                                        # edge_to_pmid[(sub2, sub4, obj_type4)].add(f'{pmid}-{sent_idx}')
                                        edge_to_pmid[(sub2, sub4, obj_type4)].add((f'{pmid}-{sent_idx}', obj3))
                                        reg_edge_to_tagger[(sub2, sub4, obj_type4)].add(obj3)

                                        # print('Rule 2:')
                                        # print(pmid, sent_idx)
                                        # print(sent)
                                        # print(obj1, obj_type1, obj2, obj_type2)
                                        # print(sub1, sub_type1, obj_type2, sub2, sub_type2)
                                        # print(sub2, sub_type2, obj_type2, obj3, obj_type3)
                                        #
                                        # print(sub2, sub_type2, obj_type4, sub4, sub_type4)
                                        # print()
                                        # input('Type anything for Additional information.')

        if (only_save_log_theme and sentence_save_flag) or not only_save_log_theme:
            # 5.25 save node information if this sentence contains the log-line.
            # print()
            # print(additional_info)
            # print()
            # input('Type anything for next sentence.')

            for (sub, sub_type, obj, obj_type) in additional_info:

                node_count[sub] += 1
                node_count[obj] += 1

                node_set.add(sub)
                node_set.add(obj)

                node_to_type[sub].add(sub_type)
                node_to_type[obj].add(obj_type)

                var_theme_edge_set.add((sub, obj, 'Theme'))
                # # update 7-15: add tagger to edge_to_pmid
                # edge_to_pmid[(sub, obj, 'Theme')].add(f'{pmid}-{sent_idx}')
                edge_to_pmid[(sub, obj, 'Theme')].add((f'{pmid}-{sent_idx}', 'Theme'))
                var_theme_count[(sub, obj)] += 1

        if sentence_save_flag:
            for var, theme in var_2_themeof.items():
                theme_wf = '|'.join(theme)
                wf_log.write(f'{var}\t{theme_wf}\n')
            wf_log.write('\n')

    wf_log.close()

    # 3. save node information.
    node_id = 0
    with open(node_file, 'w', encoding='utf-8') as wf_node:
        wf_node.write('Node_id\tNode_Name\tDegree\tNode_type\n')
        for node in node_set:
            # fixme: A node may have multiple types
            # node_type = '|'.join(node_to_type[node])
            node_type = list(node_to_type[node])[0]

            wf_node.write(f'{node_id}\t{node}\t{node_count[node]}\t'
                     f'{node_type}\n')
            node_id += 1

    # 4. save edge information.
    edge_save_count = 0
    edge_to_id = {}
    with open(edge_file, 'w', encoding='utf-8') as wf_edge:
        wf_edge.write(f'Edge ID\tSource\tTarget\tRelation\tWeight\tPMID Source\tTagger\n')
        for edge in edge_set:
            (source, target, relation) = edge

            if edge_to_id.get(edge):
                edge_id = edge_to_id[edge]
            else:
                edge_id = len(edge_to_id.keys())
                edge_to_id[edge] = edge_id

            edge_save_count += 1
            # 7-20: Multiple evidence written in multiple lines.
            for evidence_id, tagger in edge_to_pmid[edge]:
                wf_edge.write(f'{edge_id}\t'
                              f'{source}\t{target}\t{relation}\t'
                              f'{edge_count[ edge ]}\t'
                              f'{evidence_id}\t{tagger}\n')

        for edge in var_theme_edge_set:
            (var, theme, relation1) = edge
            edge_save_count += 1

            if edge_to_id.get(edge):
                edge_id = edge_to_id[edge]
            else:
                edge_id = len(edge_to_id.keys())
                edge_to_id[edge] = edge_id

            for evidence_id, tagger in edge_to_pmid[edge]:
                wf_edge.write(f'{edge_id}\t'
                              f'{var}\t{theme}\t{relation1}\t'
                              f'{var_theme_count[(var, theme)]}\t'
                              f'{evidence_id}\t{tagger}\n')


    print(f'{node_file} save done, save node: {node_id:,}.')
    print(f'{edge_file} save done, save edge: {edge_save_count:,}.')
    print(f'Logical chain save count: {save_count:,}, save file: {log_line_save_file}.')


def get_case_set(input_file: str):

    case_set = set()
    with open(input_file) as f:
        for line in f:
            l = line.strip().split('\t')
            case_set.add(l[0])
    print('Total case token:')
    print(case_set)
    print(f'read file: {input_file}, case count: {len(case_set):,}.')
    return case_set


def case_filter(infer_file: str, save_file: str,
                case_set: set,
                lower_case:bool=True):


    if lower_case:
        case_set = set(map(lambda x: x.lower(), case_set))

    save_count = 0
    save_case = defaultdict(int)
    save_pmid = set()
    save_sent_idx = set()
    with open(infer_file) as f:
        for line in f:
            l = line.strip().split('\t')

            token1 = l[0].strip()
            token2 = l[3].strip()
            pmid, sent_idx = l[8], l[9]

            if lower_case:
                token1 = token1.lower()
                token2 = token2.lower()

            if token1 in case_set or token2 in case_set:
                if token1 in case_set:
                    save_case[token1] += 1
                else:
                    save_case[token2] += 1
                save_pmid.add(pmid)
                save_sent_idx.add(sent_idx)

    # 5-26 filter by sent_idx
    wf = open(save_file, 'w')
    with open(infer_file) as f:
        for line in f:
            l = line.strip().split('\t')

            pmid, sent_idx = l[8], l[9]
            # relation = l[10]
            # 5-26 save NoRelation to make sure all entity has be tagged.
            # if relation == 'NoRelation':
            #     continue
            if sent_idx in save_sent_idx:
                wf.write(line)
                save_count += 1

    wf.close()

    if save_count == 0:
        os.remove(save_file)
        print(f'{save_file} deleted, save count: {save_count:,}.')
        return False
    else:
        print(f'Covered Case: {save_case}.')
        print(f'{save_file} save done,'
              f' save count: {save_count:,},'
              f' covered case: {len(save_case.keys()):,}'
              f' covered pmid: {len(save_pmid)},'
              f' covered sentence: {len(save_sent_idx)}.')
        return True


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RE infer result processing.')

    parser.add_argument('-i', dest='infer_save_file', required=True)
    parser.add_argument('-t', dest='tagging_file', required=True)
    parser.add_argument('-s', dest='save_path', required=True)
    parser.add_argument('-f', dest='save_prefix',
                        default='ad-pmid',
                        help='default: ad-pmid')
    parser.add_argument('-r', dest='only_norm_var', action='store_true',
                        default=False,
                        help='only_norm_var, default: False.')

    parser.add_argument('-n',dest='sent_filted',
                        default='infer_save.sent.tsv',
                        help='default: infer_save.sent.tsv')
    parser.add_argument('-k', dest='case_token_file',
                        default='../infer_result/Case_dir/AD.66.GeneSymbol.txt',
                        help='default: ../infer_result/Case_dir/AD.66.GeneSymbol.txt')
    parser.add_argument('-c', dest='case_filter', action='store_true',
                        default=False,
                        help='case_filter, default: False')
    parser.add_argument('-p', dest='split_case_file', action='store_true',
                        default=False,
                        help='split_case_file, default: False')
    args = parser.parse_args()

    sent_filted_file = os.path.join(args.save_path, args.sent_filted)

    # cytoscape input file
    cytoscape_dir = f'{args.save_path}/cytoscape_input'

    Case_filter = False
    split_case_file = False

    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)
    if not os.path.exists(cytoscape_dir):
        os.mkdir(cytoscape_dir)

    # Sentence filter.
    sent_id_to_norm_tagging = sentence_filter(args.infer_save_file, sent_filted_file,
                    args.tagging_file, only_norm_var=args.only_norm_var)

    if args.case_filter:
        case_path = f'{args.save_path}/Case_Dir'
        if not os.path.exists(case_path):
            os.mkdir(case_path)

        if not args.case_token_file is None:
            case_name = '.'.join(os.path.basename(args.case_token_file).split('.')[:-2])
            case_token = get_case_set(args.case_token_file)

        else:
            # APOE, SEMA3A, RAMP3, EFR3B
            case_name = 'APOE4'
            case_token = {'APOE4'}

        if (not args.case_token_file  is None) and args.split_case_file:
            for case in case_token:
                case_name = case
                case_token = {case}

                case_file = f'{case_path}/{case_name}.infer.tsv'
                if not os.path.exists(case_path):
                    os.mkdir(case_path)
                log_line = f'{case_name}.log.tsv'
                log_save_path = f'{args.save_path}/log_file'
                if not os.path.exists(log_save_path):
                    os.mkdir(log_save_path)

                log_line_file = f'{log_save_path}/{log_line}'

                # all sentence in the pmid that containing the case_token show be saved.
                save_case_bool = case_filter(sent_filted_file, case_file, case_token, True)
                if save_case_bool:
                    log_line_extraction(case_file, log_line_file,
                                        cytoscape_dir, case_name,
                                        only_save_log_theme=True,)
        else:
            case_file = f'{case_path}/{case_name}.infer.tsv'
            if not os.path.exists(case_path):
                os.mkdir(case_path)

            log_line = f'{case_name}.log.tsv'
            log_save_path = f'{save_path}/log_file'
            if not os.path.exists(log_save_path):
                os.mkdir(log_save_path)

            log_line_file = f'{log_save_path}/{log_line}'

            # all sentence in the pmid that containing the case_token show be saved.
            save_case_bool = case_filter(sent_filted_file, case_file, case_token, True)
            if save_case_bool:
                log_line_extraction(case_file, log_line_file,
                                    cytoscape_dir, case_name,
                                    only_save_log_theme=True)
    else:
        print('no case filter.')
        log_line = 'log_line.seth.tsv'
        log_save_path = f'{args.save_path}/log_file'
        if not os.path.exists(log_save_path):
            os.mkdir(log_save_path)

        log_line_file = f'{log_save_path}/{args.save_prefix}.{log_line}'

        log_line_extraction(sent_filted_file, log_line_file,
                            cytoscape_dir, args.save_prefix,
                            only_save_log_theme=True)
