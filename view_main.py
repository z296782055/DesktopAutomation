import threading
import time
import wx
from util import utils, keyring_util
from util.keyring_util import EVT_FORCE_RELOGIN_TYPE, api_client, EVT_FORCE_RELOGIN
from util.validator_util import NumberValidator
from view.config_dialog import ConfigDialog
import keyboard

from view.info_dialog import InfoDialog
from view.login_dialog import LoginDialog
from view.logon_dialog import LogonDialog


class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title=utils.get_config("software"), size=wx.Size(500, 300), style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)

        self.lock = threading.Lock()
        self.Center()  # 窗口居中
        # self.panel = wx.Panel(self)
        self.Bind(wx.EVT_CONTEXT_MENU, self.show_context_menu)  # 绑定右键事件:ml-citation{ref="4" data="citationList"}

        # 创建菜单栏
        self.menubar = wx.MenuBar()
        menu_menu = wx.Menu()

        new_item = menu_menu.Append(wx.ID_NEW, "新建(&N)\tCtrl+N")
        open_item = menu_menu.Append(wx.ID_OPEN, "打开(&O)\tCtrl+O")

        config_item = menu_menu.Append(wx.ID_ANY, "配置(&F)\tCtrl+F")
        log_itm = menu_menu.Append(wx.ID_ANY, "日志(&L)\tCtrl+L")

        menu_menu.AppendSeparator()  # 添加分隔线:ml-citation{ref="2" data="citationList"}
        exit_item = menu_menu.Append(wx.ID_EXIT, "退出(&Q)\tCtrl+Q")
        self.menubar.Append(menu_menu, "&菜单")

        operate_menu = wx.Menu()
        restart_item = operate_menu.Append(wx.ID_ANY, "初始化(&R)\tCtrl+R")
        self.menubar.Append(operate_menu, "&操作")

        view_menu = wx.Menu()
        info_item = view_menu.Append(wx.ID_ANY, "详细信息(&I)\tCtrl+I")
        self.menubar.Append(view_menu, "&查看")

        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.on_new, new_item)
        self.Bind(wx.EVT_MENU, self.on_config, config_item)
        self.Bind(wx.EVT_MENU, self.on_log, log_itm)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_info, info_item)
        self.Bind(wx.EVT_MENU, self.on_restart, restart_item)


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
        self.on_login_btn.SetToolTip("登录")

        top_sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer_3.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        top_sizer_3.Add(self.on_login_btn, 0, wx.ALIGN_CENTER_VERTICAL, 0)  # 添加按钮到主Sizer，并使其居中，留出底部空间
        top_sizer_3.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        top_panel_3.SetSizer(top_sizer_3)

        form_panel = wx.Panel(center_panel, size=wx.Size(-1, -1))
        center_right_panel = wx.Panel(center_panel, size=wx.Size(0, -1))
        center_sizer = wx.BoxSizer(wx.HORIZONTAL)
        center_sizer.Add(form_panel, 1, wx.ALIGN_CENTER_VERTICAL)
        center_sizer.Add(center_right_panel, 0, wx.ALIGN_CENTER_VERTICAL)
        center_panel.SetSizer(center_sizer)
        self.form_init(form_panel)

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
        self.init(token_flag=True if utils.get_config("username") else False)

        # 4. 绑定自定义事件，使用你创建的事件绑定器常量
        self.Bind(EVT_FORCE_RELOGIN, self.on_login)  # <<< 直接使用 EVT_FORCE_RELOGIN

        # 启动时尝试通过refresh token自动登录
        def callback(success, message):
            if success:
                self.init(token_flag=True)
            else:
                self.init(token_flag=False)
        if api_client.refresh_token:
            api_client.refresh_access_token(callback)
        else:
            self.init(token_flag=False)

    # self.login_verify()

    def init(self,token_flag=False):
        auto_thread = utils.thread_is_alive("auto_thread")
        if auto_thread and utils.get_config("event_status", 1) == "1":
            self.on_btn.Bind(wx.EVT_BUTTON, self.on_off)
            self.on_btn.SetLabel("停止(&F12)")
            self.on_go_back_btn.Enable(False)
            self.on_go_forward_btn.Enable(False)
            self.on_login_btn.Enable(False)
            self.menubar.EnableTop(0, False)
            self.menubar.EnableTop(1, False)
        else:
            self.on_btn.Bind(wx.EVT_BUTTON, self.on_on)
            self.on_btn.SetLabel("开始(&F11)")
            self.on_go_back_btn.Enable(True)
            self.on_go_forward_btn.Enable(True)
            self.on_login_btn.Enable(True)
            self.on_btn.Enable(True)
            self.menubar.EnableTop(0, True)
            self.menubar.EnableTop(1, True)
        if token_flag:
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
        self.step_text.Label = next(iter(utils.get_step(utils.get_config("software"), utils.get_config("step"), default="")))
        self.SetTitle(utils.get_config("software"))

    def form_init(self, form_panel):
        form_sizer = wx.GridBagSizer(vgap=10, hgap=10)

        self.a_static_text = wx.StaticText(parent=form_panel, label="数据a：")
        ConfigDialog.draw_static_text(self.a_static_text)
        form_sizer.Add(window=self.a_static_text, flag=wx.ALIGN_CENTER | wx.ALL,
                       pos=wx.GBPosition(0, 0), border=5)
        self.a_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), validator=NumberValidator(),
                                                    name="数据a")
        ConfigDialog.draw_text_ctrl(self.a_text_ctrl)
        form_sizer.Add(window=self.a_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(0, 1), border=5)

        self.b_static_text = wx.StaticText(parent=form_panel, label="数据b：")
        ConfigDialog.draw_static_text(self.b_static_text)
        form_sizer.Add(window=self.b_static_text, flag=wx.ALIGN_CENTER | wx.ALL,
                       pos=wx.GBPosition(0, 2), border=5)
        self.b_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), validator=NumberValidator(),
                                       name="数据b")
        ConfigDialog.draw_text_ctrl(self.b_text_ctrl)
        form_sizer.Add(window=self.b_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(0, 3), border=5)

        self.c_static_text = wx.StaticText(parent=form_panel, label="数据c：")
        ConfigDialog.draw_static_text(self.c_static_text)
        form_sizer.Add(window=self.c_static_text, flag=wx.ALIGN_CENTER | wx.ALL,
                       pos=wx.GBPosition(1, 0), border=5)
        self.c_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), validator=NumberValidator(),
                                       name="数据c")
        ConfigDialog.draw_text_ctrl(self.c_text_ctrl)
        form_sizer.Add(window=self.c_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(1, 1), border=5)

        self.d_static_text = wx.StaticText(parent=form_panel, label="数据d：")
        ConfigDialog.draw_static_text(self.d_static_text)
        form_sizer.Add(window=self.d_static_text, flag=wx.ALIGN_CENTER | wx.ALL,
                       pos=wx.GBPosition(1, 2), border=5)
        self.d_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), validator=NumberValidator(),
                                       name="数据d")
        ConfigDialog.draw_text_ctrl(self.d_text_ctrl)
        form_sizer.Add(window=self.d_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(1, 3), border=5)

        form_panel.SetSizer(form_sizer)

    def refresh(self):
        while True:
            time.sleep(1)
            self.init(token_flag=True if utils.get_config("username") else False)
            if self.on_btn.Label == "开始(&F11)":
                break

    def Close(self, force=False):
        result = wx.MessageBox("确定要退出吗？", "确认", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            keyboard.unhook_all()
            utils.set_config("thread_status", 0)
            utils.event.set()
            super().Close()

    def on_new(self, event):
        dlg = ConfigDialog(self)
        dlg.ShowModal()  # 显示模态对话框
        dlg.Destroy()  # 关闭后销毁对话框

    def on_config(self, event):
        dlg = ConfigDialog(self)
        dlg.ShowModal()  # 显示模态对话框
        dlg.Destroy()  # 关闭后销毁对话框

    def on_log(self, event):
        utils.get_log(self)

    def show_context_menu(self, event):
        context_menu = wx.Menu()
        context_menu.Append(wx.ID_COPY, "复制(&C)\tCtrl+C")
        context_menu.Append(wx.ID_PASTE, "粘贴(&V)\tCtrl+V")
        self.PopupMenu(context_menu)  # 显示上下文菜单:ml-citation{ref="4" data="citationList"}

    def on_exit(self, event):
        self.Close()
        event.Skip()

    def on_on(self, event):
        # if not self.login_verify():
        #     dlg = wx.MessageDialog(self, "登录信息失效，请重新登录", "提示", wx.OK | wx.ICON_INFORMATION)
        #     dlg.ShowModal()  # 显示对话框
        #     dlg.Destroy()  # 销毁对话框，释放资源
        #     self.on_login(self)
        #     return
        # 启动时尝试通过refresh token自动登录
        def call(success, message):
            if success:
                with self.lock:
                    from util import control_util
                    utils.set_config("event_status", 1)
                    utils.event.set()
                    if utils.thread_is_alive("auto_thread" ):
                        pass
                    else:
                        thread = threading.Thread(target=getattr(control_util, "start"),args=(self,),name="auto_thread")
                        utils.set_config("thread_status", 1)
                        thread.start()
                    try:
                        self.init(token_flag=True)
                    except Exception as e:
                        pass
            else:
                call_dlg = wx.MessageDialog(self, message, "提示", wx.OK | wx.ICON_INFORMATION)
                call_dlg.ShowModal()  # 显示对话框
                call_dlg.Destroy()  # 销毁对话框，释放资源
        if api_client.refresh_token:
            api_client.refresh_access_token(call)
        else:
            dlg = wx.MessageDialog(self, "登录信息失效，请重新登录", "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源
            self.on_login(self)
            return

    def on_off(self, event):
        with self.lock:
            auto_thread = utils.thread_is_alive("auto_thread")
            if auto_thread:
                utils.set_config("event_status", 0)
            try:
                self.refresh()
            except Exception as e:
                pass

    def on_restart(self, event):
        result = wx.MessageBox("初始化后将重新开始，您确定吗？", "确认", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            utils.set_config("index", 0)
            utils.set_config("thread_status", 0)
            utils.set_config("step", 1)
            utils.set_config("event_status", 1)
            utils.event.set()
            self.disable()
            self.refresh()

    def on_go_forward(self, event):
        self.on_go(step_num = 1)

    def on_go_back(self, event):
        self.on_go(step_num = -1)

    def on_go(self, step_num = 0):
        utils.set_step(step_num)
        if utils.thread_is_alive("auto_thread"):
            result = wx.MessageBox("换页后将从选择步骤起始处开始，确认要换页吗？", "确认", wx.YES_NO | wx.ICON_QUESTION)
            if result == wx.YES:
                utils.set_config("thread_status", 0)
                utils.set_config("event_status", 1)
                utils.event.set()
                self.disable()
                self.refresh()
        else:
            self.init(token_flag=True if utils.get_config("username") else False)

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

    # def login_verify(self):
    #     if not utils.login_verify():
    #         keyring_util.delete_token_from_keyring(utils.get_config("username"))
    #         utils.set_config("username", "")
    #         utils.set_config("password", "")
    #         self.init()
    #         return False
    #     return True

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
    app = wx.App()
    frame = MyFrame()
    frame.Show()
    keyboard.on_press_key("F11", frame.on_on)
    keyboard.on_press_key("F12", frame.on_off)
    app.MainLoop()

