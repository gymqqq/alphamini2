import os
import time
import random
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from util import sparkApi


# 以下密钥信息从控制台获取
appid = '3f9e5e77'  # 填写控制台中获取的 APPID 信息
# noinspection SpellCheckingInspection
api_secret = 'NzhmNjgxYTc2NjFkMzI2NGNmZWU4YzU4'  # 填写控制台中获取的 APISecret 信息
api_key = '8ff7bf9d6d4da8839007044e8ecd4728'  # 填写控制台中获取的 APIKey 信息

# 选择版本：v1.5 / v2.0
version = 'v2.0'
if version == 'v2.0':
    # noinspection SpellCheckingInspection
    domain = 'generalv2'  # v2.0版本
    Spark_url = 'ws://spark-api.xf-yun.com/v2.1/chat'  # v2.0环境的地址
else:
    domain = 'general'  # v1.5版本
    Spark_url = 'ws://spark-api.xf-yun.com/v1.1/chat'  # v1.5环境的地址

cur_dir = os.path.dirname(os.path.abspath(__file__))

text = []

def get_text(role, content):
    json_context = {
        'role': role,
        'content': content
    }
    text.append(json_context)
    return text


def get_length(context):
    length = 0
    for content in context:
        temp = content['content']
        temp_length = len(temp)
        length += temp_length
    return length


def check_length(context):
    while get_length(context) > 8000:
        del context[0]
    return context


def read_code_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        code_list = f.readlines()
    code = ''.join(code_list)
    return code


def send_content(content, ans_file):
    try:
        question = check_length(get_text('user', content))
        sparkApi.answer = ''
        # print('星火: ', end='')
        sparkApi.main(appid, api_key, api_secret, Spark_url, domain, question, ans_file)
        get_text('assistant', sparkApi.answer)
    except Exception as e:
        print(f'Exception: {str(e)}', flush=True)


def generate_query(s: list, q: str) -> str:
    contents = '\n'.join(s)
    return f"已知内容：{contents}\n问题：{q}\n要求：直接回答问题，不要有多余的输出。"


def recognition_prompt() -> str:
    return f"你是一名名为“小航”的智能机器人，性格调皮可爱，你的任务是回答问题。\
如果用户给了【已知内容】，你会根据已知内容回答问题；如果没有【已知内容】，你就根据你自己的知识回答问题。\
所有问题都用中文回答\n\n"


def process_query(question: str, contents: list):
    text.clear()
    query = generate_query(contents, question)
    rec_prompt = recognition_prompt()
    send_content(rec_prompt + query, "")
