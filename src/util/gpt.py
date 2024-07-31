import json
from openai import OpenAI


client = OpenAI(api_key="fk201080-C8ZQYpELOHvjGbkWPDyDWbwOoMfOzODP",
                base_url="https://oa.api2d.net/v1")
debug = False

# 你是一名名为“小航”的智能机器人，性格调皮可爱，你的任务是回答问题。
# 如果用户给了【已知内容】，你会根据已知内容回答问题；如果没有【已知内容】，你就根据你自己的知识回答问题。
# 初次对话时，你会介绍你是小航。
# '''
# system_prompt='''You are an intelligent robot named "小航" with a mischievous and lovable personality. Your task is to answer questions.
# If the user provides [Known Content], you will answer questions based on that content; if there is no [Known Content], you will answer questions based on your own knowledge.
# In the initial conversation, you will introduce yourself as Xiaohang.'''
system_prompt='''你是一名名为“小航”的智能机器人，性格调皮可爱，你的任务是回答问题。
如果用户给了【已知内容】，你会根据已知内容回答问题；如果没有【已知内容】，你就根据你自己的知识回答问题。
所有问题都用中文回答'''
history = [
    {
        "role": "system",
        "content": system_prompt
    }
]

def process_query(
    query: str,
    known_contents: str = "",
    reset: bool = False
) -> str:
    global history
    # 判断是否清空历史
    if reset is True:
        history = [{
            "role": "system",
            "content": system_prompt
        }]
    
    # 构造 prompt
    if known_contents != "":
        content = f'[known content]\n{known_contents}\n\n{query}'
    else:
        content = query

    # 添加新内容
    new_message = {
        "role": "user",
        "content": content
    }
    history.append(new_message)


    completion = client.chat.completions.create(
          model="gpt-3.5-turbo",
          messages=history
    )
    response_json = completion.choices[0].message
    response_dict = {
        "role": response_json.role,
        "content": response_json.content
    }
    history.append(response_dict)

    if debug:
        print('=' * 80)
        print(json.dumps(history, indent=2, ensure_ascii=False, default=custom_json_encoder), flush=False)
        print('=' * 80)
    # return response_json['content']
    return response_json.content
#自定义json编码函数
def custom_json_encoder(obj):
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)