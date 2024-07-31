import os
import random
from typing import Any, Generator, List, Dict

import dashscope
from http import HTTPStatus

from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.utils import timezone
from ninja import NinjaAPI, Router, ModelSchema
from dashscope import Generation
from pydantic import BaseModel
from system.models import Users
from openai import OpenAI
from enum import Enum

from .models import Session
from .models import Message

from .ss_check.sensitive_check import build_automaton, load_automaton
from .ss_check.sensitive_check import check_sensitive_words
from .treesitter_analysor import analysor
from .treesitter_analysor.c_graph_node import Struct, Phrase, Branch
from utils.usual import get_user_info_from_token

router = Router()

# qwen_api_key
dashscope.api_key = 'sk-de7f7f8ce974478cbf9c0668297ccc0c'

# openAI_api_key
client = OpenAI(
    api_key='fk201080-C8ZQYpELOHvjGbkWPDyDWbwOoMfOzODP',
    base_url='https://oa.api2d.net/v1'
)
openai_config = {
    'temperature': 0.75,
    'top_p': 0.9,
}


class Mode(Enum):
    OPENAI = 1
    QWEN = 2


# 全局prompt
f = open("./progmate/system_prompt.md", "r", encoding='utf-8')
head_content = f.read()
f.close()


class Query(BaseModel):
    session_id: int
    type: int
    task_type: int
    problem: str
    code: str
    text: str
    history: List[Dict[str, str]]


def prompt_init() -> Dict[str, str]:
    sys_prompt = {"role": "system", "content": head_content}
    return sys_prompt


def pre_check(content: str) -> bool:
    # 检查是否已有存好的自动机
    if not os.path.exists('automaton.pickle'):
        A = build_automaton('./progmate/ss_check/sensitive_words_lines.txt')
    # 从文件读取自动机
    else:
        A = load_automaton('./progmate/ss_check/automaton.pickle')
    return check_sensitive_words(text=content, automaton=A)


def pre_warning(query: Query) -> str:
    warning = "请检查你的问题是否含有敏感词等问题，本次行为将被记录上报"
    session = Session.objects.get(pk=query.session_id)
    # 数据库操作，写入两条,一条user的query.text，加上warning_flag，一条assistance的warning
    user_message = Message.objects.create(session=session,
                                          time=timezone.now(),
                                          role="user",
                                          content=query.text,
                                          true_content=query.text,
                                          sensitive_flag=1,
                                          task_type=query.task_type)
    user_message.save()
    assistant_message = Message.objects.create(session=session,
                                               time=timezone.now(),
                                               role="assistant",
                                               content=warning,
                                               true_content=warning,
                                               sensitive_flag=0,
                                               task_type=query.task_type)
    assistant_message.save()
    yield warning


def distribute(query: Query) -> Generator[Any, Any, None]:
    if query.type == 0:
        return basic_qa(query)
    elif query.type == 1:
        if query.task_type == 1:
            return code_explain(query)
        elif query.task_type == 2:
            return code_fix(query)
        elif query.task_type == 3:
            return code_help(query)
    raise Exception("query.type or query.task_type Error")


def basic_qa(query: Query) -> Generator[Any, Any, None]:
    """
    实现基本的问答功能（代码解释、知识点问答）
    """
    content = query.text
    return call_stream_with_messages(content, query)


def code_explain(query: Query) -> Generator[Any, Any, None]:
    """
    代码解释，根据学生的询问，回答代码相关功能
    """
    content = f"""### Problem\n{query.problem}\n### Code of the student\n{query.code}\n### Instruction of the student\n{query.text}\n### Caution\n注意请偏向于解释代码，绝对不要直接给出任何原文以外的c语言代码，如果需要，请使用伪代码代替。"""
    return call_stream_with_messages(content, query)


