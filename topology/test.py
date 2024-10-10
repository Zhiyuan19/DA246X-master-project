import os

# 获取当前 Python 文件的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件所在目录
current_directory = os.path.dirname(current_file_path)

# 输出当前目录
print(f"当前目录: {current_directory}")
