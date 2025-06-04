import wx
import os

class MyDirDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="选择目录", size=(400, 200),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        panel = wx.Panel(self) # <-- 这个 panel 是 main_sizer 的关联窗口
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.path_label = wx.StaticText(panel, label="当前未选择任何目录。")
        main_sizer.Add(self.path_label, 0, wx.ALL | wx.EXPAND, 10)

        select_button = wx.Button(panel, label="选择目录...")
        select_button.Bind(wx.EVT_BUTTON, self.on_select_directory)
        main_sizer.Add(select_button, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        # --- 核心修改在这里 ---
        # 1. 创建一个标准的对话框按钮 Sizer
        btn_sizer = wx.StdDialogButtonSizer()

        # 2. 手动创建 OK 和 Cancel 按钮，并指定它们的父窗口为 'panel'
        ok_button = wx.Button(panel, wx.ID_OK, "确定") # 父窗口是 panel
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "取消") # 父窗口是 panel

        # 3. 将这些按钮添加到 btn_sizer
        btn_sizer.AddButton(ok_button)
        btn_sizer.AddButton(cancel_button)

        # 4. 调用 Realize() 来布局按钮
        btn_sizer.Realize()
        # --- 核心修改结束 ---

        # 绑定按钮事件 (注意：这里绑定的是按钮的 ID，而不是按钮对象本身)
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(main_sizer) # <-- main_sizer 与 panel 关联
        main_sizer.Fit(self)
        self.Centre()

        self.selected_path = ""

    # def on_select_directory(self, event):
    #     """
    #     点击“选择目录”按钮时触发。
    #     打开 wx.DirDialog 让用户选择目录。
    #     """
    #     with wx.DirDialog(self, "请选择一个目录",
    #                       defaultPath=self.selected_path if self.selected_path else os.getcwd(),
    #                       style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dir_dialog:
    #
    #         if dir_dialog.ShowModal() == wx.ID_OK:
    #             self.selected_path = dir_dialog.GetPath()
    #             self.path_label.SetLabel(f"已选择目录: {self.selected_path}")
    #         else:
    #             print("用户取消了目录选择。")

    def on_select_directory(self, event):
        dlg = wx.DirDialog(self, "选择一个文件夹", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            folder_path = dlg.GetPath()
        print("选择的文件夹是:", folder_path)
        dlg.Destroy()

    def on_ok(self, event):
        """
        点击 OK 按钮时触发。
        设置对话框的返回值并关闭对话框。
        """
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        """
        点击 Cancel 按钮时触发。
        设置对话框的返回值并关闭对话框。
        """
        self.EndModal(wx.ID_CANCEL)

# --- 主应用程序框架 (保持不变) ---
class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(300, 150))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        open_dialog_button = wx.Button(panel, label="打开目录选择对话框")
        open_dialog_button.Bind(wx.EVT_BUTTON, self.on_open_dialog)
        sizer.Add(open_dialog_button, 0, wx.ALL | wx.CENTER, 20)

        self.selected_dir_text = wx.StaticText(panel, label="未从对话框获取目录。")
        sizer.Add(self.selected_dir_text, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(sizer)
        self.Layout()
        self.Centre()
        self.Show()

    def on_open_dialog(self, event):
        with MyDirDialog(self) as dialog:
            result = dialog.ShowModal()

            if result == wx.ID_OK:
                selected_path = dialog.selected_path
                if selected_path:
                    self.selected_dir_text.SetLabel(f"从对话框获取的目录: {selected_path}")
                    print(f"用户选择了目录: {selected_path}")
                else:
                    self.selected_dir_text.SetLabel("对话框返回OK，但未选择目录。")
                    print("对话框返回OK，但未选择目录。")
            else:
                self.selected_dir_text.SetLabel("对话框被取消。")
                print("对话框被取消。")

# --- 运行应用程序 (保持不变) ---
if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame(None, "主窗口")
    app.MainLoop()
