import wx
import wx.adv # For newer widgets if needed, though not strictly used here yet
import os # For path operations if needed

from util import utils
from util.validator_util import OsPathValidator


class ConfigDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="配置", size=wx.Size(600, 400))

        # --- Dialog 的主 Sizer ---
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- 创建主面板 (用于放置表单) ---
        # 父窗口是 self (Dialog)
        main_panel = wx.Panel(self)
        # main_panel 使用自己的 Sizer
        panel_sizer = wx.BoxSizer(wx.VERTICAL) # 或者直接用 StaticBoxSizer

        # --- Form Section ---
        # StaticBox 的父窗口是 main_panel
        form_static_box = wx.StaticBox(main_panel, label="仪器与路径设置")
        form_sizer_container = wx.StaticBoxSizer(form_static_box, wx.VERTICAL)

        # GridBagSizer for the form elements
        form_sizer = wx.GridBagSizer(vgap=10, hgap=10)

        border_size = 10

        # --- Helper function ---
        # 注意: 控件的 parent 现在是 main_panel
        def add_form_row(label_text, control, row, col=0, label_span=1, control_span=1, flags=wx.EXPAND):
            # Label 的父窗口是 main_panel
            label = wx.StaticText(main_panel, label=label_text)
            form_sizer.Add(label, pos=(row, col), span=(1, label_span),
                           flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=border_size)
            # Control (已在外部创建，父窗口应为 main_panel)
            form_sizer.Add(control, pos=(row, col + label_span), span=(1, control_span),
                           flag=flags | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=border_size)
            return label, control

        # --- Form Fields (确保 parent 是 main_panel) ---
        # 例如:
        self.泵_text_ctrl = wx.TextCtrl(main_panel, name="泵") # parent=main_panel
        add_form_row("泵：", self.泵_text_ctrl, 0, 0)

        self.default_file_name_combo_box = wx.ComboBox(main_panel, name="default_file_name", value="%Y%m%d%H%M%S",choices=["%Y%m%d%H%M%S","%Y-%m-%d-%H-%M-%S"],style=wx.CB_READONLY) # parent=main_panel
        add_form_row("文件默认名称格式：", self.default_file_name_combo_box, 0, 2)

        # ... (修改所有其他控件的 parent 为 main_panel) ...
        self.柱温箱_text_ctrl = wx.TextCtrl(main_panel, name="柱温箱")
        add_form_row("柱温箱：", self.柱温箱_text_ctrl, 1, 0)

        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.image_save_path_text_ctrl = wx.TextCtrl(main_panel, name="image_save_path", validator=OsPathValidator()) # parent=main_panel
        path_sizer.Add(self.image_save_path_text_ctrl, 1, wx.EXPAND)
        self.image_save_path_btn = wx.Button(main_panel, label="...", size=(30, -1)) # parent=main_panel
        self.image_save_path_btn.Bind(wx.EVT_BUTTON, self.on_select_image_path)
        path_sizer.Add(self.image_save_path_btn, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        path_label = wx.StaticText(main_panel, label="图片保存路径：") # parent=main_panel
        form_sizer.Add(path_label, pos=(1, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=border_size)
        form_sizer.Add(path_sizer, pos=(1, 3), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=border_size)

        self.检测器_text_ctrl = wx.TextCtrl(main_panel, name="检测器") # parent=main_panel
        add_form_row("检测器：", self.检测器_text_ctrl, 2, 0)

        self.自动进样器_text_ctrl = wx.TextCtrl(main_panel, name="自动进样器") # parent=main_panel
        add_form_row("自动进样器：", self.自动进样器_text_ctrl, 3, 0)


        form_sizer.AddGrowableCol(1, 1)
        form_sizer.AddGrowableCol(3, 1)

        form_sizer_container.Add(form_sizer, 1, wx.EXPAND | wx.ALL, border=border_size)
        # 将 form_sizer_container 添加到 panel_sizer
        panel_sizer.Add(form_sizer_container, 1, wx.EXPAND | wx.ALL, border=border_size)

        # 设置 main_panel 的 Sizer
        main_panel.SetSizer(panel_sizer)

        # --- 将 main_panel 添加到 Dialog 的主 Sizer ---
        # main_panel 本身由 dialog_sizer 管理
        dialog_sizer.Add(main_panel, 1, wx.EXPAND) # 占据大部分空间

        # --- Standard Buttons ---
        # 创建标准按钮 Sizer，按钮的 parent 是 self (Dialog)
        btn_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        ok_button = self.FindWindowById(wx.ID_OK)
        if ok_button:
            ok_button.SetLabel("确定")
            self.Bind(wx.EVT_BUTTON, self.on_submit, ok_button)
        cancel_button = self.FindWindowById(wx.ID_CANCEL)
        if cancel_button:
            cancel_button.SetLabel("取消")
        # 将按钮 Sizer 添加到 Dialog 的主 Sizer
        dialog_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, border=border_size)

        # --- 设置 Dialog 的主 Sizer ---
        self.SetSizer(dialog_sizer) # 将 dialog_sizer 设置为 Dialog 的 Sizer

        # ... (后面的代码 load_data, Fit, Centre 等保持不变) ...
        self.load_data()
        dialog_sizer.Fit(self) # 用 Dialog 的 Sizer 来 Fit Dialog
        self.Centre(wx.BOTH)

    def load_data(self):
        self.泵_text_ctrl.SetValue(utils.get_dictionary("泵"))
        self.柱温箱_text_ctrl.SetValue(utils.get_dictionary("柱温箱"))
        self.检测器_text_ctrl.SetValue(utils.get_dictionary("检测器"))
        self.自动进样器_text_ctrl.SetValue(utils.get_dictionary("自动进样器"))
        self.default_file_name_combo_box.SetValue(utils.get_dictionary("default_file_name", "%Y%m%d%H%M%S"))
        self.image_save_path_text_ctrl.SetValue(utils.get_dictionary("image_save_path"))
        # Example using TransferDataToWindow if validators were fully implemented
        # self.TransferDataToWindow()


    def save_data(self):
        utils.set_dictionary("泵", self.泵_text_ctrl.GetValue())
        utils.set_dictionary("柱温箱", self.柱温箱_text_ctrl.GetValue())
        utils.set_dictionary("检测器", self.检测器_text_ctrl.GetValue())
        utils.set_dictionary("自动进样器", self.自动进样器_text_ctrl.GetValue())
        utils.set_dictionary("default_file_name", self.default_file_name_combo_box.GetValue())
        utils.set_dictionary("image_save_path", self.image_save_path_text_ctrl.GetValue())
        return True

    def on_submit(self, event):
        try:
            if self.save_data():  # 让 save_data 返回 True/False 表示成功与否
                # 4. 关闭对话框，并返回 wx.ID_OK
                self.EndModal(wx.ID_OK)
                # 5. (可选) 在对话框关闭后显示成功提示
                wx.CallAfter(wx.MessageBox, "配置保存成功！", "成功", wx.OK | wx.ICON_INFORMATION)
            else:
                # save_data 内部逻辑可能失败
                wx.MessageBox("保存配置失败，请检查日志或重试。", "保存错误", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            wx.MessageBox(f"保存配置时发生意外错误: {e}", "错误", wx.OK | wx.ICON_ERROR)

    def on_cancel(self, event):
        # Use EndModal for dialogs, indicates cancellation
        self.EndModal(wx.ID_CANCEL)

    def on_select_image_path(self, event):
        """Handles the '...' button click to select a directory."""
        current_path = self.image_save_path_text_ctrl.GetValue()
        dlg = wx.DirDialog(self, message="选择图片保存文件夹",
                           defaultPath=current_path if os.path.isdir(current_path) else os.getcwd(), # Safer default
                           style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() == wx.ID_OK:
            folder_path = dlg.GetPath()
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