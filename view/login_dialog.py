import requests
import wx

import util.utils
from util import utils, keyring_util
from util.keyring_util import api_client
from view.config_dialog import ConfigDialog

class LoginDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="登录", size=wx.Size(300, 200))
        self.parent = parent
        top_panel = wx.Panel(self, size=wx.Size(-1, 20))
        before_form_panel = wx.Panel(self)
        btn_panel = wx.Panel(self, size=wx.Size(-1, 40))
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(top_panel, 0, wx.EXPAND)
        box.Add(before_form_panel, 1, wx.EXPAND)
        box.Add(btn_panel, 0, wx.EXPAND)
        self.SetSizer(box)

        # 表单模块
        before_form_sizer = wx.BoxSizer(wx.HORIZONTAL)
        form_panel = wx.Panel(before_form_panel, size=wx.Size(250, -1))
        before_form_sizer.AddStretchSpacer(1)
        before_form_sizer.Add(form_panel, 0, wx.EXPAND)
        before_form_sizer.AddStretchSpacer(1)
        before_form_panel.SetSizer(before_form_sizer)
        form_sizer = wx.GridBagSizer(vgap=5, hgap=0)
        self.username_static_text=wx.StaticText(parent=form_panel, label="用户名：")
        ConfigDialog.draw_static_text(self.username_static_text)
        form_sizer.Add(window=self.username_static_text, flag=wx.ALIGN_CENTER|wx.ALL, pos=(0, 0), border=5)

        self.username_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), name="username")
        ConfigDialog.draw_text_ctrl(self.username_text_ctrl)
        form_sizer.Add(window=self.username_text_ctrl, flag=wx.ALIGN_CENTER|wx.ALL, pos=(0,1), border=5)

        self.password_static_text = wx.StaticText(parent=form_panel, label="密码：")
        ConfigDialog.draw_static_text(self.password_static_text)
        form_sizer.Add(window=self.password_static_text, flag=wx.ALIGN_CENTER|wx.ALL,
                       pos=wx.GBPosition(1, 0), border=5)

        self.password_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1,), style=wx.TE_PASSWORD, name="password")
        ConfigDialog.draw_text_ctrl(self.password_text_ctrl)
        form_sizer.Add(window=self.password_text_ctrl, flag=wx.ALIGN_CENTER|wx.ALL, pos=(1, 1), border=5)

        form_panel.SetSizer(form_sizer)

        # 底部按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        login_btn_panel = wx.Panel(btn_panel)

        # 创建按钮控件
        self.login_btn = wx.Button(login_btn_panel, label="登录")
        self.login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        login_btn_sizer = wx.BoxSizer()
        login_btn_sizer.Add(self.login_btn, 0, wx.CENTER)
        login_btn_panel.SetSizer(login_btn_sizer)
        btn_sizer.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        btn_sizer.Add(login_btn_panel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)  # 添加按钮到主Sizer，并使其居中，留出底部空间
        btn_sizer.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        btn_panel.SetSizer(btn_sizer)
        self.Centre()
        self.SetDefaultItem(self.login_btn)

    def on_login(self, event):
        if self.username_text_ctrl.GetValue() == "":
            dlg = wx.MessageDialog(self, "账号不能为空", "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源
            return
        elif self.password_text_ctrl.GetValue() == "":
            dlg = wx.MessageDialog(self, "密码不能为空", "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源
            return
        api_client.login(self.username_text_ctrl.GetValue(), self.password_text_ctrl.GetValue(), self._on_login_complete)
        # # 获取文本框中的值
        # headers = {
        #     "Content-Type":"application/x-www-form-urlencoded"
        # }
        # payload = {
        #     "username" : self.username_text_ctrl.GetValue(),
        #     "password" : self.password_text_ctrl.GetValue()
        # }
        # response = requests.post(url=utils.get_config("server_url")+"/user/token", headers=headers, data=payload)
        # if response.status_code == 200:
        #     util.utils.set_config("username", self.username_text_ctrl.GetValue())
        #     util.utils.set_config("password", self.password_text_ctrl.GetValue())
        #     keyring_util.save_token_to_keyring(self.username_text_ctrl.GetValue(), response.json()["access_token"])
        #     self.parent.init()
        #     self.Close()
        #     dlg = wx.MessageDialog(self, "登录成功！", "提示", wx.OK | wx.ICON_INFORMATION)
        #     dlg.ShowModal()  # 显示对话框
        #     dlg.Destroy()  # 销毁对话框，释放资源
        # else:
        #     dlg = wx.MessageDialog(self, response.json()["detail"], "提示", wx.OK | wx.ICON_INFORMATION)
        #     dlg.ShowModal()  # 显示对话框
        #     dlg.Destroy()  # 销毁对话框，释放资源

    def _on_login_complete(self, success, message):
        if success:
            util.utils.set_config("username", self.username_text_ctrl.GetValue())
            # util.utils.set_config("password", self.password_text_ctrl.GetValue())
            self.parent.init(token_flag=True)
            self.Close()
            dlg = wx.MessageDialog(self, "登录成功！", "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源
        else:
            dlg = wx.MessageDialog(self, message, "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源

    def on_cancel(self, event):
        # 关闭对话框
        self.Close()
