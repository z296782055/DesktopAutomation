import re
import sys

import wx

from util import utils
from util.validator_util import NumberValidator, OsPathValidator

class AddDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="新建", size=wx.Size(500, 600))

        top_panel = wx.Panel(self, size=wx.Size(-1, 4))
        before_form_panel = wx.Panel(self)
        btn_panel = wx.Panel(self, size=wx.Size(-1, 40))
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(top_panel, 0, wx.EXPAND)
        box.Add(before_form_panel, 1, wx.EXPAND)
        box.Add(btn_panel, 0, wx.EXPAND)
        self.SetSizer(box)

        # 表单模块
        before_form_sizer = wx.BoxSizer(wx.HORIZONTAL)
        form_left_panel = wx.Panel(before_form_panel, size=wx.Size(4, -1))
        form_panel = wx.Panel(before_form_panel)
        before_form_sizer.Add(form_left_panel, 0, wx.EXPAND)
        before_form_sizer.Add(form_panel, 1, wx.EXPAND)
        before_form_panel.SetSizer(before_form_sizer)

        form_sizer = wx.GridBagSizer(vgap=5, hgap=0)
        self.default_sleep_time_static_text=wx.StaticText(parent=form_panel, label="点击间隔时间：")
        AddDialog.draw_static_text(self.default_sleep_time_static_text)
        form_sizer.Add(window=self.default_sleep_time_static_text, flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, pos=wx.GBPosition(0, 0), border=0)

        self.default_sleep_time_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), validator=NumberValidator(), name="default_sleep_time")
        AddDialog.draw_text_ctrl(self.default_sleep_time_text_ctrl)
        form_sizer.Add(window=self.default_sleep_time_text_ctrl, flag=wx.ALIGN_CENTER_VERTICAL, pos=(0,1), border=0)

        self.default_sleep_time_unit_static_text = wx.StaticText(parent=form_panel, label="  秒")
        AddDialog.draw_static_text(self.default_sleep_time_unit_static_text)
        form_sizer.Add(window=self.default_sleep_time_unit_static_text, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
                       pos=wx.GBPosition(0, 2), border=0)

        self.default_file_name_format_static_text=wx.StaticText(form_panel, label="文件默认名称格式：")
        AddDialog.draw_static_text(self.default_file_name_format_static_text)
        form_sizer.Add(window=self.default_file_name_format_static_text, flag=wx.ALIGN_CENTER_VERTICAL,
                       pos=wx.GBPosition(1, 0), border=0)
        self.default_file_name_format_combo_box = wx.ComboBox(form_panel,name="default_file_name_format", value="YYYYMMDDHHmmss",choices=["YYYYMMDDHHmmss","YYYYMMDD"],size=wx.Size(140, -1),style=wx.CB_READONLY)
        AddDialog.draw_combo_box(self.default_file_name_format_combo_box)
        form_sizer.Add(window=self.default_file_name_format_combo_box, flag=wx.ALIGN_CENTER_VERTICAL, pos=(1, 1), border=0)

        self.image_save_path_static_text = wx.StaticText(form_panel, label="图片保存路径：")
        AddDialog.draw_static_text(self.image_save_path_static_text)
        form_sizer.Add(window=self.image_save_path_static_text, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                       pos=wx.GBPosition(2, 0), border=0)
        self.image_save_path_text_ctrl = wx.TextCtrl(form_panel, name="image_save_path",size=wx.Size(140, -1), validator=OsPathValidator())
        AddDialog.draw_text_ctrl(self.image_save_path_text_ctrl)
        form_sizer.Add(window=self.image_save_path_text_ctrl, flag=wx.ALIGN_CENTER_VERTICAL, pos=(2, 1), border=0)
        AddDialog.draw_text_ctrl(self.image_save_path_text_ctrl)
        self.image_save_path_btn = wx.Button(form_panel, label="..", size=wx.Size(30, -1))
        AddDialog.draw_button(self.image_save_path_btn)
        self.image_save_path_btn.Bind(wx.EVT_BUTTON, self.image_save_path_btn_click)
        form_sizer.Add(window=self.image_save_path_btn, flag=wx.ALIGN_CENTER_VERTICAL, pos=(2, 2), border=0)
        form_panel.SetSizer(form_sizer)

        # 底部按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        submit_btn_panel = wx.Panel(btn_panel)
        border_btn_panel = wx.Panel(btn_panel, size=wx.Size(20, -1))
        cancel_btn_panel = wx.Panel(btn_panel)


        # 创建按钮控件
        self.submit_btn = wx.Button(submit_btn_panel, label="确定")
        self.submit_btn.Bind(wx.EVT_BUTTON, self.on_submit)
        submit_btn_sizer = wx.BoxSizer()
        submit_btn_sizer.Add(self.submit_btn, 0, wx.CENTER)
        submit_btn_panel.SetSizer(submit_btn_sizer)

        # 创建取消按钮
        self.cancel_btn = wx.Button(cancel_btn_panel, label="取消")
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        cancel_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cancel_btn_sizer.Add(self.cancel_btn, 0, wx.CENTER)
        cancel_btn_panel.SetSizer(cancel_btn_sizer)

        btn_sizer.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        btn_sizer.Add(submit_btn_panel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)  # 添加按钮到主Sizer，并使其居中，留出底部空间
        btn_sizer.Add(border_btn_panel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)  # 添加按钮到主Sizer，并使其居中，留出底部空间
        btn_sizer.Add(cancel_btn_panel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)  # 添加按钮到主Sizer，并使其居中，留出底部空间
        btn_sizer.AddStretchSpacer(1)  # 这将添加一个伸展的空间器，使得按钮在底部中间
        btn_panel.SetSizer(btn_sizer)

        utils.reverse_display_form(self)

    def on_submit(self, event):
        # 获取文本框中的值
        default_sleep_time = self.default_sleep_time_text_ctrl.GetValue()
        default_file_name_format = self.default_file_name_format_combo_box.GetValue()
        image_save_path = self.image_save_path_text_ctrl.GetValue()
        utils.set_config("default_sleep_time", default_sleep_time)
        utils.set_config("default_file_name_format", default_file_name_format)
        utils.set_config("image_save_path", image_save_path)
        # 关闭对话框
        self.Close()
        dlg = wx.MessageDialog(self, "保存成功！", "提示", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()  # 显示对话框
        dlg.Destroy()  # 销毁对话框，释放资源

    def on_cancel(self, event):
        # 关闭对话框
        self.Close()

    def image_save_path_btn_click(self, event):
        dlg = wx.DirDialog(self, "选择一个文件夹", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            folder_path = dlg.GetPath()
        print("选择的文件夹是:", folder_path)
        self.image_save_path_text_ctrl.SetValue(folder_path)
        dlg.Destroy()

    @staticmethod
    def draw_static_text(static_text):
        static_text_font = wx.Font()
        static_text.SetFont(static_text_font)

    @staticmethod
    def draw_text_ctrl(text_ctrl):
        text_ctrl.SetWindowStyle(wx.BORDER_SIMPLE)
        text_ctrl.SetBackgroundColour('lightgrey')
        text_ctrl.SetForegroundColour('black')

    @staticmethod
    def draw_combo_box(combo_box):
        combo_box.SetBackgroundColour('lightgrey')  # 设置背景色
        combo_box.SetForegroundColour('black')  # 设置文字颜色

    @staticmethod
    def draw_button(button):
        pass
        # button.SetBackgroundColour('lightgrey')  # 设置背景色
        # button.SetForegroundColour('black')  # 设置文字颜色