def code_fix(query: Query) -> Generator[Any, Any, None]:
    """
    代码修复，根据学生的询问，回答可能的建议
    """
    content = f"""### Problem\n{query.problem}\n### Code of the student\n{query.code}\n### Instruction of the student\n{query.text}\n### Caution\n注意请偏向于代码纠错，绝对不要直接给出修复后的c语言代码，如果需要，请使用伪代码代替。"""
    return call_stream_with_messages(content, query)


def code_help(query: Query) -> Generator[Any, Any, None]:
    """
    子任务分解，根据题目和学生询问，提供子任务分解
    """
    # TODO
    manual = ''
    if manual == '':
        content = f"""### Problem\n{query.problem}\n### Instruction of the student\n{query.text}\n### Caution\n注意绝对不要直接给出修复后的c语言代码，如果需要，请使用伪代码代替。"""
    else:
        content = f"""### Problem\n{query.problem}\n### Manual subtask decomposition\n{manual} ### Instruction of the student\n{query.text}\n### Caution\n你可以参考上述助教给出的人工子任务分解。注意绝对不要直接给出修复后的c语言代码，如果需要，请使用伪代码代替。"""
    return call_stream_with_messages(content, query)


def save_to_mysql(content: str, cur_content: str, query: Query):
    try:
        session = Session.objects.get(pk=query.session_id)
        user_message = Message.objects.create(session=session,
                                              time=timezone.now(),
                                              role="user",
                                              content=content,
                                              true_content=query.text,
                                              sensitive_flag=0,
                                              task_type=query.task_type)
        user_message.save()
        assistant_message = Message.objects.create(session=session,
                                                   time=timezone.now(),
                                                   role="assistant",
                                                   content=cur_content,
                                                   true_content=cur_content,
                                                   sensitive_flag=0,
                                                   task_type=query.task_type)
        assistant_message.save()
        # print("saved...")
    except Session.DoesNotExist:
        print(f"Session {query.session_id} not found.")


def qwen_api(content: str, query: Query) -> Generator[Any, Any, None]:
    responses = Generation.call(
        'qwen1.5-72b-chat',
        messages=query.history,
        seed=random.randint(1, 10000),
        result_format='message',
        stream=True,
        output_in_full=True
    )
    last_content = ''
    cur_content = ''
    for response in responses:
        if response.status_code == HTTPStatus.OK:
            cur_content = response.output.choices[0]['message']['content']
            new_content = cur_content.replace(last_content, '')
            last_content = cur_content
            # print(new_content, end='')
            yield new_content.encode('utf-8')
        else:
            print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                response.request_id, response.status_code,
                response.code, response.message
            ))
    save_to_mysql(content, cur_content, query)


def openai_api(content: str, query: Query) -> Generator[Any, Any, None]:
    query.history.insert(0, prompt_init())
    query.history.append({'role': 'user', 'content': content})
    responses = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=query.history,
        stream=True,
        **openai_config
    )
    full_content = ''
    for response in responses:
        cur_content = ''
        try:
            cur_content = response.choices[0].delta.content
            if not cur_content:
                cur_content = ''
        except:
            pass
        finally:
            full_content += cur_content
            yield cur_content

    save_to_mysql(content, full_content, query)


def call_stream_with_messages(content: str, query: Query, mode=Mode.OPENAI) -> Generator[Any, Any, None]:
    if mode == Mode.QWEN:
        return qwen_api(content, query)
    elif mode == mode.OPENAI:
        return openai_api(content, query)


@router.get("/progmate/session_id")
def get_session_id(request, type: int):
    user_info = get_user_info_from_token(request)
    user_id = user_info['id']
    user = Users.objects.get(pk=user_id)
    session = Session.objects.create(user=user, visible=1, type=type, score=-1)
    session.save()
    return {"session_id": session.pk}


@router.post("/progmate/qwen")
def ask_qwen(request, query: Query):
    # 校验
    user_info = get_user_info_from_token(request)
    session = Session.objects.get(pk=query.session_id)
    assert session.user_id == user_info['id']
    # 前审查
    if pre_check(query.text):
        return StreamingHttpResponse(pre_warning(query), content_type='text/event-stream')
    # 调用API
    return StreamingHttpResponse(distribute(query), content_type='text/event-stream')


