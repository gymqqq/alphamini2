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
async def load_knowledge() -> Tuple[List, List]:
    async with aiofiles.open(knowledge_txt_path, 'r', encoding='utf-8') as f1, \
             aiofiles.open(knowledge_pkl_path, 'rb') as f2:
        knowledge = [await f1.readline() for _ in range(f1.total_lines())]
        encoded_knowledge = await f2.read()
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
    

async def main():
    emb, knowledge, encoded_knowledge, query = await asyncio.gather(
        load_embedding(),
        load_knowledge(),
        get_result()
    )
    contents = find_top_k(emb, query, knowledge, encoded_knowledge, 2)
    #print(contents)
    # 讯飞星火
    #spark.process_query(query, contents)
    #print(sparkApi.answer + 'answer')

    # ChatGPT
    response = gpt.process_query(query, contents, reset=False)
    print(response)
    await _tts(response)

# if __name__ == '__main__':
#     main()
asyncio.run(main())