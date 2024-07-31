from tencentcloud.common import credential  # 这里需要安装腾讯翻译sdk
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tmt.v20180321 import tmt_client, models
import json
def translate_text(text):
    try:
        httpProfile.endpoint = "tmt.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = tmt_client.TmtClient(cred, "ap-beijing", clientProfile)

        req = models.TextTranslateRequest()
        req.SourceText = text  # 要翻译的语句
        req.Source = 'zh'  # 源语言类型
        req.Target = 'fr'  # 目标语言类型
        # req.Target = 'en'  # 目标语言类型
        req.ProjectId = 0

        resp = client.TextTranslate(req)
        data = json.loads(resp.to_json_string())
        # return data
        # print(data['TargetText'])
        return data['TargetText']



    except TencentCloudSDKException as err:
        print(err)
# print(translate_text("你好"))
