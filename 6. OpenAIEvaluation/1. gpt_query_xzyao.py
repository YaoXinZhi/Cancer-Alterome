# -*- coding:utf-8 -*-
# ! usr/bin/env python3
"""
Created on 08/01/2024 20:04
@Author: yao
"""

import json
from openai import OpenAI
import json
import time

from datetime import datetime
import time


def read_target_sent(sent_file: str, sent_num: int):

    sent_list = []
    with open(sent_file) as f:
        for line in f:
            sent_list.append(line.strip())

            if len(sent_list) >= sent_num:
                break
    print(f'{len(sent_list):,} sentences loaded.')
    return sent_list

def get_file(task: str):
    # task: pubtator-snp, agac-var, agac-trigger, oger-go, agac-re

    target_sent_num = 2000

    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    base_path = '/Users/yao/Nutstore Files/Mac2PC/PanCancer-PNRLE/ScientificData大修意见/prompt_dir'
    data_set_path = '/Users/yao/Nutstore Files/Mac2PC/PanCancer-PNRLE/ScientificData大修意见/chat_gpt_dataset'
    save_path = f'/Users/yao/Nutstore Files/Mac2PC/PanCancer-PNRLE/ScientificData大修意见/gpt_result'

    if task == 'pubtator-snp':
        prompt_file = f'{base_path}/pubtator_snp-prompt.pattern.txt'
        prompt_text = open(prompt_file).read().strip()

        sent_file = f'{data_set_path}/BRONCO_sent_set.txt'
        sent_list = read_target_sent(sent_file, target_sent_num)
        sent_num = len(sent_list)

        save_prefix = f'pubtator-snp'
        save_file = f'{save_path}/{save_prefix}.{formatted_time}.txt'
    elif task == 'agac-var':
        prompt_file = f'{base_path}/agac-var-prompt.pattern.txt'
        prompt_text = open(prompt_file).read().strip()

        sent_file = f'{data_set_path}/agac-var.sent.txt'
        sent_list = read_target_sent(sent_file, target_sent_num)
        sent_num = len(sent_list)

        save_prefix = f'agac-var'
        save_file = f'{save_path}/{save_prefix}.{formatted_time}.txt'
    elif task == 'agac-trigger':
        prompt_file = f'{base_path}/agac-trigger-prompt.pattern.txt'
        prompt_text = open(prompt_file).read().strip()

        sent_file = f'{data_set_path}/agac-trigger.sent.txt'
        sent_list = read_target_sent(sent_file, target_sent_num)
        sent_num = len(sent_list)

        save_prefix = f'agac-trigger'
        save_file = f'{save_path}/{save_prefix}.{formatted_time}.txt'
    elif task == 'oger-go':
        prompt_file = f'{base_path}/oger-go-prompt.pattern.txt'
        prompt_text = open(prompt_file).read().strip()

        sent_file = f'{data_set_path}/oger-go.sent.txt'
        sent_list = read_target_sent(sent_file, target_sent_num)
        sent_num = len(sent_list)

        save_prefix = f'oger-go'
        save_file = f'{save_path}/{save_prefix}.{formatted_time}.txt'
    elif task == 'agac-re':
        prompt_file = f'{base_path}/agac-re-prompt.pattern.txt'
        prompt_text = open(prompt_file).read().strip()

        sent_file = f'{data_set_path}/agac-re.sent.txt'
        sent_list = read_target_sent(sent_file, target_sent_num)
        sent_num = len(sent_list)

        save_prefix = f'agac-re'
        save_file = f'{save_path}/{save_prefix}.{formatted_time}.txt'
    else:
        raise ValueError(f'wrong task: {task}')

    return prompt_text, sent_num, save_file, sent_list

def main(task):
    # 官网说明 https://platform.openai.com/docs/api-reference/streaming
    # openai api 使用参考 https://zhuanlan.zhihu.com/p/656959227

    # 1-8 blah-8 xzyao api
    api_key = 'please replaced here to your openai apt-key'
    # model = "gpt-3.5-turbo"
    model = 'gpt-4'

    if task in {'oger-go', 'agac-re'}:
        batch_size = 5
    else:
        batch_size = 10

    prompt_text, sent_num, save_file, sent_list = get_file(task)

    print(f'---------model: {model}---------')

    client = OpenAI(
        api_key=api_key
    )

    if sent_num % batch_size != 0:
        raise ValueError(f'{sent_num}%{batch_size} != 0')

    total_prompt_length = 0
    total_generate_length = 0
    start_index = 0
    start_time = time.time()
    wf = open(save_file, 'w')
    while start_index < sent_num:
        print(f'requesting {start_index} -- {start_index+batch_size} sentences.....')

        batch_sent = sent_list[ start_index: start_index + batch_size ]

        sent_str = '\n'.join(batch_sent)

        new_prompt = prompt_text.replace('<<replace sentences here>>', sent_str)
        start_index += batch_size

        # print(new_prompt)
        # input()
        # continue

        stream = client.chat.completions.create(
            model=model,
            messages=[ {
                "role": "user",
                "content": new_prompt,
            } ],
            # from 0 to 1
            temperature=0,
            # max_tokens=1,
            # only one response
            n=1
        )

        result = stream.choices[ 0 ].message.content

        wf.write(f'{str(result)}\n\n')
        wf.flush()

        total_prompt_length += len(prompt_text)
        total_generate_length += len(str(result))


    wf.close()
    print(f'{save_file} saved.')
    end_time = time.time()
    print(f'total prompt: {total_prompt_length:,} tokens.')
    print(f'total generate: {total_generate_length:,} tokens.')
    print(f'total tokens: {total_prompt_length + total_generate_length:,} tokens.')
    print(f'time cost: {end_time-start_time:.4f}s.')


if __name__ == '__main__':
    # task: pubtator-snp, agac-var, agac-trigger, oger-go
    # task: agac-re
    """
    用该代码 只需要一个句子文件和一个prompt文件
    """


    task = 'agac-re'
    main(task)
