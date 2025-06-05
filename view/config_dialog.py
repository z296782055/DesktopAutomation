import threading

import wx
from util import utils
from util.validator_util import NumberValidator, OsPathValidator

class ConfigDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="配置", size=wx.Size(540, 200))

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

        self.泵_static_text=wx.StaticText(parent=form_panel, label="泵：")
        ConfigDialog.draw_static_text(self.泵_static_text)
        form_sizer.Add(window=self.泵_static_text, flag=wx.ALIGN_CENTER | wx.ALL, pos=(0, 0), border=5)

        self.泵_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), name="泵")
        ConfigDialog.draw_text_ctrl(self.泵_text_ctrl)
        form_sizer.Add(window=self.泵_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(0,1), border=5)

        self.柱温箱_static_text = wx.StaticText(parent=form_panel, label="柱温箱：")
        ConfigDialog.draw_static_text(self.柱温箱_static_text)
        form_sizer.Add(window=self.柱温箱_static_text, flag=wx.ALIGN_CENTER | wx.ALL,
                       pos=wx.GBPosition(1, 0), border=5)

        self.柱温箱_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), name="柱温箱")
        ConfigDialog.draw_text_ctrl(self.柱温箱_text_ctrl)
        form_sizer.Add(window=self.柱温箱_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(1, 1), border=5)

        self.检测器_static_text = wx.StaticText(parent=form_panel, label="检测器：")
        ConfigDialog.draw_static_text(self.检测器_static_text)
        form_sizer.Add(window=self.检测器_static_text, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                       pos=wx.GBPosition(2, 0), border=5)

        self.检测器_text_ctrl = wx.TextCtrl(form_panel, size=wx.Size(140, -1), name="检测器")
        ConfigDialog.draw_text_ctrl(self.检测器_text_ctrl)
        form_sizer.Add(window=self.检测器_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(2, 1), border=5)

        self.default_file_name_static_text=wx.StaticText(form_panel, label="文件默认名称格式：")
        ConfigDialog.draw_static_text(self.default_file_name_static_text)
        form_sizer.Add(window=self.default_file_name_static_text, flag=wx.ALIGN_CENTER | wx.ALL,
                       pos=wx.GBPosition(0, 2), border=5)
        self.default_file_name_combo_box = wx.ComboBox(form_panel,name="default_file_name", value="%Y%m%d%H%M%S",choices=["%Y%m%d%H%M%S","%Y%m%d"],size=wx.Size(140, -1),style=wx.CB_READONLY)
        ConfigDialog.draw_combo_box(self.default_file_name_combo_box)
        form_sizer.Add(window=self.default_file_name_combo_box, flag=wx.ALIGN_CENTER | wx.ALL, pos=(0, 3), border=5)

        self.image_save_path_static_text = wx.StaticText(form_panel, label="图片保存路径：")
        ConfigDialog.draw_static_text(self.image_save_path_static_text)
        form_sizer.Add(window=self.image_save_path_static_text, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                       pos=wx.GBPosition(1, 2), border=5)
        self.image_save_path_text_ctrl = wx.TextCtrl(form_panel, name="image_save_path",size=wx.Size(140, -1), validator=OsPathValidator())
        ConfigDialog.draw_text_ctrl(self.image_save_path_text_ctrl)
        form_sizer.Add(window=self.image_save_path_text_ctrl, flag=wx.ALIGN_CENTER | wx.ALL, pos=(1, 3), border=5)
        ConfigDialog.draw_text_ctrl(self.image_save_path_text_ctrl)
        self.image_save_path_btn = wx.Button(form_panel, label="..", size=wx.Size(30, -1))
        ConfigDialog.draw_button(self.image_save_path_btn)
        self.image_save_path_btn.Bind(wx.EVT_BUTTON, self.image_save_path_btn_click)
        form_sizer.Add(window=self.image_save_path_btn, flag=wx.ALIGN_CENTER | wx.ALL, pos=(1, 4), border=0)
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
        self.reverse_display_form()
        self.Centre()

    def on_submit(self, event):
        # 获取文本框中的值
        泵 = self.泵_text_ctrl.GetValue()
        柱温箱 = self.柱温箱_text_ctrl.GetValue()
        检测器 = self.检测器_text_ctrl.GetValue()
        default_file_name = self.default_file_name_combo_box.GetValue()
        image_save_path = self.image_save_path_text_ctrl.GetValue()
        utils.set_dictionary("泵", 泵)
        utils.set_dictionary("柱温箱", 柱温箱)
        utils.set_dictionary("检测器", 检测器)
        utils.set_dictionary("default_file_name", default_file_name)
        utils.set_dictionary("image_save_path", image_save_path)
        # 关闭对话框
        self.Close()
        dlg = wx.MessageDialog(self, "保存成功！", "提示", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()  # 显示对话框
        dlg.Destroy()  # 销毁对话框，释放资源

    def on_cancel(self, event):
        # 关闭对话框
        self.Close()

    def image_save_path_btn_click(self, event):
        dlg = wx.DirDialog(self, message="选择一个文件夹", style=wx.DD_DEFAULT_STYLE, defaultPath=self.image_save_path_text_ctrl.GetValue())
        if dlg.ShowModal() == wx.ID_OK:
            folder_path = dlg.GetPath()
            self.image_save_path_text_ctrl.SetValue(folder_path)
        dlg.Destroy()

    def reverse_display_form(self):
        text_ctrl_list = utils.traverse_elements(self, element_type=wx.TextCtrl)
        for text_ctrl in text_ctrl_list:
            text_ctrl.SetValue(utils.get_dictionary(text_ctrl.GetName()))
        combo_box_list = utils.traverse_elements(self, element_type=wx.ComboBox)
        for combo_box in combo_box_list:
            combo_box.SetValue(utils.get_dictionary(combo_box.GetName()))

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

