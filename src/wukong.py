import asyncio
import logging
import random
import pickle
import numpy as np
import concurrent.futures
from sentence_transformers import SentenceTransformer
from typing import Tuple, List
from config.config import knowledge_txt_path, knowledge_pkl_path
from util.encode import load_embedding
from util import gpt
from util.read import read_speechwords
from util import spark, sparkApi
from util.translate import translate_text
import mini.mini_sdk as MiniSdk
from mini import SpeechRecogniseResponse, MiniApiResultType
from mini.apis import errors
from mini.apis.api_observe import ObserveHeadRacket, HeadRacketType, ObserveSpeechRecognise
from mini.dns.dns_browser import WiFiDevice
from mini.pb2.codemao_observeheadracket_pb2 import ObserveHeadRacketResponse
from mini.apis.api_sound import StartPlayTTS
from mini.apis.api_sound import RobotAudioStartPlay, RobotAudioStartRecord, RobotAudioStopRecord, PlayAudio, AudioStorageType, RobotAudioStartPlay
from mini.apis.api_observe import ObserveSpeechRecognise
from mini.mini_sdk import play_action
from mini.apis.api_sound import StartPlayTTS, StopPlayTTS, ControlTTSResponse
from mini.apis.api_action import PlayAction, PlayActionResponse
from TTS import _tts
from main import query
from ASR_xunfei import get_result

async def test_connect(dev: WiFiDevice) -> bool:
    """连接设备
    连接指定的设备
    Args:
        dev (WiFiDevice): 指定的设备对象 WiFiDevice
    Returns:
        bool: 是否连接成功
    """


    return await MiniSdk.connect(dev)


async def shutdown():
    """断开连接并释放资源
    断开当前连接的设备，并释放资源
    """
    await MiniSdk.quit_program()
    await MiniSdk.release()


async def test_get_device_by_name():
    """根据机器人序列号后缀搜索设备
    搜索指定序列号(在机器人屁股后面)的机器人, 可以只输入序列号尾部字符即可,长度任意, 建议5个字符以上可以准确匹配, 10秒超时
    Returns:
        WiFiDevice: 包含机器人名称,ip,port等信息
    """
    result: WiFiDevice = await MiniSdk.get_device_by_name("103254", 10)
    print(f"test_get_device_by_name result:{result}")
    return result


async def test_start_run_program():
    """进入编程模式demo
    使机器人进入编程模式，等待回复结果，并延时6秒，让机器人播完"进入编程模式"
    Returns:
        None:
    """
    await MiniSdk.enter_program()


# 测试, 触摸监听
async def test_ObserveHeadRacket():
    # 创建监听
    observer: ObserveHeadRacket = ObserveHeadRacket()
    # observer_speech: ObserveSpeechRecognise = ObserveSpeechRecognise()

    data = []

    # 事件处理器
    # ObserveHeadRacketResponse.type:
    # @enum.unique
    # class HeadRacketType(enum.Enum):
    #     SINGLE_CLICK = 1  # 单击
    #     LONG_PRESS = 2  # 长按
    #     DOUBLE_CLICK = 3  # 双击

    # def handler_speech(msg):
    #     print(f'{msg.text}')
    #     data.append(msg.text)

    def handler(msg: ObserveHeadRacketResponse): # type: ignore
        print("{0}".format(str(msg.type)))
        if msg.type == HeadRacketType.SINGLE_CLICK.value:
            # observer_speech.start()
            print("单击成功")
            text = get_result()
            print(text)
            if '演讲稿' in text:
                 asyncio.create_task(read_speechwords())
                 print(text)
                 pass
            else:
                 asyncio.create_task(get_response(text))

            # data.append(text)
            # start_rec = RobotAudioStartRecord(time_limit=5000)
            # asyncio.create_task(start_rec.execute())

        if msg.type == HeadRacketType.LONG_PRESS.value:
            asyncio.create_task(play_action('action_013'))
            pass
            # reset

        # if msg.type == HeadRacketType.DOUBLE_CLICK.value:

        #     # asyncio.create_task(RobotAudioStartPlay(file_name='record_1701796347752').execute())

        #     # observer_speech.stop()
        #     if '演讲稿' in text:
        #         asyncio.create_task(read_speechwords())
        #         print(text)
        #         pass
        #     else:
        #         text = ''.join(data)
        #         asyncio.create_task(get_response(text))


    observer.set_handler(handler)
    # observer_speech.set_handler(handler_speech)
    # 启动
    observer.start()
    await asyncio.sleep(0)


