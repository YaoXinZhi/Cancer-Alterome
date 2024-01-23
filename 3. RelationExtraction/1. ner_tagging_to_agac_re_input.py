# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 29/01/2023 13:23
@Author: yao
"""

"""
该代码用于merge OGER SETH PhenoTagger 任务一 PubTator tmvar3 的标注
并生成任务二用于输入的两个文件
一个tagging.txt文件
sent_id pmid sentence ("mention1", "type1", "Norm1", (Start1, End1))
一个re.txt
mention1 type1 (start1, end1) mention2 type2 (start2,end2) None sent pmid sent_id


python3 tagging_merge_for_re_input.py 
-ne /home/kyzhou/xzyao/cancer_small/cancer_pmid_tagging_file 
-og /home/kyzhou/xzyao/cancer_small/small_pmid_processed_oger 
-ph /home/kyzhou/xzyao/cancer_small/cancer_pmid_pheno_output 
-tm /home/kyzhou/xzyao/CancerPNRLE/small_data/small_pubtator_tmvar3/small.pubtator.pmc-pmid.txt 
-sp /home/kyzhou/xzyao/CancerPNRLE/small_data/small_re_input 
-pn 20

"""

import os
import re
import itertools
from multiprocessing import Manager, Process

import humanize
import argparse
from collections import defaultdict

def read_ner_tagging_file(tagging_file: str):
    """
    read AGAC task1 processed file.
    ('graft-versus-host disease', 'Disease', (209, 234))
    ('minimize', 'NegReg', (200, 208))
    ("Wilms' Tumor", 'Disease', (38, 50))
    (' NCT01640301 ', 'Var', (352, 365))
    ('enhance', 'PosReg', (244, 251))
    ('graft-versus-host disease', 'Disease', 'MESH:D006086', (209, 234))
    ('patients', 'Species', '9606', (342, 350))
    ("Wilms' Tumor", 'Disease', 'MESH:D009396', (38, 50))
    """
    print(f'Reading tagging: {os.path.basename(tagging_file)}-{humanize.naturalsize(os.path.getsize(tagging_file))}')
    id_pair_to_sent = {}
    id_pair_to_ner = {}
    with open(tagging_file) as f:
        for line in f:
            l = line.strip().split('\t')

            if len(l) < 4:
                continue

            sent_id = l[0]
            pmid = l[1]
            sentence = l[2]
            tagging_set = set(l[3:])

            id_pair_to_sent[(pmid, sent_id)] = sentence
            id_pair_to_ner[(pmid, sent_id)] = {eval(tag) for tag in tagging_set}
    print(f'NER file: {os.path.basename(tagging_file)} loaded {len(id_pair_to_sent):,} sentences.')
    return id_pair_to_sent, id_pair_to_ner


def read_oger_tagging_file(oger_tagging_file: str):
    """
    {('TCR', 'transcription-coupled nucleotide-excision repair', 'biological_process', 'GO:0006283', ('70', '73')),
    ('TCR', 'T cell receptor complex', 'cellular_component', 'GO:0042101', ('70', '73')),
    ('Tumor Antigen', 'obsolete tumor antigen', 'molecular_function', 'GO:0008222', ('45', '58'))}
    """
    print(f'Reading: {os.path.basename(oger_tagging_file)}-{humanize.naturalsize(os.path.getsize(oger_tagging_file))}')
    id_pair_to_oger = defaultdict(set)
    with open(oger_tagging_file) as f:
        for line in f:
            l = line.strip().split('\t')

            sent_id = l[0]
            pmid = l[1]
            sent = l[2]

            oger_tags = eval(l[3])

            id_pair_to_oger[(pmid, sent_id)] = oger_tags
    print(f'OGER file: {os.path.basename(oger_tagging_file)} loaded {len(id_pair_to_oger):,} sentences.')
    return id_pair_to_oger

# fixme: read phenotagger file
def read_pheno_tagging_file(pheno_tagging_file: str):
    """
    pmid: {mention, pheno_id)
    """
    print(f'Reading: {os.path.basename(pheno_tagging_file)}-{humanize.naturalsize(os.path.getsize(pheno_tagging_file))}')
    pmid_to_pheno = defaultdict(set)
    with open(pheno_tagging_file) as f:
        for line in f:
            l = line.strip().split('\t')
            if len(l) < 6:
                continue
            pmid = l[0]
            mention = l[3]
            pheno_id = l[5]

            pmid_to_pheno[pmid].add((mention, pheno_id))

    # tag 标准化格式
    new_pmid_to_pheno = {}
    for pmid, pheno_set in pmid_to_pheno.items():
        new_pmid_to_pheno[pmid] = tag_stand(pheno_set)
    print(f'Pheno file: {os.path.basename(pheno_tagging_file)} loaded {len(pmid_to_pheno):,} pmids.')
    return new_pmid_to_pheno

def read_tmvar3_file(tmvar_file: str):
    """
    pubtator format
    pmid: (mention, type, norm_id)
    """
    print(f'Reading: {os.path.basename(tmvar_file)}-{humanize.naturalsize(os.path.getsize(tmvar_file))}')
    mention_type_mapping = {
        'ProteinAcidChange': 'Mutation',
        'DNAAcidChange': 'Mutation'
    }

    pmid_to_tmvar = defaultdict(set)
    with open(tmvar_file) as f:
        for line in f:
            l = line.strip().split('\t')
            if len(l) < 6:
                continue
            pmid = l[0]
            start = l[1]
            end = l[2]
            mention = l[3]
            tag_type = l[4]
            tag_id = l[5]

            if tag_type in {'Gene', 'Mutation'}:
                pmid_to_tmvar[pmid].add((mention, tag_type, tag_id, (start,end)))
            if mention_type_mapping.get(tag_type):
                pmid_to_tmvar[pmid].add((mention, 'Mutation', tag_id, (start, end)))

    new_pmid_to_tmvar = {}
    for pmid, tmvar_set in pmid_to_tmvar.items():
        new_pmid_to_tmvar[pmid] = tag_stand(tmvar_set)
    print(f'tmvar3 file: {os.path.basename(tmvar_file)} loaded {len(pmid_to_tmvar):,} pmids.')
    return new_pmid_to_tmvar


def tag_stand(tag_set: set, non_normalized_mutation_syno_to_norm:dict=None):
    """
    将tag转换为标准格式
    (mention, type, norm_id, norm_name)
    """

    del_type_set = {'Species', 'CellLine', 'cellular_component', 'Chemical', 'Genus'}
    type_convert = {
        'Gene': "Gene",
        'Disease': "Disease",
        "MPA": "MPA",
        'CPA': "CPA",
        'phenotype': 'phenotype',
        "NegReg": "NegReg",
        'Reg': 'Reg',
        'PosReg': "PosReg",
        "Mutation": 'Mutation',

        'Var': "Mutation",
        'molecular_function': 'MPA',
        'biological_process': "CPA",
        'SUBSTITUTION': 'Mutation',
        'STRUCTURAL_ABNORMALITY': 'Mutation',
        'Pathway': 'Pathway',
        'Protein': "Gene",
        'Interaction': 'Interaction',
        'Enzyme': 'Gene',
        'DUPLICATION': 'Mutation',
        'FRAMESHIFT': "Mutation",
        'DELETION': 'Mutation',
        'DBSNP_MENTION': "Mutation",

    }

    new_tag_set = set()
    for tag in tag_set:
        mention = ''
        _type = ''
        norm_id = '-'
        norm_name = '-'
        if len(tag) == 2:
            mention, norm_id = tag
            _type = 'phenotype'
        elif len(tag) == 3:
            mention, _type, offset = tag
        elif len(tag) == 4:
            mention, _type, norm_id, offset = tag
        elif len(tag) == 5:
            mention, norm_name, _type, norm_id, offset = tag
        else:
            print(f'Wrong length tag: {tag}')

        if not norm_id:
            norm_id = '-'

        if _type in del_type_set:
            continue
        if type_convert.get(_type):
            _type = type_convert[_type]
            if _type == 'Mutation' :
                # rs id normalization
                if re.findall(r'rs\d+', re.escape(mention)):
                    rs_id = re.findall(r'rs\d+', re.escape(mention))[0]
                    norm_id = rs_id
                    norm_name = rs_id
                # add non -normalized mutation norm_id and norm_name
                # for AGAC Task1
                if non_normalized_mutation_syno_to_norm:
                    # print(non_normalized_mutation_syno_to_norm)
                    if non_normalized_mutation_syno_to_norm.get(mention.lower()):
                        norm_id = non_normalized_mutation_syno_to_norm[mention.lower()]
                        norm_name = non_normalized_mutation_syno_to_norm[mention.lower()]

                if 'obsolete' in norm_name:
                    norm_name = norm_name.replace('obsolete', ' ').strip()
            new_tag_set.add((mention, type_convert[_type], norm_id, norm_name))
        else:
            # print(mention, norm_id, norm_name)
            # print(f'missing type: "{_type}"')
            continue
    return new_tag_set

def match_pubtator_ann(annotation_set: set, sentence: str):
    """
    匹配句子中是否有标准tag
    ((mention, _type, norm_id, norm_name))
    """
    match_set = set()
    # value: (mention, mention type, norm_id)
    for tag in annotation_set:
        (mention, mention_type, norm_id, norm_name) = tag
        # try:
        match = re.search(r"\b" + re.escape(mention) + r"\b", sentence)
        if match:
            match_set.add(tag)

    return match_set

def filter_entities(tagging_set):
    """
    chatgpt write this
    """
    mention_dict = {}
    new_mention_dict = {}
    tagging_set = sorted(tagging_set, key=lambda x: len(x[0]), reverse=True)
    # 从长处理到短
    for mention, _type, norm_id, norm_name in tagging_set:
        if _type == 'Gene' and norm_id == '-':
            continue

        # 没见过这个mention
        if not mention_dict.get(mention):
            processed_flag = False
            new_mention_dict = mention_dict.copy()
            for (saved_mention, saved_type, saved_norm_id, saved_norm_name) in new_mention_dict.values():
                if re.match(r'\b' +  re.escape(mention) + r'\b', saved_mention):
                    processed_flag = True
                    # 新的小的有id
                    if norm_id != '-' and saved_norm_id == '-':
                        del mention_dict[saved_mention]
                        mention_dict[saved_mention] = (saved_mention, saved_type, norm_id, norm_name)
            if not processed_flag:
                mention_dict[mention] = (mention, _type, norm_id, norm_name)
            new_mention_dict = mention_dict.copy()
        #已经见过这个mention
        else:
            if norm_id == '-':
                continue
            saved_mention, saved_type, saved_norm_id, saved_norm_name = mention_dict[mention]

            # 新的norm_id不为空
            if saved_norm_id == '-':
                del mention_dict[mention]
                mention_dict[mention] = (mention, _type, norm_id, norm_name)
            # 都不为空
            else:
                # 如果新的这个不为MESH 就存这个
                if saved_norm_id.startswith('MESH:') and not norm_id.startswith('MESH:'):
                    del mention_dict[ mention ]
                    mention_dict[ mention ] = (mention, _type, norm_id, norm_name)
                # 都不为mesh 保留更大的数字
                elif not saved_norm_id.startswith('MESH:') and not norm_id.startswith('MESH:'):
                    try:
                        saved_num = re.findall(r'\d+', re.escape(saved_norm_id))[0]
                        norm_num = re.findall(r'\d+', re.escape(norm_id))[0]
                        if int(norm_num) > int(saved_num):
                            del mention_dict[ mention ]
                            mention_dict[ mention ] = (mention, _type, norm_id, norm_name)
                    except:
                        continue
                # 都为mesh 保留更大数字
                elif not saved_norm_id.startswith('MESH:') and not norm_id.startswith('MESH:'):
                    try:
                        saved_num = re.findall(r'\d+', re.escape(saved_norm_id))[0]
                        norm_num = re.findall(r'\d+', re.escape(norm_id))[0]
                        if int(norm_num) > int(saved_num):
                            del mention_dict[ mention ]
                            mention_dict[ mention ] = (mention, _type, norm_id, norm_name)
                    except:
                        continue

    filtered_set = set()
    for mention, t, norm_id, norm_name in mention_dict.values():
        filtered_set.add((mention, t, norm_id, norm_name))

    return filtered_set

def sent_to_tagging(id_pair_to_sent: dict, id_pair_to_ner: dict,
                    id_pair_to_oger: dict, id_to_pheno: dict,
                    pmid_to_tmvar: dict,
                    tagging_result: list, re_result: list,
                    filter_tagging_result: list,
                    non_normalized_mutation_syno_to_norm: dict,
                    hpo_oger_format: bool):
    """
    该代码可以通过分割id_pair_to_sent实现多进程

    1. 合并所有标注
    2. 标注融合 保存最长
    3. 句子筛选，至少包含 1个标准化gene 1个突变 1个调控词 1个其他类型标注（需要先统计标注类型）
    3. 生成 re 和 tagging文件
    """

    # 1. combine all tagging
    # (mention, type, norm_id)
    id_pair_to_total_tag = defaultdict(set)
    for id_pair, sentence in id_pair_to_sent.items():
        total_tag_set = set()

        pmid, sent_id = id_pair
        # print(f'{pmid} {sent_id}')

        ner_set = tag_stand(id_pair_to_ner[id_pair], non_normalized_mutation_syno_to_norm)
        # print(f'ner: {ner_set}')

        id_pair_to_total_tag[id_pair].update(ner_set)
        total_tag_set.update(ner_set)

        if id_pair_to_oger.get(id_pair):
            if id_pair_to_oger.get(id_pair):
                oger_tag_set = tag_stand(id_pair_to_oger[id_pair])
            else:
                oger_tag_set = set()
            # print(f'oger {oger_tag_set}')
            id_pair_to_total_tag[id_pair].update(oger_tag_set)
            total_tag_set.update(oger_tag_set)

        # HPO tagging with oger format
        if hpo_oger_format:
            if id_to_pheno.get(id_pair):
                pheno_tag_set = tag_stand(id_to_pheno[id_pair])
            else:
                pheno_tag_set = set()

            # print(f'PhenoTagSet: {pheno_tag_set}')
            id_pair_to_total_tag[id_pair].update(pheno_tag_set)
            total_tag_set.update(pheno_tag_set)
        else:
            # pheno 和 tmvar 的 tag 已经标准化过了
            if id_to_pheno.get(pmid):
                pheno_tag_set = id_to_pheno[pmid ]
                # print(f'pheno: {pheno_tag_set}')
                match_pheno_set = match_pubtator_ann(pheno_tag_set, sentence)

                id_pair_to_total_tag[id_pair].update(match_pheno_set)
                total_tag_set.update(match_pheno_set)
                # print(f'pheno match: {match_pheno_set}')

        if pmid_to_tmvar.get(pmid):
            tmvar_tag_set = pmid_to_tmvar[pmid]
            # print(f'tmvar: {tmvar_tag_set}')
            match_tmvar_set = match_pubtator_ann(tmvar_tag_set, sentence)
            id_pair_to_total_tag[id_pair].update(match_tmvar_set)
            total_tag_set.update(match_tmvar_set)

        filter_tag_set = filter_entities(total_tag_set)

        tag_wf = '\t'.join(map(str, filter_tag_set))
        tagging_result.append(f'{pmid}\t{sent_id}\t{sentence}\t{tag_wf}\n')

        if used_to_re(filter_tag_set):
            sent_re_set = generate_re(sentence, filter_tag_set, pmid, sent_id)

            for re_single in sent_re_set:
                re_result.append(re_single)

            filter_tagging_result.append(f'{pmid}\t{sent_id}\t{sentence}\t{tag_wf}\n')

def find_word_pos(sentence, word):
    match = re.search(re.escape(word), sentence)
    if match:
        start, end = match.span()
    else:
        start, end = 0, 0
    return start, end


def generate_re(sentence, tag_set, pmid, sent_id):
    """
    mention1 type1 (start1, end1) mention2 type2 (start2,end2) None sent pmid sent_id
    """
    # id convert to agac norm tag
    type_convert = {
        'Mutation': "Var",
        'Gene': 'Gene',
        'MPA': "MPA",
        'CPA': 'CPA',
        'Interaction': "Interaction",
        "Pathway": "Pathway",
        'Reg': "Reg",
        'NegReg': "NegReg",
        'PosReg': 'PosReg',
        'Protein': "Protein",
        "Disease": 'Disease',
        'phenotype': 'Disease',
    }

    gene_set = set()
    mutation_set = set()
    reg_set = set()
    other_set = set()
    for mention, _type, norm_id, norm_name in tag_set:

        if type_convert.get(_type):
            _type = type_convert[_type]
        else:
            print(f'"{_type} not in AGAC."')
            input()

        offset = find_word_pos(sentence, mention)
        if _type == 'Gene':
            gene_set.add((mention, _type, offset))
        elif _type == 'Var':
            mutation_set.add((mention, _type, offset))
        elif _type in {'Reg', 'PosReg', 'Reg'}:
                reg_set.add((mention, _type, offset))
        else:
            other_set.add((mention, _type, offset))

    sent_re_set = set()
    # gene-mutation
    sent_re_set.update(get_rs_for_to_set(gene_set, mutation_set, sentence, pmid, sent_id))
    # mutation-reg
    sent_re_set.update(get_rs_for_to_set(mutation_set, reg_set, sentence, pmid, sent_id))
    # reg-other
    # sent_re_set.update(get_rs_for_to_set(other_set, reg_set, sentence, pmid, sent_id))
    # sent_re_set.update(get_rs_for_to_set(other_set, gene_set, sentence, pmid, sent_id))
    sent_re_set.update(get_rs_for_to_set(other_set, reg_set, sentence, pmid, sent_id))
    # sent_re_set.update(get_rs_for_to_set(gene_set, other_set, sentence, pmid, sent_id))
    return sent_re_set

def get_rs_for_to_set(set1, set2, sentence, pmid, sent_id):
    """
    (mention, type, offset)
    """
    re_set = set()
    for entity1, entity2 in itertools.product(set1, set2):
        mention1, type1, offset1 = entity1
        mention2, type2, offset2 = entity2
        re_set.add(f'{mention1}\t{type1}\t{offset1}\t'
                   f'{mention2}\t{type2}\t{offset2}\t'
                   f'None\t{sentence}\t'
                   f'{pmid}\t{sent_id}\n')
    return re_set


def used_to_re(filter_tag_set):
    """
    判断一个句子是否用于ner
    至少有一个Gene 一个Mutation 一个Reg/PosReg/NegReg 和其他类型的
    """
    type_count = defaultdict(int)
    for (mention, _type, _, _) in filter_tag_set:
        if _type in {'Reg', 'PosReg', 'NegReg'}:
            _type = 'Reg'

        type_count[_type] += 1

    if type_count['Gene'] >= 1 and type_count['Mutation']>= 1 and type_count['Reg'] >= 1 and len(type_count) >= 4:
        return True
    else:
        return False

def single_cancer_process(ner_tagging_file: str, oger_tagging_file: str,
                          pheno_tagging_file: str, tmvar_tagging_file: str,
                          tagging_save_file: str, re_save_file: str,
                          filter_tagging_save_file: str, non_normalized_mutation_syno_to_norm: dict,
                          process_num: int, hpo_oger_format: bool):

    id_pair_to_sent, id_pair_to_ner = read_ner_tagging_file(ner_tagging_file)

    if file_exist(oger_tagging_file):
        id_pair_to_oger = read_oger_tagging_file(oger_tagging_file)
    else:
        print(f'Wrong: {oger_tagging_file} do not exists.')
        id_pair_to_oger = {}

    if file_exist(pheno_tagging_file):
        if hpo_oger_format:
            # if pair to pheno
            id_to_pheno = read_oger_tagging_file(pheno_tagging_file)
        else:
            # single pmid to pheno
            id_to_pheno = read_pheno_tagging_file(pheno_tagging_file)
    else:
        print(f'Wrong: {pheno_tagging_file} do not exists.')
        id_to_pheno = {}

    if file_exist(tmvar_tagging_file):
        pmid_to_tmvar = read_tmvar3_file(tmvar_tagging_file)
    else:
        print(f'Wrong: {tmvar_tagging_file} do not exists.')
        pmid_to_tmvar = {}

    if process_num > 1:
        key_list = list(id_pair_to_sent.keys())
        with Manager() as manager:
            re_result = manager.list()
            tagging_result = manager.list()
            filter_tagging_result = manager.list()

            process_list = []
            for i in range(process_num):
                batch_key = key_list[i::process_num]
                batch_id_pair_to_sent = {_key: id_pair_to_sent[_key] for _key in batch_key}

                process = Process(target=sent_to_tagging,
                                  args=(batch_id_pair_to_sent, id_pair_to_ner, id_pair_to_oger,
                                        id_to_pheno, pmid_to_tmvar,
                                        tagging_result, re_result,
                                        filter_tagging_result, non_normalized_mutation_syno_to_norm,
                                        hpo_oger_format))
                process.start()
                process_list.append(process)
                print(f'Process {i+1} started, batch-size: {len(batch_key)}')

            for process in process_list:
                process.join()

            with open(tagging_save_file, 'w') as wf:
                for tagging_line in tagging_result:
                    wf.write(tagging_line)

            with open(re_save_file, 'w') as wf:
                for re_line in re_result:
                    wf.write(re_line)

            with open(filter_tagging_save_file, 'w') as wf:
                for filter_tagging_line in filter_tagging_result:
                    wf.write(filter_tagging_line)

            print(f'{tagging_save_file} saved.')
            print(f'{re_save_file} saved.')
            print(f'{filter_tagging_save_file} saved.')

    else:
        print('Single process only used to deubg.')
        # only for test no return
        sent_to_tagging(id_pair_to_sent, id_pair_to_ner, id_pair_to_oger,
                        id_to_pheno, pmid_to_tmvar, [], [], [])


def file_exist(file):
    if os.path.exists(file):
        return True
    else:
        return False

def read_non_normalized_mutation_file(non_normalized_mutation_file: str):

    # syno: mutation_type:sub_mutation_type
    syno_to_norm = {}
    with open(non_normalized_mutation_file) as f:
        for line in f:
            l = line.strip().split('\t')
            if l == ['']:
                continue

            mutation_type = l[1]
            sub_mutation_type = l[3]
            # lowercase
            synonym_set = l[4].split('|')
            for syno in synonym_set:
                syno_to_norm[syno] = f'{mutation_type}:{sub_mutation_type}'
    return syno_to_norm

"""
python3 tagging_merge_for_re_input.py 
-ne ../../CancerPNRLE/big_data/agac_task1_tagging/agac_task1_tagging/ 
-og ../../OGER/PanCancer-GO-processed/total_process_dir/ 
-ph ../../OGER/PanCancer-HPO-processed/processed_dir/ 
-tm ../../CancerPNRLE/big_data/big_pubtator_tmvar3/ 
-sp ../../CancerPNRLE/big_data/big_re_input 
-pn 20 
-nm /home/kyzhou/xzyao/CancerPNRLE/data/non-normalized-mutation/MutationTypeDictionary20220711.txt  
-ho

