import datetime
import logging
import os
import tempfile
import threading
import uuid
import json
from . import sqllite_util
from pr_properties import pr_properties
import wx
from pathlib import Path
from util.exception_util import ThreadException

data_url = r'./data/data.json'
config_url = r'./data/config.properties'
log_dir_url = r'./log/'
step_url = r'./step/step.json'
dictionary_url = r'./data/dictionary.json'
temporary_url = r'./data/temporary.json'
info_url = r'./data/info.json'
view_url = r'./data/view.json'
event = threading.Event()
config_lock = threading.Lock()
data_lock = threading.Lock()
dictionary_lock = threading.Lock()
temporary_lock = threading.Lock()
info_lock = threading.Lock()
view_lock = threading.Lock()
step_lock = threading.Lock()
index_lock = threading.Lock()
cue_word_lock = threading.Lock()
window_dict = dict()

def generate_random_string(length=36):
    random_string = str(uuid.uuid4())[:length]
    return random_string

def get_data(key=None, default=None):
    with open(data_url, 'r', encoding='utf-8') as f:
        if key is None:
            return json.load(f).get(get_config("software"))
        else:
            return json.load(f).get(get_config("software")).get(key, default)

def set_data(key, value):
    with data_lock:
        with open(data_url, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(data_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(data_url)) as temp_f:
                if data.get(get_config("software")) is None:
                    data.update({get_config("software"):{}})
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

def get_dictionary(key, default=None):
    with open(dictionary_url, 'r', encoding='utf-8') as f:
        return json.load(f).get(get_config("software")).get(key, default)

def set_dictionary(key, value):
    with dictionary_lock:
        with open(dictionary_url, 'r', encoding='utf-8') as f:
            dictionary_data = json.load(f)
        with open(dictionary_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(dictionary_url)) as temp_f:
                if dictionary_data.get(get_config("software")) is None:
                    dictionary_data.update({get_config("software"):{}})
                dictionary_data.get(get_config("software")).update({key : value})
                json.dump(dictionary_data, temp_f, indent=4, ensure_ascii=False)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, dictionary_url)

def get_temporary(step, key):
    with open(temporary_url, 'r', encoding='utf-8') as f:
        return json.load(f).get(get_config("software")).get(step,{}).get(key, "")

def clean_temporary():
    with temporary_lock:
        with open(temporary_url, 'r', encoding='utf-8') as f:
            temporary_data = json.load(f)
        with open(temporary_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(temporary_url)) as temp_f:
                temporary_data.update({get_config("software"):{}})
                json.dump(temporary_data, temp_f, indent=4, ensure_ascii=False)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, temporary_url)

def set_temporary(step, key, value):
    with temporary_lock:
        with open(temporary_url, 'r', encoding='utf-8') as f:
            temporary_data = json.load(f)
        with open(temporary_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(temporary_url)) as temp_f:
                if temporary_data.get(get_config("software")) is None:
                    temporary_data.update({get_config("software"): {}})
                if temporary_data.get(get_config("software")).get(step) is None:
                    temporary_data.get(get_config("software")).update({step: {}})
                temporary_data.get(get_config("software")).get(step).update({str(key): value})
                json.dump(temporary_data, temp_f, indent=4, ensure_ascii=False)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, temporary_url)

def get_info(step, key=None, default=None):
    with open(info_url, 'r', encoding='utf-8') as f:
        if key is None:
            return json.load(f).get(get_config("software")).get(step, {})
        else:
            return json.load(f).get(get_config("software")).get(step, {}).get(key, default)

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
                    data = get_data()
                    for text_item in text_items[text_item_key].split(sep="."):
                        data = data.get(text_item)
                    if isinstance(data, int):
                        data = get_temporary(step=text_items[text_item_key].split(sep=".")[0], key=str(data))
                    if data:
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

def set_step(step_num = 0, step = -1):
    with step_lock:
        value = sqllite_util.get("step")
        if step != -1:
            get_step_data(get_config("software"), step + step_num)
            sqllite_util.update("step", step + step_num)
        else :
            get_step_data(get_config("software"), value + step_num)
            sqllite_util.update("step", value + step_num)

def get_step(default=1):
    value = sqllite_util.get("step")
    if not value:
        value = default
    return value

def get_step_data(key, step, default=""):
    if  step <= 0 :
        raise IndexError("步数不能小于0")
    step-=1
    with open(step_url, 'r', encoding='utf-8') as f:
        step_list = list(json.load(f).get(key, []))
        if len(step_list) == 0:
            return default
        return step_list[step]

