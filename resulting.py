import VkAgent
import OkAgent
import Ya
import requests
import os
import json
import Token
import Ya
import Agent
import hashlib

if __name__ == '__main__':
    # FILE_DIR1 = "Michel"
    # michel = VkAgent.VkAgent(Token.TOKEN_VK, "552934290")
    # michel.files_downloader(FILE_DIR1)
    # PATH_DIR1 = os.path.join(os.getcwd(), FILE_DIR1)
    # michel_load = Ya.YaUploader(Token.TOKEN_YA)
    # michel_load.upload(PATH_DIR1)

    FILE_DIR2 = "Alex"
    ok1 = OkAgent.OkAgent("332021380847")
    ok1.files_downloader(FILE_DIR2)
    PATH_DIR2 = os.path.join(os.getcwd(), FILE_DIR2)
    ok1_load = Ya.YaUploader(Token.TOKEN_YA)
    ok1_load.upload(PATH_DIR2)
