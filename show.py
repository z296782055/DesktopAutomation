import contextlib
import io
import time

from pywinauto import Desktop, Application
import json

from util import utils, control_util

# desktop = Desktop(backend="uia")  # 或者使用"win32"作为后端，取决于你的需求
# windows = desktop.windows()
# for window in windows:
#     print(window.window_text())
print("----------------------")
time.sleep(3)
app = Application("uia").connect(title="实时采集 ")
main_window = app.window(title="实时采集 ")
# main_window = main_window.child_window(**{"title":"sidePanel2", "auto_id":"sidePanel2", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"_Container","control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"_ucInsMethodEditor", "control_type":"Pane"})
# main_window = main_window.child_window(**{"title":"xtraScrollableControl1", "auto_id":"xtraScrollableControl1", "control_type":"Pane"})
# main_window = main_window.child_window(**{"title":"panelControlMain", "auto_id":"panelControlMain", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"InstrumentEditor", "control_type":"Window"})
# main_window = main_window.child_window(**{"title":"xtraTabPage1", "auto_id":"xtraTabPage1", "control_type":"Pane"})
# main_window = main_window.child_window(**{"auto_id":"NavBar", "control_type":"Pane"})
# automation_list = utils.get_step(key=utils.get_config("software"), step=5).get(step)
# control_util.connect_window(title=title)
# automation = automation_list[1]
# control_util.connect_child_window(window = automation.get("window"), kwargs = automation.get("kwargs"), title = automation.get("title"), step = step)
# main_window.print_control_identifiers()

buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    # 在这里调用 print_control_identifiers()，其输出会被捕获到 buffer 中
    main_window.print_control_identifiers()
captured_output = buffer.getvalue()
with open(r"D:\t_tran_log.sql", 'w', encoding='utf-8') as f:
    f.write(captured_output)

print("-----------------------")