def get_step_data_all(key):
    with open(step_url, 'r', encoding='utf-8') as f:
        step_list = list(json.load(f).get(key, []))
        return step_list

def get_view(default=None):
    if default is None:
        default = []
    with open(view_url, 'r', encoding='utf-8') as f:
        return json.load(f).get(get_config("software"), default)

def set_view(key, index=None, title=None, type=None, content=None):
    with view_lock:
        with open(view_url, 'r', encoding='utf-8') as f:
            view_data = json.load(f)
        with open(view_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(view_url)) as temp_f:
                match key:
                    case "add":
                        if len(view_data.get(get_config("software")))==0 or view_data.get(get_config("software"))[-1].get("title") != title:
                            view_data.get(get_config("software")).append({"index":index, "is_active":True, "title":title, "type":type, "content":content})
                    case "delete":
                        for view_item in view_data.get(get_config("software")):
                            if view_item.get("index") == index:
                                view_item.update({"is_active":False})
                    case "clear":
                        view_data.get(get_config("software")).clear()
                json.dump(view_data, temp_f, indent=4, ensure_ascii=False)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, view_url)

def set_index(index_num = 0, index = -1):
    with index_lock:
        value = sqllite_util.get("index")
        if index != -1:
            sqllite_util.update("index", index + index_num)
        else :
            sqllite_util.update("index", value + index_num)

def get_index(default=0):
    value = sqllite_util.get("index")
    if not value:
        value = default
    return value

def set_event_status(event_status):
    sqllite_util.update("event_status", event_status)

def get_event_status(default=0):
    value = sqllite_util.get("event_status")
    if not value:
        value = default
    return value

def set_thread_status(thread_status):
    sqllite_util.update("thread_status", thread_status)

def get_thread_status(default=0):
    value = sqllite_util.get("thread_status")
    if not value:
        value = default
    return value

def set_flag(flag):
    sqllite_util.update("flag", flag)

def get_flag(default=1):
    value = sqllite_util.get("flag")
    if not value:
        value = default
    return value

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

def pause(main_ui):
    if get_event_status() != 1:
        wx.CallAfter(main_ui.init)
        global event
        event.clear()
        event.wait()
    if get_thread_status() != 1:
        wx.CallAfter(main_ui.init)
        raise ThreadException("线程关闭...")

def get_cue_word():
    cue_word_url = "ai/"+get_config("software")+"/text/index.txt"
    with open(cue_word_url, 'r', encoding='utf-8') as f:
        return f.read()

def set_cue_word(value):
    with cue_word_lock:
        cue_word_url = "ai/" + get_config("software") + "/text/index.txt"
        with open(cue_word_url, 'w', encoding='utf-8') as f:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8',
                                             dir=os.path.dirname(cue_word_url)) as temp_f:
                temp_f.write(value)
                temp_file_path = temp_f.name
        os.replace(temp_file_path, cue_word_url)

def get_cue_img_url():
    img_url = "ai/" + get_config("software") + "/img/index.png"
    return img_url

def ai_response_item_is_null(result_dict, key):
    return result_dict.get(key) is not None and result_dict.get(key) != "None" and result_dict[key] != "无" and result_dict[key] != "N/A"


def seconds_to_verbose_time(total_seconds):
    """
    将秒数转换为更自然的语言描述，例如 "1 天 2 小时 30 分钟 5 秒"。
    """
    if not isinstance(total_seconds, (int, float)):
        raise TypeError("输入必须是数字。")
    if total_seconds < 0:
        raise ValueError("输入不能是负数。")
    if total_seconds == 0:
        return "0 秒"

    total_seconds = int(total_seconds)

    parts = []

    seconds_in_minute = 60
    seconds_in_hour = 60 * seconds_in_minute
    seconds_in_day = 24 * seconds_in_hour

    # 天
    days = total_seconds // seconds_in_day
    if days > 0:
        parts.append(f"{days} 天")
    total_seconds %= seconds_in_day

    # 小时
    hours = total_seconds // seconds_in_hour
    if hours > 0:
        parts.append(f"{hours} 小时")
    total_seconds %= seconds_in_hour

    # 分钟
    minutes = total_seconds // seconds_in_minute
    if minutes > 0:
        parts.append(f"{minutes} 分钟")
    total_seconds %= seconds_in_minute

    # 秒
    seconds = total_seconds
    if seconds > 0 or not parts:  # 如果没有其他单位，即使秒数为0也要显示，但这里我们已经处理了total_seconds=0的情况
        parts.append(f"{seconds} 秒")

    return " ".join(parts)

