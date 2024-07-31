import os
cur_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(cur_dir)
base_dir = os.path.dirname(src_dir)
embedding_path = 'D:/Code/Android_new/model/embedding/bge-large-zh-v1.5'
# embedding_path = "http://10.70.250.249:8090/embedding/bge-large-zh-v1.5/"
# embedding_path = 'http://10.70.250.249/models/bge-large-zh-v1.5'
# embedding_path = 'https://api-inference.huggingface.co/models/BAAI/bge-large-zh-v1.5'
data_dir = os.path.join(base_dir, 'data')
knowledge_txt_path = os.path.join(data_dir, 'knowledge.txt')
knowledge_pkl_path = os.path.join(data_dir, 'knowledge.pkl')

log_dir = os.path.join(base_dir, 'log')
log_path = os.path.join(log_dir, 'log.log')
