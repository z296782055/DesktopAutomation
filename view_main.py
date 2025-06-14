import multiprocessing
import os
import queue
import sys
import threading
import time
import wx
import wx.adv
from util import utils
from util.keyring_util import EVT_FORCE_RELOGIN_TYPE, api_client, EVT_FORCE_RELOGIN
from view.config_dialog import ConfigDialog
import wx.lib.scrolledpanel as scrolled
import keyboard

from view.cue_word_dialog import CueWordDialog
from view.info_dialog import InfoDialog
from view.login_dialog import LoginDialog
from view.logon_dialog import LogonDialog

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title=utils.get_config("software"), size=wx.Size(600, 400), style=wx.DEFAULT_FRAME_STYLE)

        self.event = multiprocessing.Event()

        icon = wx.Icon("img/icon/icon.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        self.SetTitle(utils.get_config("software"))
        self.Bind(wx.EVT_CONTEXT_MENU, self.show_context_menu)  # 绑定右键事件:ml-citation{ref="4" data="citationList"}
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # 创建菜单栏
        self.menubar = wx.MenuBar()
        menu_menu = wx.Menu()

        # new_item = menu_menu.Append(wx.ID_NEW, "新建(&N)\tCtrl+N")
        # open_item = menu_menu.Append(wx.ID_OPEN, "打开(&O)\tCtrl+O")

        config_item = menu_menu.Append(wx.ID_ANY, "配置(&F)\tCtrl+F")
        log_itm = menu_menu.Append(wx.ID_ANY, "日志(&L)\tCtrl+L")

        menu_menu.AppendSeparator()  # 添加分隔线:ml-citation{ref="2" data="citationList"}
        exit_item = menu_menu.Append(wx.ID_EXIT, "退出(&Q)\tCtrl+Q")
        self.menubar.Append(menu_menu, "&菜单")

        operate_menu = wx.Menu()
        restart_item = operate_menu.Append(wx.ID_ANY, "初始化(&R)\tCtrl+R")
        cu_word_item = operate_menu.Append(wx.ID_ANY, "AI提示词设置(&P)\tCtrl+P")
        self.menubar.Append(operate_menu, "&操作")

        view_menu = wx.Menu()
        info_item = view_menu.Append(wx.ID_ANY, "详细信息(&I)\tCtrl+I")
        self.menubar.Append(view_menu, "&查看")

        self.SetMenuBar(self.menubar)

        # self.Bind(wx.EVT_MENU, self.on_new, new_item)
        self.Bind(wx.EVT_MENU, self.on_config, config_item)
        self.Bind(wx.EVT_MENU, self.on_log, log_itm)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_info, info_item)
        self.Bind(wx.EVT_MENU, self.on_restart, restart_item)
        self.Bind(wx.EVT_MENU, self.on_cu_word, cu_word_item)

        box = wx.BoxSizer(wx.VERTICAL)
        top_panel = wx.Panel(self, size=wx.Size(-1, 40), style=wx.BORDER_SUNKEN)
        center_panel = wx.Panel(self, style=wx.BORDER_SUNKEN)
        bottom_panel = wx.Panel(self, size=wx.Size(-1, 50))
        box.Add(top_panel, 0, wx.EXPAND)
        box.Add(center_panel, 5, wx.EXPAND)
        box.Add(bottom_panel, 0, wx.EXPAND)
        self.SetSizer(box)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_panel_1 = wx.Panel(top_panel, size=wx.Size(60, -1))
        top_panel_2 = wx.Panel(top_panel, size=wx.Size(-1, -1))
        top_panel_3 = wx.Panel(top_panel, size=wx.Size(60, -1))

        top_sizer_2 = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.on_go_back_btn = wx.BitmapButton(parent=top_panel_2, style=wx.BORDER_NONE, size=wx.Size(50, -1),
                                              bitmap=wx.ArtProvider.GetBitmap(wx.ART_GO_BACK))
        self.on_go_back_btn.SetToolTip("上一步")
        self.on_go_back_btn.Bind(wx.EVT_BUTTON, self.on_go_back)
        self.on_go_forward_btn = wx.BitmapButton(parent=top_panel_2, style=wx.BORDER_NONE, size=wx.Size(50, -1),
                                              bitmap=wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD))
        self.on_go_forward_btn.SetToolTip("下一步")
        self.on_go_forward_btn.Bind(wx.EVT_BUTTON, self.on_go_forward)
        self.step_text = wx.StaticText(parent=top_panel_2, style=wx.ALIGN_CENTER, size=wx.Size(260, -1))
        font = wx.Font(12,  # 字号
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL,
                       faceName="微软雅黑")
        self.step_text.SetFont(font)

        top_sizer_2.Add(self.on_go_back_btn, 0, wx.ALIGN_CENTER)
        top_sizer_2.AddStretchSpacer(1)
        top_sizer_2.Add(self.step_text, 0, wx.ALIGN_CENTER)
        top_sizer_2.AddStretchSpacer(1)
        top_sizer_2.Add(self.on_go_forward_btn, 0, wx.ALIGN_CENTER)
        top_panel_2.SetSizer(top_sizer_2)

        top_sizer.Add(top_panel_1, 0, wx.EXPAND)
        top_sizer.Add(top_panel_2, 1, wx.EXPAND)
        top_sizer.Add(top_panel_3, 0, wx.EXPAND)
        top_panel.SetSizer(top_sizer)

        # 创建重新开始按钮控件
        image = wx.Bitmap("img/icon/login.png", wx.BITMAP_TYPE_ANY).ConvertToImage()
        scaled_image = image.Rescale(20, 20, wx.IMAGE_QUALITY_HIGH)
        scaled_bitmap = scaled_image.ConvertToBitmap()
        self.on_login_btn = wx.BitmapButton(parent=top_panel_3, style=wx.BORDER_NONE, bitmap=scaled_image)
        self.on_login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        self.on_login_btn.SetToolTip("登录")


        top_sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer_3.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        top_sizer_3.Add(self.on_login_btn, 0, wx.ALIGN_CENTER_VERTICAL, 0)  # 添加按钮到主Sizer，并使其居中，留出底部空间
        top_sizer_3.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        top_panel_3.SetSizer(top_sizer_3)

        # view_panel = wx.Panel(center_panel, size=wx.Size(-1, -1))
        self.view_panel = scrolled.ScrolledPanel(center_panel, -1, style=wx.VSCROLL | wx.HSCROLL)
        self.view_sizer = wx.BoxSizer(wx.VERTICAL)
        center_right_panel = wx.Panel(center_panel, size=wx.Size(0, -1))
        center_sizer = wx.BoxSizer(wx.HORIZONTAL)
        center_sizer.Add(self.view_panel, 1, wx.EXPAND)
        center_sizer.Add(center_right_panel, 0, wx.ALIGN_CENTER_VERTICAL)
        center_panel.SetSizer(center_sizer)
        self.view_init()

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        on_btn_panel = wx.Panel(bottom_panel)
        detail_panel = wx.Panel(bottom_panel)

        detail_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detail_static_text = wx.StaticText(parent=detail_panel, label="")
        ConfigDialog.draw_static_text(self.detail_static_text)
        detail_sizer.Add(self.detail_static_text, 1 ,wx.ALIGN_CENTER_VERTICAL)

        # 创建开始按钮控件
        self.on_btn = wx.Button(on_btn_panel, label="开始(&F11)")
        self.on_btn.Bind(wx.EVT_BUTTON, self.on_on)
        on_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        on_btn_sizer.Add(self.on_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        on_btn_panel.SetSizer(on_btn_sizer)

        bottom_sizer.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        bottom_sizer.Add(on_btn_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 0)  # 添加按钮到主Sizer，并使其居中，留出底部空间
        bottom_sizer.Add(detail_panel, 1, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 0)  # 添加按钮到主Sizer，并使其居中，留出底部空间

        bottom_panel.SetSizer(bottom_sizer)

        self.reverse_display_form()

        # 设置窗口布局和属性
        self.Centre()
        self.Show()
        self.Layout()  # 调用Layout来应用sizer布局
        auto_process = utils.process_is_alive("auto_process")
        if auto_process:
            utils.set_process_status(1)
        else:
            utils.set_process_status(0)
        self.init()
        # 4. 绑定自定义事件，使用你创建的事件绑定器常量
        self.Bind(EVT_FORCE_RELOGIN, self.on_login)  # <<< 直接使用 EVT_FORCE_RELOGIN

        # 启动时尝试通过refresh token自动登录
        if api_client.refresh_token:
            api_client.refresh_access_token(self.token_init)

        self.result_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_check_result, self.result_timer)  #

    def token_init(self, success, message):
        if success:
            image = wx.Bitmap("img/icon/logon.png", wx.BITMAP_TYPE_ANY).ConvertToImage()
            scaled_image = image.Rescale(24, 24, wx.IMAGE_QUALITY_HIGH)
            scaled_bitmap = scaled_image.ConvertToBitmap()
            self.on_login_btn.SetBitmapLabel(scaled_bitmap)  # 设置新的位图
            self.on_login_btn.Bind(wx.EVT_BUTTON, self.on_logon)
            self.on_login_btn.SetToolTip(utils.get_config("username", ""))
            self.on_login_btn.Refresh()
        else:
            image = wx.Bitmap("img/icon/login.png", wx.BITMAP_TYPE_ANY).ConvertToImage()
            scaled_image = image.Rescale(20, 20, wx.IMAGE_QUALITY_HIGH)
            scaled_bitmap = scaled_image.ConvertToBitmap()
            self.on_login_btn.SetBitmapLabel(scaled_bitmap)  # 设置新的位图
            self.on_login_btn.Bind(wx.EVT_BUTTON, self.on_login)
            self.on_login_btn.SetToolTip("登录")
            self.on_login_btn.Refresh()

    def init(self):
        if utils.get_process_status() == 1 and utils.get_event_status() == 1:
            self.on_btn.Bind(wx.EVT_BUTTON, self.on_off)
            self.on_btn.SetLabel("停止(&F12)")
            self.on_btn.Enable(True)
            self.on_go_back_btn.Enable(False)
            self.on_go_forward_btn.Enable(False)
            self.on_login_btn.Enable(False)
            self.menubar.EnableTop(0, False)
            self.menubar.EnableTop(1, False)
        else:
            self.on_btn.Bind(wx.EVT_BUTTON, self.on_on)
            self.on_btn.SetLabel("开始(&F11)")
            self.on_btn.Enable(True)
            self.on_go_back_btn.Enable(True)
            self.on_go_forward_btn.Enable(True)
            self.on_login_btn.Enable(True)
            self.menubar.EnableTop(0, True)
            self.menubar.EnableTop(1, True)
        self.step_text.Label = next(iter(utils.get_step_data(utils.get_config("software"), utils.get_step(), default="")))

    def view_init(self):
        self.view_sizer.Clear(delete_windows=True)
        index = 0
        for view_item in utils.get_view():
            if view_item.get("index") != index:
                index_static_text = wx.StaticText(parent=self.view_panel)
                index_static_text.SetLabel("第"+str(view_item.get("index"))+"次循环")
                index_text_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
                index_static_text.SetFont(index_text_font)
                if not view_item.get("is_active"):
                    disabled_text_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
                    index_static_text.SetForegroundColour(disabled_text_color)
                else:
                    index_static_text.SetForegroundColour(wx.RED)
                self.view_sizer.Add(index_static_text, 0, wx.ALL | wx.EXPAND, 5)
                index = view_item.get("index")
            title_static_text = wx.StaticText(parent=self.view_panel)
            title_static_text.SetLabel(view_item.get("title"))
            title_text_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            title_static_text.SetFont(title_text_font)
            if not view_item.get("is_active"):
                disabled_text_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
                title_static_text.SetForegroundColour(disabled_text_color)
            else:
                title_static_text.SetForegroundColour(wx.Colour(150, 50, 200))
            self.view_sizer.Add(title_static_text, 0, wx.LEFT, 10)

            if view_item.get("type") == "url":
                content_static_text = wx.adv.HyperlinkCtrl(self.view_panel, wx.ID_ANY,
                                                 label=f"{view_item.get("content")}",
                                                 url=f"file://{view_item.get("content")}")
                # 绑定 EVT_HYPERLINK 事件来自定义行为（例如，处理错误或执行额外操作）
                content_static_text.Bind(wx.adv.EVT_HYPERLINK, self.OnOpenFileLink)
            else:
                content_static_text = wx.StaticText(parent=self.view_panel)
                content_static_text.SetLabel(view_item.get("content"))
                ConfigDialog.draw_static_text(content_static_text)
            if not view_item.get("is_active"):
                disabled_text_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
                content_static_text.SetForegroundColour(disabled_text_color)
            self.view_sizer.Add(content_static_text, 0, wx.LEFT, 20)
        self.view_panel.SetSizer(self.view_sizer)
        self.view_panel.SetupScrolling()
        self.view_panel.Layout()
        wx.CallAfter(self.view_panel_scroll_bottom)

    def OnOpenFileLink(self, event):
        """处理点击本地文件链接的事件"""
        # event.GetURL() 可以获取到 HyperlinkCtrl 设置的 URL
        url = event.GetURL()
        # 移除 file:// 前缀，获取实际路径
        file_path = url.replace("file://", "")

        print(f"尝试打开文件: {file_path}")
        if not os.path.exists(file_path):
            wx.MessageBox(f"文件或目录不存在:\n{file_path}", "错误", wx.OK | wx.ICON_ERROR)
            return
        try:
            # HyperlinkCtrl 默认会尝试打开 URL，所以这里可以不写打开逻辑
            # 但如果你想做额外的检查或使用特定的打开方式，可以在这里实现
            # 例如，如果你不想依赖默认行为，可以调用自己的函数：
            # self._open_path_with_system_default(file_path)
            pass # 默认行为已经足够
        except Exception as e:
            wx.MessageBox(f"无法打开文件或目录:\n{file_path}\n错误: {e}", "错误", wx.OK | wx.ICON_ERROR)
        event.Skip()

    def view_panel_scroll_bottom(self):
        """将ScrolledPanel滚动到最底端"""
        # 获取垂直滚动条的最大滚动单位
        max_y_unit = self.view_panel.GetScrollRange(wx.VERTICAL)
        # Scroll(x, y) 方法接受的是逻辑单位，而不是像素
        # x 可以保持当前水平位置（0表示最左），y设置为最大单位
        self.view_panel.Scroll(0, max_y_unit)

    def on_new(self, event):
        pass
        # dlg = ConfigDialog(self)
        # dlg.ShowModal()  # 显示模态对话框
        # dlg.Destroy()  # 关闭后销毁对话框

    def on_config(self, event):
        dlg = ConfigDialog(self)
        dlg.ShowModal()  # 显示模态对话框
        dlg.Destroy()  # 关闭后销毁对话框

    def on_log(self, event):
        utils.get_log(self)

    def show_context_menu(self, event):
        context_menu = wx.Menu()
        # context_menu.Append(wx.ID_COPY, "复制(&C)\tCtrl+C")
        # context_menu.Append(wx.ID_PASTE, "粘贴(&V)\tCtrl+V")
        self.PopupMenu(context_menu)  # 显示上下文菜单:ml-citation{ref="4" data="citationList"}

    def on_exit(self, event):
        self.Close()
        event.Skip()

    def on_close(self, event):
        dlg = wx.MessageDialog(self, "确定要退出吗？", "确认", wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_YES:
            keyboard.unhook_all()
            utils.set_process_status(0)
            self.event.set()
            event.Skip()
        else:
            event.Veto()

    def on_on(self, event):
        def call(success, message):
            if success:
                from util import control_util
                utils.set_event_status(1)
                self.event.set()
                if utils.process_is_alive("auto_process"):
                    pass
                else:
                    self.command_queue = multiprocessing.Queue()
                    self.result_queue = multiprocessing.Queue()
                    process = multiprocessing.Process(
                        target=getattr(control_util, "start"),
                        args=(self.command_queue,self.result_queue,self.event),
                        daemon=True,
                        name="auto_process"
                    )
                    utils.set_process_status(1)
                    process.start()
                    self.result_timer.Start(100)
                    print(utils.prevent_sleep())
            else:
                call_dlg = wx.MessageDialog(self, message, "提示", wx.OK | wx.ICON_INFORMATION)
                call_dlg.ShowModal()  # 显示对话框
                call_dlg.Destroy()  # 销毁对话框，释放资源
            self.init()
            self.token_init(success, message)
        if api_client.refresh_token:
            self.on_btn.Enable(False)
            api_client.refresh_access_token(call)
        else:
            dlg = wx.MessageDialog(self, "登录信息失效，请重新登录", "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源
            self.on_login(self)
            return

    def on_check_result(self, event):
        """定时器触发，检查结果队列"""
        if not self.result_queue:
            # 如果队列不存在（可能启动失败或已完成），停止定时器
            print("[Main UI] 定时器触发，但结果队列不存在，停止定时器。")
            self.result_timer.Stop()
            return

        keep_checking = True
        try:
            # 循环获取，一次性处理完当前队列中的所有结果
            while True:
                # 4. 非阻塞地获取结果
                result = self.result_queue.get_nowait()  # 或者 get(block=False)
                # --- 5. 处理收到的结果 ---
                print(f"[Main UI] 从队列收到: {result}")
                method = result.get('method', None)
                args = result.get('args', {})
                getattr(self, method)(**args)
        except queue.Empty:
            # 队列为空是正常情况，表示这次检查没有新的结果
            # print("[Main UI] 结果队列暂时为空")
            pass  # 什么都不做，等待下次定时器触发

        except Exception as e:
            error_msg = f"处理结果时发生意外错误: {e}"
            print(f"[Main UI] {error_msg}")
            keep_checking = False  # 发生错误，停止检查
        finally:
            if not keep_checking:
                pass

    def on_off(self, event):
        self.on_btn.Enable(False)
        auto_process = utils.process_is_alive("auto_process")
        if auto_process:
            utils.set_event_status(0)
        utils.allow_sleep()

    def on_restart(self, event):
        result = wx.MessageBox("初始化后将重新开始，您确定吗？", "确认", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            utils.set_index(0, 0)
            utils.set_process_status(0)
            utils.set_step(1, 0)
            utils.set_event_status(1)
            self.event.set()
            utils.set_view("clear")
            self.view_init()
            self.SetTitle(utils.get_config("software"))
            self.disable()
            self.init()
            self.result_timer.Stop()
            utils.allow_sleep()

    def on_go_forward(self, event):
        self.on_go(step_num = 1)

    def on_go_back(self, event):
        self.on_go(step_num = -1)

    def on_go(self, step_num = 0):
        if utils.process_is_alive("auto_process"):
            result = wx.MessageBox("换页后将从选择步骤起始处开始，确认要换页吗？", "确认", wx.YES_NO | wx.ICON_QUESTION)
            if result == wx.YES:
                utils.set_step(step_num)
                utils.set_process_status(0)
                utils.set_event_status(1)
                self.event.set()
                self.disable()
                self.result_timer.Stop()
                utils.allow_sleep()
        else:
            utils.set_step(step_num)
        self.init()

    def on_info(self, event):
        dlg = InfoDialog(self)
        dlg.ShowModal()  # 显示模态对话框
        dlg.Destroy()  # 关闭后销毁对话框

    def on_login(self, event):
        dlg = LoginDialog(self)
        dlg.ShowModal()  # 显示模态对话框
        dlg.Destroy()  # 关闭后销毁对话框

    def on_logon(self, event):
        dlg = LogonDialog(self)
        dlg.ShowModal()  # 显示模态对话框
        dlg.Destroy()  # 关闭后销毁对话框

    def on_cu_word(self, event):
        dlg = CueWordDialog(self)
        dlg.ShowModal()  # 显示模态对话框
        dlg.Destroy()  # 关闭后销毁对话框

    def disable(self):
        self.on_btn.Enable(False)
        self.on_go_back_btn.Enable(False)
        self.on_go_forward_btn.Enable(False)
        self.on_login_btn.Enable(False)

    def reverse_display_form(self):
        pass
        # text_ctrl_list = utils.traverse_elements(self, element_type=wx.TextCtrl)
        # for text_ctrl in text_ctrl_list:
        #     text_ctrl.SetValue(utils.get_config(text_ctrl.GetName()))
        # combo_box_list = utils.traverse_elements(self, element_type=wx.ComboBox)
        # for combo_box in combo_box_list:
        #     combo_box.SetValue(utils.get_config(combo_box.GetName()))

if __name__ == '__main__':
    multiprocessing.freeze_support()  # 推荐，尤其在 Windows 或打包应用时
    app = wx.App()
    frame = MyFrame()
    frame.Show()
    keyboard.on_press_key("F11", frame.on_on)
    keyboard.on_press_key("F12", frame.on_off)
    app.MainLoop()

