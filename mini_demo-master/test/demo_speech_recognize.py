import asyncio

from mini.apis.api_observe import ObserveSpeechRecognise
from mini.apis.api_sound import StartPlayTTS
from mini.dns.dns_browser import WiFiDevice

from mini.pb2.codemao_speechrecognise_pb2 import SpeechRecogniseResponse
from test_connect import test_connect, shutdown
from test_connect import test_get_device_by_name, test_start_run_program
from mini.apis.api_action import PlayAction

async def __tts():
    block: StartPlayTTS = StartPlayTTS(text="你好， 我是悟空， 啦里啦，啦里啦")
    await block.execute()

# 测试监听语音识别
async def test_speech_recognise():
    # 语音监听对象
    observe: ObserveSpeechRecognise = ObserveSpeechRecognise()
    
    def handler(msg: SpeechRecogniseResponse): 
        print(f'=======handle speech recognise:{msg}')
        print("{0}".format(str(msg.text)))
        if str(msg.text) == "悟空":
            #监听到"悟空", tts打个招呼
            asyncio.create_task(__tts())

        elif str(msg.text) == "结束":
            #监听到结束, 停止监听
            observe.stop()
            #结束event_loop
            asyncio.get_running_loop().run_in_executor(None, asyncio.get_running_loop().stop)

    observe.set_handler(handler)
    #启动
    observe.start()
    await asyncio.sleep(0)


if __name__ == '__main__':
    device: WiFiDevice = asyncio.get_event_loop().run_until_complete(test_get_device_by_name())
    if device:
        asyncio.get_event_loop().run_until_complete(test_connect(device))
        asyncio.get_event_loop().run_until_complete(test_start_run_program())
        asyncio.get_event_loop().run_until_complete(test_speech_recognise())
        asyncio.get_event_loop().run_forever()  # 定义了事件监听对象,必须让event_loop.run_forver
        asyncio.get_event_loop().run_until_complete(shutdown())