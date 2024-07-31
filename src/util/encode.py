import pickle
from loguru import logger
from sentence_transformers import SentenceTransformer
import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import embedding_path
from config.config import knowledge_txt_path, knowledge_pkl_path


def load_embedding() -> SentenceTransformer:
    logger.info('Loading embedding...')
    emb = SentenceTransformer(embedding_path)
    logger.info('Embedding loaded.')
    return emb


def encode():
    emb = load_embedding()
    with open(knowledge_txt_path, 'r', encoding='utf-8') as f:
        read_lines = f.readlines()
    
    lines = []
    for line in read_lines:
        line = line.strip()
        temp = line.split(',')[0]
        temps = ['北航', '博物馆', '航博', '校史馆','杭州','中法航空学院']
        if not any(t in temp for t in temps):
            line = '北航' + line
        lines.append(line)
    encoded_knowledge = emb.encode([line for line in lines])
    with open(knowledge_pkl_path, 'wb') as f:
        pickle.dump(encoded_knowledge, f)

if __name__ == '__main__':
    encode()
    print("task done!")