def c_dfs(pre_node, post_node, node_list, edge_list, label, func_name):
    global edge_count, search_list
    nodes = node_list
    edges = edge_list
    if post_node is not None:
        if isinstance(post_node, Struct):
            if pre_node is None:
                temp_node = Struct('start', 0, 'any', 0)
                nodes, edges = c_dfs(temp_node, post_node.entry, nodes, edges, label, func_name)
            elif pre_node.depth > post_node.depth:
                temp_node = pre_node
                temp_node.depth = post_node.depth
                nodes, edges = c_dfs(temp_node, post_node.child, nodes, edges, label, func_name)
            else:
                temp_node = pre_node
                temp_node.depth = post_node.depth
                nodes, edges = c_dfs(temp_node, post_node.entry, nodes, edges, label, func_name)
        elif isinstance(post_node, Phrase) or isinstance(post_node, Struct):
            if pre_node is None:
                nodes.append({
                    'id': post_node.id,
                    'type': 'input',
                    'data': {'label': post_node.text}
                })
                search_list.append(post_node)
                nodes, edges = c_dfs(post_node, post_node.child, nodes, edges, None, func_name)
            elif post_node in search_list:
                if label is None:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id
                    })
                    edge_count += 1
                else:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id,
                        'label': label
                    })
                    edge_count += 1
            else:
                nodes.append({
                    'id': post_node.id,
                    'sourcePosition': 'top',
                    'targetPosition': 'bottom',
                    'data': {'label': post_node.text}
                })
                if label is None:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id
                    })
                    edge_count += 1
                else:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id,
                        'label': label
                    })
                    edge_count += 1
                search_list.append(post_node)
                nodes, edges = c_dfs(post_node, post_node.child, nodes, edges, None, func_name)
        elif isinstance(post_node, Branch):
            if pre_node is None:
                nodes.append({
                    'id': post_node.id,
                    'type': 'input',
                    'data': {'label': post_node.text}
                })
                search_list.append(post_node)
                nodes, edges = c_dfs(post_node, post_node.branch_true, nodes, edges, 'y', func_name)
                nodes, edges = c_dfs(post_node, post_node.branch_false, nodes, edges, 'n', func_name)
            elif post_node in search_list:
                if label is None:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id
                    })
                    edge_count += 1
                else:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id,
                        'label': label
                    })
                    edge_count += 1
            else:
                nodes.append({
                    'id': post_node.id,
                    'sourcePosition': 'top',
                    'targetPosition': 'bottom',
                    'data': {'label': post_node.text}
                })
                if label is None:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id
                    })
                    edge_count += 1
                else:
                    edges.append({
                        'id': func_name + str(edge_count),
                        'source': pre_node.id,
                        'animated': True,
                        'target': post_node.id,
                        'label': label
                    })
                    edge_count += 1
                search_list.append(post_node)
                nodes, edges = c_dfs(post_node, post_node.branch_true, nodes, edges, 'y', func_name)
                nodes, edges = c_dfs(post_node, post_node.branch_false, nodes, edges, 'n', func_name)
    return nodes, edges


edge_count = 0
search_list = []


class CodeQuery(BaseModel):
    code: str


@router.post("/progmate/code_graph")
def code_analyse(request, codequery: CodeQuery):
    global edge_count, search_list
    function_list = []
    funcs = analysor.analyse_code(codequery.code)
    for func in funcs:
        function_entity = {
            'name': func.function_name,
            'node_list': None,
            'edge_list': None
        }
        node_list = []
        edge_list = []
        t = func.entry
        edge_count = 0
        search_list = []
        node_list, edge_list = c_dfs(None, t, node_list, edge_list, None, func.function_name + '_e_')
        function_entity['node_list'] = node_list
        function_entity['edge_list'] = edge_list
        function_list.append(function_entity)
    return {
        'function_list': function_list,
    }
