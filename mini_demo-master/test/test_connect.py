import asyncio
import logging

import mini.mini_sdk as MiniSdk
from mini.apis.api_sence import FaceDetect, FaceAnalysis
from mini.apis.api_sound import StartPlayTTS
from mini.dns.dns_browser import WiFiDevice


# 搜索指定序列号(在机器人屁股后面)的机器人, 可以只输入序列号尾部字符即可,长度任意, 建议5个字符以上可以准确匹配, 10秒超时
# 搜索的结果WiFiDevice, 包含机器人名称,ip,port等信息
async def test_get_device_by_name():
    """根据机器人序列号后缀搜索设备

    搜索指定序列号(在机器人屁股后面)的机器人, 可以只输入序列号尾部字符即可,长度任意, 建议5个字符以上可以准确匹配, 10秒超时


    Returns:
        WiFiDevice: 包含机器人名称,ip,port等信息

    """
    result: WiFiDevice = await MiniSdk.get_device_by_name("100037", 10)
    print(f"test_get_device_by_name result:{result}")
    return result


# 搜索指定序列号(在机器人屁股后面)的机器人,
async def test_get_device_list():
    """搜索所有设备

    搜索所有设备，10s后返回结果

    Returns:
        [WiFiDevice]: 所有搜索到的设备，WiFiDevice数组

    """
    results = await MiniSdk.get_device_list(10)
    print(f"test_get_device_list results = {results}")
    return results


# MiniSdk.connect 返回值为bool, 这里忽略返回值
async def test_connect(dev: WiFiDevice) -> bool:
    """连接设备

    连接指定的设备

    Args:
        dev (WiFiDevice): 指定的设备对象 WiFiDevice

    Returns:
        bool: 是否连接成功

    """
    return await MiniSdk.connect(dev)


# 进入编程模式,机器人有个tts播报,这里通过asyncio.sleep 让当前协程等6秒返回,让机器人播完
async def test_start_run_program():
    """进入编程模式demo

    使机器人进入编程模式，等待回复结果，并延时6秒，让机器人播完"进入编程模式"

    Returns:
        None:

    """
    await MiniSdk.enter_program()


# 断开连接并释放资源
async def shutdown():
    """断开连接并释放资源

    断开当前连接的设备，并释放资源

    """
    await MiniSdk.quit_program()
    await MiniSdk.release()

# 测试text合成声音
async def test_play_tts():
    """测试播放tts

    使机器人开始播放一段tts，内容为"你好， 我是悟空， 啦啦啦"，并等待结果

    #ControlTTSResponse.isSuccess : 是否成功

    #ControlTTSResponse.resultCode : 返回码

    """
    # is_serial:串行执行
    # text:要合成的文本
    block: StartPlayTTS = StartPlayTTS(text="你好， 我是悟空， 啦啦啦")
    # 返回元组, response是个ControlTTSResponse
    (resultType, response) = await block.execute()

    print(f'test_play_tts result: {response}')
    # StartPlayTTS block的response包含resultCode和isSuccess
    # 如果resultCode !=0 可以通过errors.get_speech_error_str(response.resultCode)) 查询错误描述信息
    print('resultCode = {0}, error = {1}'.format(response.resultCode, errors.get_speech_error_str(response.resultCode)))


async def test_face_detect():
    """测试人脸个数侦测

    侦测人脸个数，10s超时，并等待回复结果

    #FaceDetectResponse.count : 人脸个数

    #FaceDetectResponse.isSuccess : 是否成功

    #FaceDetectResponse.resultCode : 返回码

    """
    # timeout: 指定侦测时长
    block: FaceDetect = FaceDetect(timeout=5)
    # response: FaceDetectResponse
    (resultType, response) = await block.execute()

    print(f'test_face_detect result: {response}')

# 测试人脸分析(性别)
async def test_face_analysis():
    """测试人脸分析（性别）

    侦测人脸信息(性别、年龄)，超时时间10s，并等待回复结果

    当多人存在摄像头前时，返回占画面比例最大的那个人脸信息

    返回值：示例 {"age": 24, "gender": 99, "height": 238, "width": 238}

    age: 年龄

    gender：[1, 100], 小于50为女性，大于50为男性

    height：人脸在摄像头画面中的高度

    width：人脸在摄像头画面中的宽度

    """
    block: FaceAnalysis = FaceAnalysis(timeout=10)
    # response: FaceAnalyzeResponse
    (resultType, response) = await block.execute()

    print(f'test_face_analysis result: {response}')
    print('code = {0}, error={1}'.format(response.resultCode, errors.get_vision_error_str(response.resultCode)))


# 默认的日志级别是Warning, 设置为INFO
MiniSdk.set_log_level(logging.INFO)
# 设置机器人类型
MiniSdk.set_robot_type(MiniSdk.RobotType.MINI)


async def main():
    device: WiFiDevice = await test_get_device_by_name()
    if device:
        await test_connect(device)
        await test_start_run_program()


if __name__ == '__main__':
    asyncio.run(main())
