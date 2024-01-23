# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 02/02/2023 17:03
@Author: yao
"""

import os
import re

import argparse
import time
from collections import defaultdict

from multiprocessing import Manager, Process


"""
该代码用于将任务二产生的链条文件生成数据库

数据库文件包含
Gene Mutation RegType Phenotype PhenotypeID PMID SentID Sentence RichSentence
"""

def type_check(element, _type):
    if element[1] == _type:
        return True
    else:
        return False


def chain_parser(chain_list):
    """
    Gene Mutation RegType Phenotype PhenotypeID PMID SentID Sentence RichSentence
    """

    gene, _, var, _, reg, _, phenotype = chain_list

    gene = eval(gene)
    var = eval(var)
    reg = eval(reg)
    phenotype = eval(phenotype)

    if not type_check(gene, "Gene") or not type_check(var, "Var") \
            or not reg[1] in {'Reg', 'PosReg', 'NegReg'} \
            or phenotype[1] in {'Gene', 'Var', 'Reg', 'PosReg', 'NegReg'}:
        # print(chain_list)
        # input()
        return False

    mention_set = {gene[0], var[0], reg[0], phenotype[0]}

    gene_symbol = gene[3][0]

    # todo: add non-normalized var
    # ('epigenetics', 'Var', '(36, 47)',
    # ('epigenetics', 'Mutation', 'epigenic marks:epigenetics', 'epigenic marks:epigenetics'))
    if var[3][2] == '-':
        var_id = var[3][1]
        # fixme: delete non-normalized mutation
    else:
        var_id = var[3][2]

    reg_type = reg[1]

    phenotype_name = phenotype[3][0]
    if phenotype[3][2] == '-':
        phenotype_id = '-'
    else:
        phenotype_id = phenotype[3][2]

    return mention_set, gene_symbol, var_id, reg_type, phenotype_id, phenotype_name

def get_rich_text(mention_set: set, sentence: str):
    # mention 里的词被加粗

    # mention_set = {'DNMT3A', 'p.Gly332Arg', 'TET2', 'loss-of-function', 'Gly332Arg', 'p.Arg882'}
    # sentence = 'To explore this, we profiled one AML sample carrying the p.Gly332Arg DNMT3A variant (this sample also carries another DNMT3A variant and two frameshift variants in TET2), with AML samples extracted from TCGA and carriers of DNMT3A somatic variants known to cause global methylation alterations (i.e., the bona fide p.Arg882 DNMT3A loss-of-function alteration).'

    # 先给长的mention加粗 这样避免包含关系
    sorted_mention_list = list(sorted(mention_set, key=lambda x: len(x), reverse=True))

    # mentions_regex = '|'.join(map(re.escape, sorted_mention_list))
    mentions_regex = r'\b(' + '|'.join(map(re.escape, sorted_mention_list)) + r')\b'

    # rich_sentence = re.sub(mentions_regex, r"<b>\g<0></b>", sentence, flags=re.IGNORECASE)
    rich_sentence = re.sub(mentions_regex, r"<b>\1</b>", sentence, flags=re.IGNORECASE)

    return rich_sentence

def multi_chain_file_process(chain_file_list: str, db_result: list):

    for chain_file in chain_file_list:
        cancer_name = os.path.basename(chain_file).split('.')[0]
        record_num = 0
        print(f'Processing: {cancer_name}')
        with open(chain_file) as f:
            for line in f:
                l = line.strip().split('\t')
                if l == ['']:
                    continue

                pmid = l[0]
                sent_id = l[1]
                sentence = l[2]

                chain_list = l[3:]
                # Gene ThemeOf Var CauseOf Reg ThemeOf Phenotype
                if len(chain_list) != 7:
                    continue

                chain_parser_result = chain_parser(chain_list)
                if not chain_parser_result:
                    continue
                mention_set, gene_symbol, var_id, reg_type, \
                phenotype_id, phenotype_name = chain_parser_result

                rich_sentence = get_rich_text(mention_set, sentence)

                record = f'{gene_symbol}\t{cancer_name}\t' \
                         f'{var_id}\t{reg_type}\t' \
                         f'{phenotype_name}\t{phenotype_id}\t' \
                         f'{pmid}\t{sent_id}\t' \
                         f'{sentence}\t{rich_sentence}\n'
                db_result.append(record)
                record_num += 1

        print(f'{cancer_name} have {record_num:,} chain records.')


def main(chain_path: str, save_file: str,
         process_num: int):

    file_list = os.listdir(chain_path)

    file_list = [f'{chain_path}/{file}' for file in file_list]

    # todo: read no normalized mutation

    print(f'Total File: {len(file_list):,}')
    with Manager() as manager:
        db_result = manager.list()

        process_list = []
        for i in range(process_num):
            batch_data = file_list[i::process_num]

            process = Process(target=multi_chain_file_process,
                              args=(batch_data, db_result))

            process.start()
            process_list.append(process)
            print(f'Process {i+1} started, batch files: {len(batch_data):,}.')

        for process in process_list:
            process.join()

        with open(save_file, 'w') as wf:

            ## Gene Mutation RegType Phenotype PhenotypeID PMID SentID Sentence RichSentence
            wf.write('Gene\tCancer\t'
                     'Mutation\tRegType\t'
                     'Phenotype\tPhenotypeID\t'
                     'PMID\tSentID\t'
                     'Sentence\t'
                     'RichSentence\n')

            for line in db_result:
                wf.write(line)

        print(f'{save_file} saved.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ca', dest='chain_path', required=True)
    parser.add_argument('-sf', dest='save_file', required=True)

    parser.add_argument('-pn', dest='process_num', default=8,
                        type=int)
    args = parser.parse_args()

    main(args.chain_path, args.save_file, args.process_num)

