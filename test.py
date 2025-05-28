import datetime
import json
import os
import tempfile
import time

from pr_properties import pr_properties
from pywinauto.application import Application
from pywinauto import Desktop
from pywinauto.controls.uia_controls import TreeViewWrapper

from util import utils

config_url = r'./data/config.properties'


# print(json.loads(json.dumps(kwargs).format(1)))

# desktop = Desktop(backend="uia")  # 或者使用"win32"作为后端，取决于你的需求
# windows = desktop.windows()
# for window in windows:
#     print(window.window_text())


app = Application("uia").connect(title="实时采集 ")
window = app.window(title="实时采集 ")

main_window = window.child_window(**{"title":"sidePanel2", "auto_id":"sidePanel2", "control_type":"Pane"})
main_window = main_window.child_window(**{"title":"项目 ", "auto_id":"dpnlProject", "control_type":"Pane"})
main_window = main_window.child_window(**{"auto_id":"dockPanel1_Container", "control_type":"Pane"})
main_window = main_window.child_window(**{"auto_id":"_ucProjectBrowser", "control_type":"Pane"})
main_window = main_window.child_window(**{"title":"navBarControl1", "auto_id":"navBarControl1", "control_type":"Pane"})
main_window = main_window.child_window(**{"auto_id":"navBarGroupControlContainer3", "control_type":"Pane"})
main_window = main_window.child_window(**{"auto_id":"splitContainer1", "control_type":"Pane"})
main_window = main_window.child_window(**{"auto_id":"tlData", "control_type":"Tree"})
target_nodes = main_window.descendants(**{"control_type": "TreeItem"})
for target_node in target_nodes:
    if target_node.is_selected():
        try:
            getattr(target_node, "right_click")()
        except AttributeError:
            getattr(target_node, "right_click" + "_input")()
# main_window = main_window.wrapper_object()
# nodes = main_window.descendants(**{"control_type":"TreeItem"})
# for node in nodes:
#     if node.legacy_properties()["Value"] == "新建文件夹":
#         node.select()
#         node.click_input()

# for child in main_window.children() :
#     print(child.select())
# main_window.get_item(r"\新建项目新建项目新建项目新建项目新建项目新建项目新建项目新建项目").select()

# (**{"Value" : "新建文件夹"})
# main_window = window.child_window(**{"title":"DropDown", "control_type":"Menu"})
# main_window = main_window.child_window(**{"title":"添加行 ", "control_type":"MenuItem"})
# main_window.click_input()
#
# main_window = window.child_window(**{"title":"DropDown", "control_type":"Menu"})
# main_window = main_window.child_window(**{"title":"添加行 ", "control_type":"MenuItem"})
# main_window = main_window.child_window(**{"title":"1行 ", "control_type":"MenuItem"})
#
# main_window = main_window.child_window(**{"title":"sidePanel2", "auto_id":"sidePanel2", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"_Container","control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"_ucInsMethodEditor", "control_type":"Pane"})
# main_window = main_window.child_window(**{"title":"xtraScrollableControl1", "auto_id":"xtraScrollableControl1", "control_type":"Pane"})
# main_window = main_window.child_window(**{"title":"panelControlMain", "auto_id":"panelControlMain", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"InstrumentEditor", "control_type":"Window"})
# main_window = main_window.child_window(**{"title":"xtraTabPage1", "auto_id":"xtraTabPage1", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"NavBar", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"panelControl", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"CT3100IMEUI", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"tabMain", "control_type":"Tab"})
# main_window = main_window.child_window(**{"title":"常规 ", "auto_id":"tpGeneral", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"dvEvent", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"gcEvent", "control_type":"Table"})
# main_window1 = main_window.child_window(**{"title":"数据面板", "control_type":"Custom"})
# main_window1 = main_window1.child_window(**{"title":"行 1", "control_type":"Custom"})
# main_window1 = main_window1.child_window(**{"title":"事件类型 row0", "control_type":"DataItem"})
# main_window1.click_input()
# time.sleep(1)
# main_window1.click_input()
# main_window2 = main_window.child_window(**{"title":"编辑控件", "control_type":"Edit"})
# main_window2 = main_window2.wrapper_object()
# main_window2.set_text("停止控温")
# main_window2.select("停止控温")

# main_window = app.window(title="实时采集 ")
# main_window = main_window.child_window(**{"title":"sidePanel2", "auto_id":"sidePanel2", "control_type":"Pane"})
# main_window = main_window.child_window(**{"title":"仪器方法-新仪器方法?", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"_Container", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"_ucInsMethodEditor", "control_type":"Pane"})
# main_window = main_window.child_window(**{"title":"xtraScrollableControl1", "auto_id":"xtraScrollableControl1", "control_type":"Pane"})
# main_window.click_input()
# target_control = main_window.child_window(**{'auto_id':'btRealTimeAnalysis'})
# target_control.right_click()
# target_control.wait("visible", timeout=5)
# target_control.wait("enabled", timeout=5)

# control_type = target_control.element_info.control_type
# print("控件类型",control_type)
# target_control.click_input()
# if control_type == "Button":
#     print("控件是按钮，正在点击...")
#     target_control.click()
#     print("按钮点击完成。")
# elif control_type == "Edit":
#     text_to_type = "your_input_text" # 替换为你要输入的文本
#     print(f"控件是编辑框，正在输入文本: '{text_to_type}'...")
#     target_control.type_keys(text_to_type, with_spaces=True) # with_spaces=True 保留空格
#     print("文本输入完成。")
# elif control_type == "CheckBox":
#     print("控件是复选框，正在切换状态...")
#     target_control.toggle() # 切换复选框状态
#     print("复选框状态切换完成。")
