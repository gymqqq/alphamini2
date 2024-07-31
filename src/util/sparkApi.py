import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
import os
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import log_path
from loguru import logger

import websocket  # 使用websocket_client

answer = ''
ans_file = ''


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = (f'api_key="{self.APIKey}",'
                                f'algorithm="hmac-sha256",'
                                f'headers="host date request-line", '
                                f'signature="{signature_sha_base64}"')

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.Spark_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# 收到 websocket 错误的处理
def on_error(ws, error):
    # print(ans_file, "### error:", error)
    logger.error(error)
    print_ans(log_path, "### error:", error)
    exit(1)


# 收到 websocket 关闭的处理
def on_close(ws, one, two):
    logger.info('Websocket closed.')
    print_ans(log_path, " ")
    # print(ans_file, " ")


# 收到 websocket 连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)


# 收到 websocket 消息的处理
def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        logger.error(f'请求错误: {code}, {data}')
        print_ans(log_path, f'请求错误: {code}, {data}')
        # print(ans_file, f'请求错误: {code}, {data}', flush=True)
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        # print(content, end="")
        # print_ans(ans_file, content, end="")
        global answer
        answer += content
        if status == 2:
            ws.close()


def gen_params(appid, domain, question):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": domain,
                # "random_threshold": 0.5,
                "temperature": 0.9,
                "max_tokens": 1024,
                "top_k": 4,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


# 用于替换 print(), 将内容写入特定文件
def print_ans(ans_file_name, *args, sep=' ', end='\n'):
    with open(ans_file_name, 'a', encoding='utf-8') as file:
        content = sep.join(map(str, args))
        file.write(content)
        file.write(end)


def main(appid, api_key, api_secret, Spark_url, domain, question, _ans_file):
    global ans_file
    ans_file = _ans_file

    # 创建 WebSocket 参数对象
    wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)

    # 关闭 WebSocket 调试信息输出
    websocket.enableTrace(False)

    # 创建 WebSocket 的 URL
    wsUrl = wsParam.create_url()

    # 创建 WebSocketApp 对象，设置相应的回调函数
    ws = websocket.WebSocketApp(
        wsUrl,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    # 将参数保存到 WebSocket 对象的属性中
    ws.appid = appid
    ws.question = question
    ws.domain = domain

    # 开始运行 WebSocket 连接，直到连接关闭
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
