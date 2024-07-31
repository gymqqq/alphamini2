import asyncio

from mini.apis import errors
from mini.apis.api_sound import StartPlayTTS, StopPlayTTS, ControlTTSResponse
from mini.apis.base_api import MiniApiResultType
from mini.apis.api_action import PlayAction


async def read_speechwords():
    """测试停止播放tts

    使机器人开始播放一段长文本tts，内容为"你好， 我是悟空， 啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦啦"，不等待结果
    2s后，使机器人停止播放tts

    #ControlTTSResponse.isSuccess : 是否成功

    #ControlTTSResponse.resultCode : 返回码

    """
    # is_serial:串行执行
    # text:要合成的文本

    # block: MoveRobot = MoveRobot(step=2, direction=MoveRobotDirection.LEFTWARD,is_serial=False)
    # await block.execute()
    # await asyncio.sleep(2)
    # block: PlayAction = PlayAction(action_name='action_014',is_serial=False)
    # await block.execute()
    # await asyncio.sleep(3)
    block: PlayAction = PlayAction(action_name='action_014', is_serial=False)
    await block.execute()
    await asyncio.sleep(4)
    block: StartPlayTTS = StartPlayTTS(is_serial=False, text="尊敬的各位领导，下面由我代表数据科学与智能计算科教平台汇报一下当前平台的建设情况。")
    await block.execute()
    await asyncio.sleep(9)

    block: StartPlayTTS = StartPlayTTS(is_serial=False,text="我们平台主要负责智算中心和北航AI平台“小航”的建设工作。")
    await block.execute()
    await asyncio.sleep(7)

    block: StartPlayTTS = StartPlayTTS(is_serial=False,text="首先，汇报一下我们智算中心的设计和建设情况。")
    await block.execute()
    await asyncio.sleep(5)

    block: StartPlayTTS = StartPlayTTS(is_serial=False,text="智算中心的建设主要为全校师生提供科研和教学上的AI算力支撑。")
    await block.execute()
    await asyncio.sleep(7)

    block: StartPlayTTS = StartPlayTTS(is_serial=False,text="我们立足于建设全国产的AI算力中心。")
    await block.execute()
    await asyncio.sleep(4)

    block: StartPlayTTS = StartPlayTTS(is_serial=False,text="在选型过程中，也充分考虑了跟国际上主流GPU和CPU的兼容性，选择了兼容性最好的海光系列CPU和天数系列GPU，在算法迁移过程中最为无缝衔接，基本上在10分钟以内就可以完成程序迁移。")
    await block.execute()
    await asyncio.sleep(20)


    (resultType, response) = await StopPlayTTS().execute()

    print(f'test_stop_play_tts result: {response}')
    # StopPlayTTS block的response包含resultCode和isSuccess
    # 如果resultCode !=0 可以通过errors.get_speech_error_str(response.resultCode)) 查询错误描述信息
    print('resultCode = {0}, error = {1}'.format(response.resultCode, errors.get_speech_error_str(response.resultCode)))

    assert resultType == MiniApiResultType.Success, 'test_stop_play_tts timetout'
    assert response is not None and isinstance(response, ControlTTSResponse), 'test_stop_play_tts result unavailable'
    assert response.isSuccess, 'test_stop_play_tts failed'