"""


def main(ner_path: str, oger_path: str, pheno_path: str,
         tmvar_path: str, save_path: str, non_normalized_mutation_file: str,
         process_num: int, hpo_oger_format: bool):

    if not os.path.exists(save_path):
        os.makedirs(save_path, exist_ok=True)

    file_list = os.listdir(ner_path)

    non_normalized_mutation_syno_to_norm = read_non_normalized_mutation_file(non_normalized_mutation_file)

    # an independent function for multi process
    for idx, ner_tagging_file in enumerate(file_list):
        print(f'Processing: {os.path.basename(ner_tagging_file)}')
        # task1 ner tagging file
        cancer_name = ner_tagging_file.split('.')[0]
        # print(f'Process {idx} cancer: {cancer_name}')

        ner_file = f'{ner_path}/{ner_tagging_file}'

        # fixme: 20230531
        # oger_tagging_file = f'{oger_path}/{cancer_name}.oger-process.txt'
        oger_tagging_file = f'{oger_path}/{cancer_name}.tsv'

        # fixme: oger format for HPO tagging
        if hpo_oger_format:
            # pheno_tagging_file = f'{pheno_path}/{cancer_name}.tsv'
            pheno_tagging_file = f'{pheno_path}/{cancer_name}.HPO.tsv'
        else:
            pheno_tagging_file = f'{pheno_path}/{cancer_name}.pubtator.filter.txt'

        if os.path.isdir(tmvar_path):
            tmvar_file = f'{tmvar_path}/{cancer_name}.pubtator.txt'
        else:
            tmvar_file = tmvar_path

        tagging_save_file = f'{save_path}/{cancer_name}.tagging.txt'
        re_input_save_file = f'{save_path}/{cancer_name}.re.txt'
        filter_tagging_save_file = f'{save_path}/{cancer_name}.filter-tagging.txt'

        if os.path.exists(tagging_save_file) and os.path.exists(re_input_save_file) \
                and os.path.exists(filter_tagging_save_file):
            print(f'{re_input_save_file} existed.')
            continue

        single_cancer_process(ner_file, oger_tagging_file,
                              pheno_tagging_file, tmvar_file,
                              tagging_save_file, re_input_save_file,
                              filter_tagging_save_file, non_normalized_mutation_syno_to_norm,
                              process_num, hpo_oger_format)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-ne', dest='ner_path', required=True,
                        help='Task 1 processed path.')
    parser.add_argument('-og', dest='oger_path')
    parser.add_argument('-ph', dest='pheno_path')
    parser.add_argument('-tm', dest='tmvar_path')

    parser.add_argument('-sp', dest='save_path')

    parser.add_argument('-pn', dest='process_num', type=int, default=1)

    # fixme: already updated
    parser.add_argument('-nm', dest='non_normalized_mutation_file',
                        help='/home/kyzhou/xzyao/CancerPNRLE/data/non-normalized-mutation/MutationTypeDictionary20220711.txt')

    parser.add_argument('-ho', dest='hpo_oger_format', action='store_true',
                        default=False,
                        help='HPO tagging is OGER format? default: False.')

    args = parser.parse_args()



    main(args.ner_path, args.oger_path, args.pheno_path, args.tmvar_path,
         args.save_path, args.non_normalized_mutation_file, args.process_num,
         args.hpo_oger_format)



