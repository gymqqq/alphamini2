import edge_tts
import asyncio
import playsound
import shutil
import os
# text = "你好啊，我是智能助手小伊，有什么能帮助你的吗"
voice = "zh-CN-XiaoyiNeural"
script_dir = os.path.dirname(os.path.abspath(__file__))
output_speech_file = os.path.normpath(os.path.join(script_dir, "test2.mp3"))
# output_speech_file = r"./test2.mp3"

async def _tts(text) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_speech_file)
    playsound.playsound(output_speech_file) #播放生成的音频文件
    os.remove(output_speech_file) #删除播放完的音频文件

# asyncio.run(_tts("你好啊，我是智能助手小伊，有什么能帮助你的吗"))