import copy
import json
import logging
import os
import time
from pathlib import Path

import _ctypes
import pyperclip
import pywinauto
from PIL import Image
from pdf2image import convert_from_path
from pywinauto import Application,base_wrapper,uia_defines
from pywinauto.controls.uiawrapper import UIAWrapper
import wx

from util import utils
from util.exception_util import ViewException
from util.keyring_util import api_client
from util.logger_util import logger
from pywinauto.timings import TimeoutError

default_sleep_time = float(utils.get_config('default_sleep_time', 1))
default_backend = "uia"

def start(command_queue, result_queue, event):
    while utils.get_flag():
        step_list = utils.get_step_data_all(utils.get_config('software'))
        now_step_list = step_list[int(utils.get_step())-1:]
        for step in now_step_list:
            utils.set_step(1, step_list.index(step))
            result_queue.put({"method":"init"})
            utils.window_dict.clear()
            for key, value in step.items():
                for automation in list(value):
                    result_queue.put({"method": "SetTitle", "args": {"title" : utils.get_config("software")+"-"+get_detail(key, automation)}})
                    do_automation(command_queue=command_queue, result_queue=result_queue, event=event, step=key, automation=automation)
        utils.set_step(1, 0)
    utils.set_event_status(0)
    utils.set_process_status(0)

