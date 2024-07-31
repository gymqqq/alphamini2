import mini.pkg_tool as Tool
from mini import mini_sdk as MiniSdk
# 设置机器人类型
MiniSdk.set_robot_type(MiniSdk.RobotType.MINI)
# 安装当前目录下simple_socket-0.0.2-py3-none-any.whl文件
Tool.install_py_pkg(package_path="E:/Codespace/Android_new/mini_demo/test/tts_edge_demo/dist/tts_demo-0.0.2-py3-none-any.whl", robot_id="3254")