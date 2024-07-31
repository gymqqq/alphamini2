import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Tuple, List
from config.config import knowledge_txt_path, knowledge_pkl_path
from util.encode import load_embedding
from util import spark, sparkApi
from util import gpt
# from ASR_google import speech_to_text
from ASR_xunfei import get_result
from TTS import _tts
import asyncio
import aiofiles
# 读取知识库
def load_knowledge() -> Tuple[List, List]:
    with open(knowledge_txt_path, 'r', encoding='utf-8') as f1, open(knowledge_pkl_path, 'rb') as f2:
        knowledge = [line.strip() for line in f1.readlines()]
        encoded_knowledge = pickle.load(f2)
    return knowledge, encoded_knowledge


# 召回 top_k 个相关的文本段
def find_top_k(emb: SentenceTransformer, query: str,
               knowledge: list, encoded_knowledge: list,
               k=2) -> List[str]:
    # 编码 query
    instruction = "为这个句子生成表示以用于检索相关文章："
    query_embedding = emb.encode(instruction + query)

    # 查找 top_k
    scores = query_embedding @ encoded_knowledge.T
    # 使用 argpartition 找出每行第 k 个大的值的索引，第 k 个位置左侧都是比它大的值，右侧都是比它小的值
    top_k_indices = np.argpartition(scores, -k)[-k:]
    # 由于 argpartition 不保证顺序，我们需要对提取出的 k 个索引进行排序
    top_k_values_sorted_indices = np.argsort(scores[top_k_indices])[::-1]
    top_k_indices = top_k_indices[top_k_values_sorted_indices]

    # 返回
    contents = [knowledge[index] for index in top_k_indices]
    return contents
    

def main():
    emb = load_embedding()
    knowledge, encoded_knowledge = load_knowledge()
    #query = "悟空悟空，我想知道怎么参观北航校史馆"
    #query = "悟空悟空， 我想知道北航杭州校区"
    #query = "悟空悟空, 给我讲个笑话吧"
    query = get_result()
    contents = find_top_k(emb, query, knowledge, encoded_knowledge, 2)
    #print(contents)
    # 讯飞星火
    spark.process_query(query, contents)
    response = sparkApi.answer
    print(response)

    # ChatGPT
    #response = gpt.process_query(query, contents, reset=False)
    #print(response)
    asyncio.run(_tts(response))

def query(text):
    emb = load_embedding()
    knowledge, encoded_knowledge = load_knowledge()
    # query = get_result()
    contents = find_top_k(emb, text, knowledge, encoded_knowledge, 2)

    # ChatGPT
    response = gpt.process_query(query, contents, reset=False)
    return response

if __name__ == '__main__':
    main()