def get_detail(step, automation):
    auto_type = automation.get("auto_type")
    detail = ""
    match auto_type:
        case "connect_window":
            detail += "获取窗口:"
            detail += "\""+automation.get("title")+"\""
        case "connect_child_window":
            detail += "从窗口:\"" + automation.get("window") + "\""
            detail += "获取子窗口"
            detail += automation.get("title")
        case "control_click":
            detail += "点击控件:"
            if (len(automation.get("kwargs"))) == 0:
                detail += ("\"" + automation.get("window") + "\"")
            else:
                kwarg = next(iter(automation.get("kwargs")[-1].values()))
                key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
                info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
                team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
                detail += ("\"" + (info if info is not None else team) + "\"")
        case "edit_write":
            detail += "填写文本框:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
            info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
            team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
            detail += ("\"" + (info if info is not None else team) + "\"")
        case "list_select":
            detail += "列表选择:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
            info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
            team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
            detail += ("\"" + (info if info is not None else team) + "\"")
        case "check":
            detail += "选择复选框:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
            info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
            team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
            detail += ("\"" + (info if info is not None else team) + "\"")
        case "table_fill":
            detail += "填写表格:"
            kwarg = next(iter(automation.get("table_kwargs")[-1].values()))
            key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
            info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
            team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
            detail += ("\"" + (info if info is not None else team) + "\"")
        case "tree_click":
            detail += "点击树状图节点:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
            info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
            team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
            detail += ("\"" + (info if info is not None else team) + "\"")
        case "table_click":
            detail += "点击表格控件:"
            kwarg = next(iter(automation.get("table_kwargs")[-1].values()))
            key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
            info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
            team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
            detail += ("\"" + (info if info is not None else team) + "\"")
        case "wait":
            detail += "等待:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
            info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
            team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
            detail += ("\"" + (info if info is not None else team) + "\"")
        case "window_close":
            detail += "关闭窗口:"
            detail += "\"" + automation.get("title") + "\""
            if (len(automation.get("kwargs"))) != 0:
                kwarg = next(iter(automation.get("kwargs")[-1].values()))
                key = (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id"))
                info = utils.get_info(step=step, key=key, default={"info": key}).get("info")
                team = utils.get_info(step=step, key=key, default={"team": key}).get("team")
                detail += ("\"" + (info if info is not None else team) + "\"")
        case "ai_post":
            detail += "请求AI"
    if automation.get("before_sleep_time") and automation.get("before_sleep_time") > 0:
        detail += "("+utils.seconds_to_verbose_time(automation.get("before_sleep_time"))+"后)"
    return detail

def do_automation(command_queue, result_queue, event, step, automation):
    auto_type = automation.get("auto_type")
    if auto_type == "connect_window":
        connect_window(command_queue=command_queue, result_queue=result_queue, event=event, title=automation.get("title"), sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "connect_child_window":
        connect_child_window(command_queue=command_queue, result_queue=result_queue, event=event, window = automation.get("window"), kwargs = automation.get("kwargs"), title = automation.get("title"), step = step, sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "control_click":
        control_click(command_queue=command_queue, result_queue=result_queue, event=event, window = automation.get("window"), kwargs = automation.get("kwargs"), click_type = automation.get("click_type"), index=automation.get("index"), ready=automation.get("ready"), ignore=automation.get("ignore"), step = step, sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "list_select":
        list_select(command_queue=command_queue, result_queue=result_queue, event=event, window = automation.get("window"), kwargs = automation.get("kwargs") , click_type = automation.get("click_type"), ready=automation.get("ready"), step = step, select_window_title = automation.get("select_window_title"), select_window_kwargs = automation.get("select_window_kwargs"), sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "edit_write":
        edit_write(command_queue=command_queue, result_queue=result_queue, event=event, window=automation.get("window"), kwargs = automation.get("kwargs"), edit_type=automation.get("edit_type"), ready=automation.get("ready"), step=step, sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "table_fill":
        table_fill(command_queue=command_queue, result_queue=result_queue, event=event, window=automation.get("window"), table_kwargs = automation.get("table_kwargs"), table_head_kwargs = automation.get("table_head_kwargs"), table_body_kwargs = automation.get("table_body_kwargs"), title = automation.get("title"), step=step, add = automation.get("add"), clear = automation.get("clear"), table_column = automation.get("table_column"), sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "check":
        check(command_queue=command_queue, result_queue=result_queue, event=event, window=automation.get("window"), kwargs = automation.get("kwargs"), ready=automation.get("ready"), step=step, sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "tree_click":
        tree_click(command_queue=command_queue, result_queue=result_queue, event=event, window=automation.get("window"), kwargs=automation.get("kwargs"),
                      click_type=automation.get("click_type"),title=automation.get("title"), up=automation.get("up"), down=automation.get("down"), step=step, is_select=automation.get("is_select"), sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time,
                      before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "table_click":
        table_click(command_queue=command_queue, result_queue=result_queue, event=event, window=automation.get("window"), table_kwargs=automation.get("table_kwargs"), kwargs=automation.get("kwargs"), replace=automation.get("replace"), step=step, title=automation.get("title"), click_type=automation.get("click_type"),
                        sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "wait":
        wait(command_queue=command_queue, result_queue=result_queue, event=event, window=automation.get("window"), kwargs=automation.get("kwargs"), step=step, ready=automation.get("ready"), index=automation.get("index"), condition=automation.get("condition"), sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "window_close":
        window_close(command_queue=command_queue, result_queue=result_queue, event=event, title=automation.get("title"), kwargs=automation.get("kwargs"), step=step, index=automation.get("index"), before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0)
    elif auto_type == "ai_post":
        ai_post(command_queue=command_queue, result_queue=result_queue, event=event, step=step, sleep_time=automation.get("sleep_time") if automation.get("sleep_time") else default_sleep_time, before_sleep_time=automation.get("before_sleep_time") if automation.get("before_sleep_time") else 0 if automation.get("before_sleep_time") else 0)

def connect_window(command_queue, result_queue, event, title, backend = default_backend, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        try:
            app = Application(backend).connect(title=title)
            window = app.window(title=title)
            window.wait('ready',timeout=1)
            utils.window_dict[title] = window
        except (pywinauto.findwindows.ElementNotFoundError,pywinauto.timings.TimeoutError):
            logger.log("找不到窗口:\ntitle:" + title)
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个窗口:\ntitle:" + title)
            time.sleep(sleep_time)
            continue
        loop = False

def connect_child_window(command_queue, result_queue, event, window, kwargs, title, step, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        target_child_window = utils.window_dict.get(window)
        try:
            for kw in kwargs:
                for key,value in kw.items():
                    target_child_window = getattr(target_child_window, key)(**value)
                    if isinstance(target_child_window, list) :
                        target_child_window = target_child_window[0]
            utils.window_dict[title] = target_child_window
        except pywinauto.findwindows.ElementNotFoundError:
            logger.log("找不到子窗口:\nwindow:" + window + "\ntitle:" + title+"")
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个子窗口:\nwindow:" + window + "\ntitle:" + title+"")
            time.sleep(sleep_time)
            continue
        loop = False

def control_click(command_queue, result_queue, event, window, kwargs, step, click_type=None, index=None, ready=None, ignore=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        if click_type is None:
            click_type = "click"
        if index is None:
            index = 0
        target_control = utils.window_dict.get(window)
        try:
            for kw in kwargs:
                for key,value in kw.items():
                    if value.get("control_type") == "Hyperlink":
                        value["title"] = utils.refer_dictionary(step=step, key=window)
                    target_control = getattr(target_control, key)(**value)
                    if isinstance(target_control, list) :
                        if not isinstance(index, int):
                            index = int(index)
                        target_control = target_control[index]
            if not isinstance (target_control, UIAWrapper) :
                if ready is None:
                    target_control = target_control.wrapper_object()
                else:
                    target_control = target_control.wait(ready, timeout=60)
            try:
                getattr(target_control, click_type)()
            except AttributeError:
                getattr(target_control, click_type+"_input")()
        except (pywinauto.findwindows.ElementNotFoundError,IndexError,_ctypes.COMError,base_wrapper.ElementNotEnabled,TimeoutError) as e:
            logger.log("找不到控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            if ignore:
                ignore -= 1
            if ignore == 0:
                loop = False
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        loop = False

def list_select(command_queue, result_queue, event, window, kwargs, step, click_type=None, select_window_title = None, select_window_kwargs=None, ready=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        try:
            target_list = utils.window_dict.get(window)
            for kw in kwargs:
                for key, value in kw.items():
                    target_list = getattr(target_list, key)(**value)
                    if isinstance(target_list, list):
                        target_list = target_list[0]
            if not isinstance(target_list, UIAWrapper):
                if ready is None:
                    target_list = target_list.wrapper_object()
                else:
                    target_list = target_list.wait(ready, timeout=60)
            target_select_window = target_list
            if select_window_kwargs is None:
                select_window_kwargs = []
            if len(select_window_kwargs) != 0:
                connect_child_window(command_queue=command_queue, result_queue=result_queue, event=event, window = window, kwargs=select_window_kwargs, title=select_window_title, step=step, sleep_time=sleep_time)
                target_select_window = utils.window_dict.get(select_window_title)
            item = utils.get_data(step).get(target_list.element_info.automation_id if target_list.element_info.automation_id else target_list.element_info.name)
            if item is None:
                loop = False
                continue
            try:
                if click_type == "double_click":
                    target_list.click_input()
                    time.sleep(0.5)
                if click_type != "no_click":
                    target_list.click_input()
                if not isinstance(target_select_window, UIAWrapper):
                    if ready is None:
                        target_select_window = target_select_window.wrapper_object()
                    else:
                        target_select_window.wait(ready, timeout=60)
                if target_select_window.element_info.control_type == "Edit":
                    target_select_window.set_text(item)
                else :
                    target_select_window.select(item)
            except (TypeError,uia_defines.NoPatternInterfaceError,IndexError):
                target_list_item = target_select_window.descendants(title=item)
                if len(target_list_item) == 0:
                    target_list_item = utils.window_dict.get(window).descendants(title=item)
                if len(target_list_item) != 0:
                    target_list_item[0].click_input()
        except (pywinauto.findwindows.ElementNotFoundError,IndexError,_ctypes.COMError,base_wrapper.ElementNotEnabled,TimeoutError) as e:
            logger.log("找不到列表:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个列表:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        loop = False
def edit_write(command_queue, result_queue, event, window, kwargs, step, edit_type=None, ready=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        target_edit = utils.window_dict.get(window)
        try:
            for kw in kwargs:
                for key, value in kw.items():
                    target_edit = getattr(target_edit, key)(**value)
                    if isinstance(target_edit, list) :
                        target_edit = target_edit[0]
            if not isinstance(target_edit, UIAWrapper):
                if ready is None:
                    target_edit = target_edit.wrapper_object()
                else:
                    target_edit = target_edit.wait(ready, timeout=60)
            text = utils.get_data(step).get(target_edit.element_info.automation_id if target_edit.element_info.automation_id else target_edit.element_info.name)
            if not text:
                loop = False
                continue
            if isinstance(text, int):
                text = utils.refer_dictionary(step=step, key=text)
            target_edit.type_keys("^a")
            if edit_type == "copy":
                pyperclip.copy(text)
                target_edit.type_keys("^v")
            else:
                try:
                    target_edit.set_text(text)
                except AttributeError:
                    pyperclip.copy(text)
                    target_edit.type_keys("^v")
        except (pywinauto.findwindows.ElementNotFoundError,IndexError,_ctypes.COMError,base_wrapper.ElementNotEnabled,TimeoutError):
            logger.log("找不到控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        loop = False

def check(command_queue, result_queue, event, window, kwargs, step, ready=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        target_check_box = utils.window_dict.get(window)
        try:
            for kw in kwargs:
                for key, value in kw.items():
                    target_check_box = getattr(target_check_box, key)(**value)
                    if isinstance(target_check_box, list) :
                        target_check_box = target_check_box[0]
            if not isinstance(target_check_box, UIAWrapper):
                if ready is None:
                    target_check_box = target_check_box.wrapper_object()
                else:
                    target_check_box = target_check_box.wait(ready, timeout=60)
            check_status = utils.get_data(step).get(target_check_box.element_info.automation_id if target_check_box.element_info.automation_id else target_check_box.element_info.name)
            try:
                if check_status == "True":
                    target_check_box.check()
                else:
                    target_check_box.uncheck()
            except AttributeError:
                if check_status == "True":
                    target_check_box.click_input()
        except (pywinauto.findwindows.ElementNotFoundError,IndexError,_ctypes.COMError,base_wrapper.ElementNotEnabled,TimeoutError):
            logger.log("找不到控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        loop = False

def table_fill(command_queue, result_queue, event, window, step, table_kwargs, table_head_kwargs, table_body_kwargs, title, add, clear, table_column, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        connect_child_window(command_queue=command_queue, result_queue=result_queue, event=event, window=window, kwargs=table_kwargs, title=title, step=step, sleep_time=default_sleep_time)
        try:
            list_len = int(utils.get_data(step).get(title))
            for clear_item in clear:
                do_automation(command_queue, result_queue, event, step, clear_item, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
            for i in range(list_len):
                for add_item in add:
                    do_automation(command_queue, result_queue, event, step, add_item, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
            for i in range(list_len):
                for column_item in table_column.get("column"):
                    column_item = copy.copy(column_item)
                    column_item["window"] = title
                    column_item["kwargs"] = json.loads(json.dumps(column_item["kwargs"]) %i)
                    do_automation(command_queue, result_queue, event, step, column_item, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
        except pywinauto.findwindows.ElementNotFoundError as e:
            logger.log("找不到表格:\nwindow:" + window + "\ntable_kwargs:" + str(table_kwargs))
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个表格:\nwindow:" + window + "\ntable_kwargs:" + str(table_kwargs))
            time.sleep(sleep_time)
            continue
        loop = False

def tree_click(command_queue, result_queue, event, window, kwargs, step, title, up, down, click_type=None, is_select=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        if click_type is None:
            click_type = "click"
        connect_child_window(command_queue=command_queue, result_queue=result_queue, event=event, window=window, kwargs=kwargs, title=title, step=step, sleep_time=default_sleep_time)
        target_tree = utils.window_dict.get(title)
        try:
            if not isinstance (target_tree, UIAWrapper) :
                target_tree = target_tree.wrapper_object()
            if is_select == "True":
                target_nodes = target_tree.descendants(**{"control_type": "TreeItem"})
                flag = True
                for target_node in target_nodes:
                    if target_node.is_selected():
                        text = utils.get_data(step).get(
                            target_tree.element_info.automation_id if target_tree.element_info.automation_id else target_tree.element_info.name)
                        if isinstance(text, int):
                            utils.set_temporary(step=step, key=text, value=target_node.legacy_properties()["Value"])
                        flag = False
                        try:
                            getattr(target_node, click_type)()
                        except AttributeError:
                            getattr(target_node, click_type + "_input")()
            else:
                text = utils.get_data(step).get(
                    target_tree.element_info.automation_id if target_tree.element_info.automation_id else target_tree.element_info.name)
                if isinstance(text, int):
                    text = utils.refer_dictionary(step=step, key=text)
                target_nodes = target_tree.descendants(**{"control_type": "TreeItem"})
                flag = True
                for target_node in target_nodes:
                    if target_node.legacy_properties()["Value"] == text:
                        flag = False
                        target_node.select()
                        try:
                            getattr(target_node, click_type)()
                        except AttributeError:
                            getattr(target_node, click_type + "_input")()
            if flag:
                for down_item in down:
                    do_automation(command_queue, result_queue, event, step, down_item, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
                logger.log("找不到树状图:\nwindow:" + window + "\nkwargs:" + str(kwargs))
                time.sleep(sleep_time)
                continue
        except (pywinauto.findwindows.ElementNotFoundError,IndexError,_ctypes.COMError,base_wrapper.ElementNotEnabled) as e:
            logger.log("找不到树状图:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找到了多个树状图:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        loop = False
def table_click(command_queue, result_queue, event, window, table_kwargs, kwargs, replace, step, title, click_type=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        if click_type is None:
            click_type = "click"
        connect_child_window(command_queue=command_queue, result_queue=result_queue, event=event, window=window, kwargs=table_kwargs, title=title, step=step, sleep_time=default_sleep_time)
        target_table = utils.window_dict.get(title)
        try:
            i = None
            target_table_replace = target_table
            for kw in replace.get("kwargs"):
                for key, value in kw.items():
                    target_table_replace = getattr(target_table_replace, key)(**value)
                    if isinstance(target_table_replace, list) :
                        target_table_replace = target_table_replace[0]
            match replace.get("type"):
                case "len-1":
                    i = len(target_table_replace.children())-1
                case "len":
                    i = len(target_table_replace.children())
            target_table.set_focus()
            control_click(command_queue=command_queue, result_queue =result_queue, window=title, kwargs=json.loads(json.dumps(kwargs) % i), step=step, click_type=click_type, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
        except (pywinauto.findwindows.ElementNotFoundError,IndexError,_ctypes.COMError,base_wrapper.ElementNotEnabled) as e:
            logger.log("找不到表格:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        except pywinauto.findwindows.ElementAmbiguousError:
            logger.log("找不到表格:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        loop = False

def wait(command_queue, result_queue, event, window, kwargs, step, ready, condition, index=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        if index is None:
            index = 0
        target_wait = utils.window_dict.get(window)
        try:
            for kw in kwargs:
                for key,value in kw.items():
                    target_wait = getattr(target_wait, key)(**value)
                    if isinstance(target_wait, list) :
                        if not isinstance(index, int):
                            index = int(index)
                        target_wait = target_wait[index]
            if not isinstance (target_wait, UIAWrapper) :
                if ready == "text":
                    if target_wait.legacy_properties()["Value"] != condition:
                        logger.log("等待:\nwindow:" + window + "\nkwargs:" + str(kwargs))
                        time.sleep(30)
                        continue
                else:
                    logger.log("等待:\nwindow:" + window + "\nkwargs:" + str(kwargs))
                    target_wait.wait(ready, timeout=30)
        except TimeoutError as e:
            logger.log("等待:\nwindow:" + window + "\nkwargs:" + str(kwargs))
            time.sleep(sleep_time)
            continue
        loop = False

def window_close(command_queue, result_queue, event, title, kwargs, step, index=None, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        if index is None:
            index = 0
        try:
            app = Application(default_backend).connect(title=title)
            target_window = app.window(title=title)
            target_window.wait('ready', timeout=60)
            for kw in kwargs:
                for key, value in kw.items():
                    target_window = getattr(target_window, key)(**value)
                    if isinstance(target_window, list):
                        if not isinstance(index, int):
                            index = int(index)
                        target_window = target_window[index]
            target_window.close()
        except (pywinauto.findwindows.ElementNotFoundError,TimeoutError) as e:
            pass
        loop = False

def ai_post(command_queue, result_queue, event, step, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    loop = True
    while loop:
        utils.pause(command_queue=command_queue, result_queue=result_queue, event=event)
        try:
            if int(utils.get_index()) == 0:
                with open("ai/" + utils.get_config("software") + "/text/index.txt", "r", encoding='utf-8') as text_file:
                    text = text_file.read()
                    if not text:
                        raise ViewException("AI提示词不能为空")
                    data_payload = {
                        "software": utils.get_config("software"),
                        "index": int(utils.get_index()),
                        "text": text
                    }
                if Path(utils.get_cue_img_url()).exists():
                    with open(utils.get_cue_img_url(), "rb") as img_file:  # 注意这里是 "rb" (read binary) 模式
                        files_payload = {
                            'img': (os.path.basename(utils.get_cue_img_url()), img_file.read(), 'image/png')
                        }
                    response = api_client.make_api_request_sync(method="post", endpoint="ai_post/", data=data_payload, files=files_payload)
                else:
                    response = api_client.make_api_request_sync(method="post", endpoint="ai_post/", data=data_payload)
            else:
                file_url = utils.get_dictionary("image_save_path")+"\\"+utils.get_temporary("数据处理", "1001")
                pdf_url = file_url + ".pdf"
                img_url = file_url + ".png"
                if not Path(pdf_url).exists():
                    raise ViewException("没有找到新的图谱，请先完成实验")
                else:
                    utils.set_view("add", utils.get_index(0), title="图谱文件:", type="url", content=pdf_url)
                    # wx.CallAfter(result_queue.view_init)
                    result_queue.put({"method": "view_init"})
                    chart = False
                pages = convert_from_path(
                    Path(pdf_url),
                    poppler_path=r'tools\poppler\Library\bin',  # 明确指定 Poppler 的 bin 路径
                    fmt='png'
                )
                if not pages:
                    raise ViewException("图谱文件内容为空")
                else:
                    max_width = 0
                    for page in pages:
                        max_width = max(max_width, page.width)
                    # 计算所有页面的总高度
                    total_height = 0
                    for page in pages:
                        total_height += page.height
                    # 3. 创建一张新的空白图片，用于存放拼接后的内容
                    # 使用 'RGB' 模式，背景色为白色 (255, 255, 255)
                    stitched_image = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                    # 4. 逐页将图片粘贴到新的空白图片上
                    current_height = 0
                    for page in pages:
                        # 将当前页面粘贴到拼接图片上，x 坐标为 0，y 坐标为当前累计高度
                        stitched_image.paste(page, (0, current_height))
                        # 更新累计高度，为下一页做准备
                        current_height += page.height
                    # 5. 保存拼接后的图片
                    # 对于 JPEG 格式，可以设置 quality 参数来控制文件大小和质量 (0-100)
                    stitched_image.save(img_url, 'png')
                with open(img_url, "rb") as img_file:  # 注意这里是 "rb" (read binary) 模式
                    files_payload = {
                        'img': (os.path.basename(img_url), img_file.read(), 'image/png')
                    }
                with open("ai/"+utils.get_config("software")+"/text/after.txt", "r", encoding='utf-8') as text_file:
                    data_payload = {
                        "software":utils.get_config("software"),
                        "index": utils.get_index(),
                        "text": text_file.read()
                    }
                response = api_client.make_api_request_sync(method="post", endpoint="ai_post/", data=data_payload, files=files_payload)
                try:
                    os.remove(img_url)
                except:
                    pass
            # 检查响应
            if response.status_code == 200:
                try:
                    response = response.json()
                    if response["success"] is True:
                        utils.clean_temporary()
                        result_dict = dict()
                        for item in response["data"].split("\n"):
                            kv = item.split(": ", 1)
                            if len(kv) == 2:
                                result_dict.update({kv[0]: kv[1]})
                        if utils.ai_response_item_is_null(result_dict, "Column_Temperature_C"):
                            new_data = utils.get_data("柱温箱")
                            new_data.update({"txtAimTemperatureSet":result_dict["Column_Temperature_C"]})
                            utils.set_data("柱温箱", new_data)
                        if utils.ai_response_item_is_null(result_dict, "Estimated_Run_Time_min"):
                            new_data = utils.get_data("方法概要")
                            new_data.update({"txtRunTime":result_dict["Estimated_Run_Time_min"]})
                            utils.set_data("方法概要", new_data)
                        if utils.ai_response_item_is_null(result_dict, "Detection_Wavelength_nm"):
                            new_data = utils.get_data("检测器")
                            new_data.update({"txtLambda1":result_dict["Detection_Wavelength_nm"]})
                            utils.set_data("检测器", new_data)
                        if utils.ai_response_item_is_null(result_dict, "Flow_Rate_mL_min"):
                            new_data = utils.get_data("泵")
                            new_data.update({"txtFlowVelocity": result_dict["Flow_Rate_mL_min"]})
                            utils.set_data("泵", new_data)
                        new_data = utils.get_data("泵")
                        new_data = {key: value for key, value in utils.get_data("泵").items() if " row" not in key}
                        utils.set_data("泵", new_data)
                        new_data = utils.get_data("柱温箱")
                        new_data = {key: value for key, value in utils.get_data("柱温箱").items() if " row" not in key}
                        utils.set_data("柱温箱", new_data)
                        if utils.ai_response_item_is_null(result_dict, "Ratio_A_B"):
                            ratio_a = result_dict["Ratio_A_B"].split(":",1)[0]
                            ratio_b = result_dict["Ratio_A_B"].split(":",1)[1]
                            # 等度泵列表
                            new_data = utils.get_data("泵")
                            new_data.update({"gcGradient": str(2)})
                            new_data.update({"时间(min) row0": str(0)})
                            new_data.update({"流速(mL/min) row0": result_dict["Flow_Rate_mL_min"]})
                            new_data.update({"%A row0": ratio_a})
                            new_data.update({"%B row0": ratio_b})
                            new_data.update({"时间(min) row1": result_dict["Estimated_Run_Time_min"]})
                            new_data.update({"流速(mL/min) row1": result_dict["Flow_Rate_mL_min"]})
                            new_data.update({"%A row1": ratio_a})
                            new_data.update({"%B row1": ratio_b})
                            utils.set_data("泵", new_data)
                            # 等度柱温箱列表
                            new_data = utils.get_data("柱温箱")
                            new_data.update({"gcEvent": str(2)})
                            new_data.update({"时间(min) row0": str(0)})
                            new_data.update({"事件值 row0": result_dict["Column_Temperature_C"]})
                            new_data.update({"时间(min) row1": result_dict["Estimated_Run_Time_min"]})
                            new_data.update({"事件值 row1": result_dict["Column_Temperature_C"]})
                            utils.set_data("柱温箱", new_data)
                        elif utils.ai_response_item_is_null(result_dict, "Gradient_Program"):
                            gradient_list = json.loads(result_dict["Gradient_Program"])
                            # 梯度泵列表
                            new_data = utils.get_data("泵")
                            new_data.update({"gcGradient": str(len(gradient_list))})
                            for i,gradient in enumerate(gradient_list):
                                new_data.update({"时间(min) row"+str(i): str(gradient[0])})
                                new_data.update({"流速(mL/min) row"+str(i): result_dict["Flow_Rate_mL_min"]})
                                new_data.update({"%A row" + str(i): str(100 - gradient[1] - (0 if len(gradient)<=2 else gradient[2]))})
                                new_data.update({"%B row"+str(i): str(gradient[1])})
                                if len(gradient)>2:
                                    new_data.update({"%C row"+str(i): str(gradient[2])})
                            utils.set_data("泵", new_data)
                            # 梯度柱温箱列表
                            new_data = utils.get_data("柱温箱")
                            new_data.update({"gcEvent": str(len(gradient_list))})
                            for i,gradient in enumerate(gradient_list):
                                new_data.update({"时间(min) row"+str(i): str(gradient[0])})
                                new_data.update({"事件值 row"+str(i): result_dict["Column_Temperature_C"]})
                            utils.set_data("柱温箱", new_data)
                except Exception as e:
                    logging.error(e)
                    raise ViewException("AI返回数据格式不对，请检查提示词")
            elif response.status_code == 409:
                response = response.json()
                if response["message"] == "请求重复":
                    utils.set_index(1)
                elif response["message"] == "请求无效":
                    utils.set_view(key="delete", index=utils.get_index())
                    # wx.CallAfter(result_queue.view_init)
                    result_queue.put({"method": "view_init"})
                    utils.set_index(-1)
                raise Exception(response["message"])
            elif response.status_code == 410 or response.status_code == 400:
                response = response.json()
                raise ViewException(response["message"])
            else:
                response = response.json()
                raise Exception(response["message"])
        except ViewException as ve:
            dlg = wx.MessageDialog(None, str(ve), "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源
            logger.log(ve)
            logging.exception(ve)
            utils.set_process_status(0)
            # wx.CallAfter(result_queue.init)
            result_queue.put({"method": "init"})
            continue
        except Exception as e:
            logger.log(e)
            logging.exception(e)
            continue
        utils.set_index(1)
        utils.set_view(key="add", index=utils.get_index(), title="AI返回:", type="text", content=response["data"])
        # wx.CallAfter(result_queue.view_init)
        result_queue.put({"method": "view_init"})
        loop = False