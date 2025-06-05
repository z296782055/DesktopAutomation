import datetime
import logging
import os
import tempfile
import threading
import uuid
import json

import requests
from pr_properties import pr_properties
import wx
from pathlib import Path

from util import keyring_util
from util.exception_util import ThreadException

data_url = r'./data/data.json'
config_url = r'./data/config.properties'
log_dir_url = r'./log/'
step_url = r'./step/step.json'
dictionary_url = r'./data/dictionary.json'
temporary_url = r'./data/temporary.json'
info_url = r'./data/info.json'
event = threading.Event()
config_lock = threading.Lock()
data_lock = threading.Lock()
dictionary_lock = threading.Lock()
temporary_lock = threading.Lock()
info_lock = threading.Lock()
window_dict = dict()

def generate_random_string(length=36):
    random_string = str(uuid.uuid4())[:length]
    return random_string

def get_data(key=None, default=None):
    with open(data_url, 'r', encoding='utf-8') as f:
        if key is None:
            return json.load(f).get(get_config("software"))
        else:
            return json.load(f).get(get_config("software")).get(key, "")

def set_data(key, value):
    with data_lock:
        with open(data_url, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(data_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(data_url)) as temp_f:
                data.get(get_config("software")).update({key: value})
                json.dump(data, temp_f, indent=4, ensure_ascii=False)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, data_url)

def get_config(key, default=None):
    config = pr_properties.read(config_url)
    if len(config.properties) == 0:
        os.replace(config_url+".pr_bak", config_url)
        config = pr_properties.read(config_url)
    return config.get(key, default)

def set_config(key, value):
    with config_lock:
        config = pr_properties.read(config_url)
        config[key] = value
        config.write()

def get_dictionary(key):
    with open(dictionary_url, 'r', encoding='utf-8') as f:
        return json.load(f).get(get_config("software")).get(key, "")

def set_dictionary(key, value):
    with dictionary_lock:
        with open(dictionary_url, 'r', encoding='utf-8') as f:
            dictionary_data = json.load(f)
        with open(dictionary_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(dictionary_url)) as temp_f:
                dictionary_data.get(get_config("software")).update({key : value})
                json.dump(dictionary_data, temp_f, indent=4, ensure_ascii=False)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, dictionary_url)

def get_temporary(step, key):
    with open(temporary_url, 'r', encoding='utf-8') as f:
        return json.load(f).get(get_config("software")).get(step,{}).get(key, "")

def set_temporary(step, key, value):
    with temporary_lock:
        with open(temporary_url, 'r', encoding='utf-8') as f:
            temporary_data = json.load(f)
        with open(temporary_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(temporary_url)) as temp_f:
                temporary_data.get(get_config("software")).get(step).update({str(key): value})
                json.dump(temporary_data, temp_f, indent=4, ensure_ascii=False)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, temporary_url)

def get_info(key=None, default=None):
    with open(info_url, 'r', encoding='utf-8') as f:
        if key is None:
            return json.load(f).get(get_config("software"))
        else:
            return json.load(f).get(get_config("software")).get(key, "")

def refer_dictionary(step, key):
    dictionary = get_dictionary(str(key))
    value = ""
    if isinstance(dictionary, dict):
        for text_items in dictionary["text"]:
            text_item_key = next(iter(text_items))
            match text_item_key:
                case "dictionary":
                    value += get_dictionary(text_items[text_item_key])
                case "text":
                    value += text_items[text_item_key]
                case "data":
                    data = get_data(key=get_config("software"))
                    for text_item in text_items[text_item_key].split(sep="."):
                        data = data[text_item]
                    if isinstance(data, int):
                        data = get_temporary(step=text_items[text_item_key].split(sep=".")[0], key=str(data))
                    value += data
        match dictionary["type"]:
            case "nowtime":
                now = datetime.datetime.now()
                formatted_time = now.strftime(value)
                value = formatted_time
            case "param":
                pass
            case _:
                pass
    else:
        value = dictionary
    if isinstance(key, int):
        set_temporary(step=step, key=key, value=value)
    return value

def set_step(step_num = 0, step = 0):
    with config_lock:
        config = pr_properties.read(config_url)
        if len(config.properties) == 0:
            os.replace(config_url + ".pr_bak", config_url)
            config = pr_properties.read(config_url)
        if step != 0:
            get_step(config["software"], step + step_num)
            config["step"] = step + step_num
        else :
            get_step(config["software"], int(config["step"]) + step_num)
            config["step"] = int(config["step"]) + step_num
        config.write()

def get_step(key, step, default=""):
    step = int(step)
    if  step <= 0 :
        raise IndexError("步数不能小于0")
    step-=1
    with open(step_url, 'r', encoding='utf-8') as f:
        step_list = list(json.load(f).get(key, []))
        if len(step_list) == 0:
            return default
        return step_list[int(step)]

def get_step_all(key):
    with open(step_url, 'r', encoding='utf-8') as f:
        step_list = list(json.load(f).get(key, []))
        return step_list

def set_index(index_num = 0, index = 0):
    with config_lock:
        config = pr_properties.read(config_url)
        if len(config.properties) == 0:
            os.replace(config_url + ".pr_bak", config_url)
            config = pr_properties.read(config_url)
        if index != 0:
            config["index"] = index + index_num
        else :
            config["index"] = int(config["index"]) + index_num
        config.write()

# def set_step_name(key, value):
#     with data_lock:
#         with open(step_url, 'w', encoding='utf-8') as f:
#             json.load(f).set(key, value)

def traverse_elements(self, element_type, element_list=None):
    if element_list is None:
        element_list = []
    children = self.GetChildren()
    for child in children:
        # 检查子窗口是否为TextCtrl类型
        if isinstance(child, element_type):
            element_list.append(child)
        elif isinstance(child, wx.Panel):
            traverse_elements(child, element_type, element_list)
    return element_list

def get_log(self):
    try:
        log_file = Path(log_dir_url + get_config("default_log_file_name") + "." + datetime.datetime.now().strftime("%Y-%m-%d")+".log")
        if os.path.exists(log_file):
            os.startfile(log_file)
        else:
            os.startfile(Path(log_dir_url + get_config("default_log_file_name")))
    except FileNotFoundError as e:
        logging.exception(e)
        dlg = wx.MessageDialog(self, "日志不存在！", "提示", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()  # 显示对话框
        dlg.Destroy()  # 销毁对话框，释放资源

def thread_is_alive(name):
    threads = threading.enumerate()
    target_thread = [t for t in threads if t.name == name]
    if len(target_thread)>1:
        print("线程数量："+str(len(target_thread)))
    print("线程数量：" + str(len(target_thread)))
    if target_thread:
        return target_thread[0]
    else:
        return False

def pause():
    if get_config("event_status", 1) != "1":
        global event
        event.clear()
        event.wait()
    if get_config("thread_status", 1) != "1":
        raise ThreadException("线程关闭...")

def login_verify():
    try:
        if get_config("username") == "":
            return False
        token = keyring_util.load_token_from_keyring(get_config("username"))
        if not token:
            return False
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.post(url=get_config("server_url")+"/user/verify", headers=headers)

        print("Status Code:", response.status_code)
        print("Response JSON:", json.dumps(response.json(), indent=2, ensure_ascii=False))

        # 检查响应状态码
        response.raise_for_status()

        print("Status Code:", response.status_code)
        print("Response JSON:", json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code != 200:
            return False
    except Exception:
        return False
    return True
