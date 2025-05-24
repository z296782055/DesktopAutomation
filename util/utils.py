import datetime
import logging
import os
import threading
import uuid
import json

from pr_properties import pr_properties
import wx
from pathlib import Path
from util.exception_util import ThreadException

data_url = r'./data/data.json'
config_url = r'./data/config.properties'
log_dir_url = r'./log/'
step_url = r'./step/step.json'
dictionary_url = r'./data/dictionary.json'
event = threading.Event()
config_lock = threading.Lock()
data_lock = threading.Lock()
dictionary_lock = threading.Lock()

window_dict = dict()

def generate_random_string(length=36):
    random_string = str(uuid.uuid4())[:length]
    return random_string

def get_data(key, default=None):
    with open(data_url, 'r', encoding='utf-8') as f:
        return json.load(f).get(key, "")

def set_data(key, value):
    with data_lock:
        with open(data_url, 'w', encoding='utf-8') as f:
            json.load(f).set(key, value)

def get_config(key, default=None):
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
            dictionary_data.get(get_config("software")).update({key : value})
            json.dump(dictionary_data, f, indent=4)

def refer_dictionary(key):
    dictionary = get_dictionary(str(key))
    match key:
        case 10001:
            dictionary = get_dictionary(dictionary)
            now = datetime.datetime.now()
            formatted_time = now.strftime(dictionary)
            return formatted_time
        case _:
            return dictionary

def set_step(step_num = 0, step = 0):
    with config_lock:
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