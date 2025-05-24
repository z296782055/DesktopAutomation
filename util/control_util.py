import copy
import json
import re
import time

import pyperclip
import pywinauto
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper

from util import utils
from util.logger_util import logger

default_sleep_time = float(utils.get_config('default_sleep_time', 1))
default_backend = "uia"

def start(self):
    step_list = utils.get_step_all(utils.get_config("software"))
    now_step_list = step_list[int(utils.get_config("step"))-1:]
    for step in now_step_list:
        utils.set_config("step", step_list.index(step) + 1)
        self.step_text.Label = next(iter(step))
        utils.window_dict.clear()
        for key, value in step.items():
            for automation in list(value):
                do_automation(key, automation)
                self.SetTitle(get_detail(automation))
    utils.set_config("step", 1)
    utils.set_config("event_status", 0)
    utils.set_config("thread_status", 0)
    self.SetTitle(utils.get_config("software"))
    self.refresh()

def get_detail(automation):
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
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            detail += ("\"" + (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id")) + "\"")
        case "edit_write":
            detail += "填写文本框:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            detail += ("\"" + (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id")) + "\"")
        case "list_select":
            detail += "列表选择:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            detail += ("\"" + (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id")) + "\"")
        case "edit_write":
            detail += "填写文本框:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            detail += ("\"" + (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id")) + "\"")
        case "check":
            detail += "选择复选框:"
            kwarg = next(iter(automation.get("kwargs")[-1].values()))
            detail += ("\"" + (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id")) + "\"")
        case "table_fill":
            detail += "填写表格:"
            kwarg = next(iter(automation.get("table_kwargs")[-1].values()))
            detail += ("\"" + (kwarg.get("title") if kwarg.get("title") else kwarg.get("auto_id")) + "\"")
    return detail

def do_automation(step, automation, sleep_time=default_sleep_time, before_sleep_time=0):
    auto_type = automation.get("auto_type")
    if auto_type == "connect_window":
        connect_window(title = automation.get("title"), sleep_time=sleep_time, before_sleep_time=before_sleep_time)
    elif auto_type == "connect_child_window":
        connect_child_window(window = automation.get("window"), kwargs = automation.get("kwargs"), title = automation.get("title"), step = step, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
    elif auto_type == "control_click":
        control_click(window = automation.get("window"), kwargs = automation.get("kwargs"), click_type = automation.get("click_type"), step = step, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
    elif auto_type == "list_select":
        list_select(window = automation.get("window"), kwargs = automation.get("kwargs") , click_type = automation.get("click_type"), step = step, select_window_title = automation.get("select_window_title"), select_window_kwargs = automation.get("select_window_kwargs"), sleep_time=sleep_time, before_sleep_time=before_sleep_time)
    elif auto_type == "edit_write":
        edit_write(window=automation.get("window"), kwargs = automation.get("kwargs"), step=step, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
    elif auto_type == "table_fill":
        table_fill(window=automation.get("window"), table_kwargs = automation.get("table_kwargs"), table_head_kwargs = automation.get("table_head_kwargs"), table_body_kwargs = automation.get("table_body_kwargs"), title = automation.get("title"), step=step, add = automation.get("add"), clear = automation.get("clear"), table_column = automation.get("table_column"), sleep_time=sleep_time, before_sleep_time=before_sleep_time)


def connect_window(title, backend = default_backend, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    window = None
    try:
        app = Application(backend).connect(title=title)
        window = app.window(title=title)
        utils.window_dict[title] = window
    except pywinauto.findwindows.ElementNotFoundError:
        logger.log("找不到窗口:\ntitle:" + title)
        time.sleep(sleep_time)
        window = connect_window(backend=backend, title=title, sleep_time=sleep_time)
    except pywinauto.findwindows.ElementAmbiguousError:
        logger.log("找到了多个窗口:\ntitle:" + title)
        time.sleep(sleep_time)
        window = connect_window(backend=backend, title=title, sleep_time=sleep_time)
    return window

def connect_child_window(window, kwargs, title, step, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
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
        connect_child_window(window=window, kwargs=kwargs, title=title, step=step, sleep_time=sleep_time)
    except pywinauto.findwindows.ElementAmbiguousError:
        logger.log("找到了多个子窗口:\nwindow:" + window + "\ntitle:" + title+"")
        time.sleep(sleep_time)
        connect_child_window(window=window, kwargs=kwargs, title=title, step=step, sleep_time=sleep_time)

def control_click(window, kwargs, step, click_type=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    if click_type is None:
        click_type = "click"
    target_control = utils.window_dict.get(window)
    try:
        for kw in kwargs:
            for key,value in kw.items():
                if value.get("control_type") == "Hyperlink":
                    value["title"] = utils.refer_dictionary(window)
                target_control = getattr(target_control, key)(**value)
                if isinstance(target_control, list) :
                    target_control = target_control[0]
        if not isinstance (target_control, UIAWrapper) :
            target_control = target_control.wrapper_object()
        try:
            getattr(target_control, click_type)()
        except AttributeError:
            getattr(target_control, click_type+"_input")()
    except (pywinauto.findwindows.ElementNotFoundError,IndexError) as e:
        logger.log("找不到控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        control_click(window=window, kwargs=kwargs, step = step, click_type=click_type, sleep_time=sleep_time)
    except pywinauto.findwindows.ElementAmbiguousError:
        logger.log("找到了多个控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        control_click(window=window, kwargs=kwargs, step=step, click_type=click_type, sleep_time=sleep_time)


def list_select(window, kwargs, step, click_type=None, select_window_title = None, select_window_kwargs=None, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    try:
        target_list = utils.window_dict.get(window)
        for kw in kwargs:
            for key, value in kw.items():
                target_list = getattr(target_list, key)(**value)
                if isinstance(target_list, list):
                    target_list = target_list[0]
        if not isinstance(target_list, UIAWrapper):
            target_list = target_list.wrapper_object()
        target_select_window = target_list
        if select_window_kwargs is None:
            select_window_kwargs = []
        if len(select_window_kwargs) != 0:
            connect_child_window(window = window, kwargs=select_window_kwargs, title=select_window_title, step=step, sleep_time=sleep_time)
            target_select_window = utils.window_dict.get(select_window_title)

        item = utils.get_data(utils.get_config("software")).get(step, "").get(target_list.element_info.automation_id if target_list.element_info.automation_id else target_list.element_info.name)
        try:
            if click_type == "double_click":
                target_list.click_input()
                time.sleep(0.5)
            if click_type != "no_click":
                target_list.click_input()
            if not isinstance(target_select_window, UIAWrapper):
                target_select_window = target_select_window.wrapper_object()
            if target_select_window.element_info.control_type == "Edit":
                target_select_window.set_text(item)
            else :
                target_select_window.select(item)
        except (TypeError,pywinauto.uia_defines.NoPatternInterfaceError,IndexError):
            target_list_item = target_select_window.descendants(title=item)
            if len(target_list_item) == 0:
                target_list_item = utils.window_dict.get(window).descendants(title=item)
            if len(target_list_item) != 0:
                target_list_item[0].click_input()
    except (pywinauto.findwindows.ElementNotFoundError,IndexError) as e:
        logger.log("找不到列表:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        list_select(window=window, kwargs=kwargs, step = step, click_type = click_type, select_window_title = select_window_title, select_window_kwargs=select_window_kwargs, sleep_time=sleep_time)
    except pywinauto.findwindows.ElementAmbiguousError:
        logger.log("找到了多个列表:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        list_select(window=window, kwargs=kwargs, step=step, click_type=click_type,
                    select_window_title=select_window_title, select_window_kwargs=select_window_kwargs,
                    sleep_time=sleep_time)

def edit_write(window, kwargs, step, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    target_edit = utils.window_dict.get(window)
    try:
        for kw in kwargs:
            for key, value in kw.items():
                target_edit = getattr(target_edit, key)(**value)
                if isinstance(target_edit, list) :
                    target_edit = target_edit[0]
        if not isinstance(target_edit, UIAWrapper):
            target_edit = target_edit.wrapper_object()
        text = utils.get_data(utils.get_config("software")).get(step,"").get(target_edit.element_info.automation_id if target_edit.element_info.automation_id else target_edit.element_info.name)
        if isinstance(text, int):
            text = utils.refer_dictionary(text)
        target_edit.type_keys("^a")
        try:
            target_edit.set_text(text)
        except AttributeError:
            pyperclip.copy(text)
            target_edit.type_keys("^v")
    except (pywinauto.findwindows.ElementNotFoundError,IndexError):
        logger.log("找不到控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        edit_write(window=window, kwargs=kwargs, step = step, sleep_time=sleep_time)
    except pywinauto.findwindows.ElementAmbiguousError:
        logger.log("找到了多个控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        edit_write(window=window, kwargs=kwargs, step = step, sleep_time=sleep_time)

def check(window, kwargs, step, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    target_check_box = utils.window_dict.get(window)
    try:
        for kw in kwargs:
            for key, value in kw.items():
                target_check_box = getattr(target_check_box, key)(**value)
                if isinstance(target_check_box, list) :
                    target_check_box = target_check_box[0]
        if not isinstance(target_check_box, UIAWrapper):
            target_check_box = target_check_box.wrapper_object()
        check_status = utils.get_data(utils.get_config("software")).get(step,"").get(target_check_box.element_info.automation_id if target_check_box.element_info.automation_id else target_check_box.element_info.name)
        if check_status == "True":
            target_check_box.check()
        else:
            target_check_box.uncheck()
    except (pywinauto.findwindows.ElementNotFoundError,IndexError):
        logger.log("找不到控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        check(window=window, kwargs=kwargs, step = step, sleep_time=sleep_time)
    except pywinauto.findwindows.ElementAmbiguousError:
        logger.log("找到了多个控件:\nwindow:" + window + "\nkwargs:" + str(kwargs))
        time.sleep(sleep_time)
        check(window=window, kwargs=kwargs, step = step, sleep_time=sleep_time)

def table_fill(window, step, table_kwargs, table_head_kwargs, table_body_kwargs, title, add, clear, table_column, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    connect_child_window(window=window, kwargs=table_kwargs, title=title, step=step, sleep_time=default_sleep_time)
    try:
        list_len = int(utils.get_data(utils.get_config("software")).get(step, "").get(title))
        for clear_item in clear:
            do_automation(step, clear_item, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
        for i in range(list_len):
            for add_item in add:
                do_automation(step, add_item, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
        for i in range(list_len):
            for column_item in table_column.get("column"):
                column_item = copy.copy(column_item)
                column_item["window"] = title
                column_item["kwargs"] = json.loads(json.dumps(column_item["kwargs"]) %i)
                do_automation(step, column_item, sleep_time=sleep_time, before_sleep_time=before_sleep_time)
    except pywinauto.findwindows.ElementNotFoundError as e:
        logger.log("找不到表格:\nwindow:" + window + "\ntable_kwargs:" + str(table_kwargs))
        time.sleep(sleep_time)
        table_fill(window=window, step=step, table_kwargs=table_kwargs, table_head_kwargs=table_head_kwargs, table_body_kwargs=table_body_kwargs, title=title, add=add, clear=clear, table_column=table_column, sleep_time=sleep_time)
    except pywinauto.findwindows.ElementAmbiguousError:
        logger.log("找到了多个表格:\nwindow:" + window + "\ntable_kwargs:" + str(table_kwargs))
        time.sleep(sleep_time)
        table_fill(window=window, step=step, table_kwargs=table_kwargs, table_head_kwargs=table_head_kwargs,
                   table_body_kwargs=table_body_kwargs, title=title, add=add, clear=clear, table_column=table_column,
                   sleep_time=sleep_time)