async def get_response(text):
    text = '小航小航' + text
    global emb
    global knowledge,encoded_knowledge
    contents = find_top_k(emb, text, knowledge, encoded_knowledge, 2)
    flag = 0
    # ans = gpt.process_query(text, contents, reset=False)
    if '法语' in text :
        text = text.replace("法语","中文")
        flag = 1
    spark.process_query(text, contents)

    ans = sparkApi.answer
    print(f'ans: {ans}')
    if flag:
        # loop = asyncio.get_event_loop()
        # fu1 = loop.run_in_executor(None, translate_text(text))
        # ans = await fu1
        ans = translate_text(ans)
        print(ans)
        voice = 'Charline'
    else:
        voice = 'xiaoyi'
    f = random.random()
    print(f'f = {f}')
    name = 'action_020'

    if f < 0.2:
        pass
    elif f < 0.4:
        name = '011'
    elif f < 0.6:
        name = '021'
    elif f < 0.8:
        name = 'action_005'
    else:
        name = 'action_013'


    block: PlayAction = PlayAction(action_name='action_014', is_serial=False)
    await block.execute()

    await asyncio.gather(
        play_online_audio(ans,voice),
        play_action(name)
    )
    # block: StartPlayTTS = StartPlayTTS(text=ans)
    # # 返回元组, response是个ControlTTSResponse
    # (resultType, response) = await block.execute()


async def play_online_audio(text,voice):
    """测试播放在线音效
    使机器人播放一段在线音效，支持格式有mp3,amr,wav 等
    并等待结果
    #PlayAudioResponse.isSuccess : 是否成功
    #PlayAudioResponse.resultCode : 返回码
    """
    # 播放音效, url表示要播放的音效列表

    url = f'http://101.201.224.75:2020/dealAudio?text={text}&voice={voice}'

    block: PlayAudio = PlayAudio(
        url=url,
        storage_type=AudioStorageType.NET_PUBLIC)
    # response是个PlayAudioResponse
    (resultType, response) = await block.execute()

    print(f'test_play_online_audio result: {response}')
    print('resultCode = {0}, error = {1}'.format(response.resultCode, errors.get_speech_error_str(response.resultCode)))

    # assert resultType == MiniApiResultType.Success, 'test_play_online_audio timetout'
    # assert response is not None and isinstance(response, PlayAudioResponse), 'test_play_online_audio result unavailable'
    # assert response.isSuccess, 'test_play_online_audio failed'

# 加载知识库
def load_knowledge() -> Tuple[List, List]:
    with open(knowledge_txt_path, 'r', encoding='utf-8') as f1, open(knowledge_pkl_path, 'rb') as f2:
        knowledge = [line.strip() for line in f1.readlines()]
        encoded_knowledge = pickle.load(f2)
    return knowledge, encoded_knowledge

# 召回
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
# 加载向量模型与知识库
async def load():
    loop = asyncio.get_event_loop()
    fu1 = loop.run_in_executor(None, load_embedding)
    fu2 = loop.run_in_executor(None, load_knowledge)
    emb = await fu1
    knowledge, encoded_knowledge = await fu2
    return emb, knowledge, encoded_knowledge

async def init():
    done, pending = await asyncio.wait([load()])
    if pending:
        raise Exception('Load task did not complete')
    else:
        result = done.pop().result()
        emb, knowledge, encoded_knowledge = result
        return emb, knowledge, encoded_knowledge

if __name__ == '__main__':
    MiniSdk.set_robot_type(MiniSdk.RobotType.MINI)
    MiniSdk.set_log_level(logging.INFO)
    device: WiFiDevice = asyncio.get_event_loop().run_until_complete(test_get_device_by_name())
    if device:
        asyncio.get_event_loop().run_until_complete(test_connect(device))
        emb, knowledge, encoded_knowledge = asyncio.get_event_loop().run_until_complete(init())
        asyncio.get_event_loop().run_until_complete(test_start_run_program())
        print("准备就绪")
        asyncio.get_event_loop().run_until_complete(test_ObserveHeadRacket())
        # 定义了事件监听对象,必须让event_loop.run_forver()
        asyncio.get_event_loop().run_forever()
        # asyncio.get_event_loop().run_until_complete(shutdown())

