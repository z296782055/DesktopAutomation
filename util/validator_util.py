import re
import wx

class NumberValidator(wx.Validator):
    def __init__(self):
        super().__init__()
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

    def Clone(self):
        return NumberValidator()

    def Validate(self, win):
        text_ctrl = win.GetWindow()
        value = text_ctrl.GetValue()
        pattern = r'^\d+(\.\d+)?$'
        if value == "" or re.match(pattern, value):
            return True
        else:
            return False

    def TransferFromWindow(self):
        # 当从文本框获取值时，不做任何处理，因为我们已经在Validate中处理了所有事情
        return True

    def TransferToWindow(self):
        # 当设置文本框的值时，不做任何处理，因为我们不希望在用户输入过程中修改值
        return True

    def on_char(self, event):
        text_ctrl = self.GetWindow()
        value = text_ctrl.GetValue()
        key = event.GetKeyCode()
        if (chr(key).isdigit() and value!=0)  or key in (wx.WXK_BACK, wx.WXK_DELETE) or (""!=value and "." not in value and key == wx.FONTENCODING_UNICODE):
            event.Skip()
        else:
            wx.Bell()  # 无效输入时响铃提示

    def on_kill_focus(self, event):
        if self.Validate(self):
            event.Skip()
        else:
            text_ctrl = self.GetWindow()
            text_ctrl.SetValue("")
            wx.MessageBox("输入必须为数字！", "错误", wx.OK | wx.ICON_ERROR)
            event.Skip()

class OsPathValidator(wx.Validator):
    def __init__(self):
        super().__init__()
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

    def Clone(self):
        return OsPathValidator()

    def Validate(self, win):
        text_ctrl = win.GetWindow()
        value = text_ctrl.GetValue()
        pattern = r'^(?:(?:[a-zA-Z]:|\\.{1,2})?[\\/](?:[^\\?/*|<>:\"]+[\\/])*)(?:(?:[^\\?/*|<>:\"]+?)(?:\\.[^.\\?/*|<>:\"]+)?)?$'
        if value == "" or re.match(pattern, value):
            return True
        else:
            return False

    def TransferFromWindow(self):
        # 当从文本框获取值时，不做任何处理，因为我们已经在Validate中处理了所有事情
        return True

    def TransferToWindow(self):
        # 当设置文本框的值时，不做任何处理，因为我们不希望在用户输入过程中修改值
        return True

    def on_kill_focus(self, event):
        if self.Validate(self):
            event.Skip()
        else:
            text_ctrl = self.GetWindow()
            text_ctrl.SetValue("")
            wx.MessageBox("输入必须正确的文件夹路径！", "错误", wx.OK | wx.ICON_ERROR)
            event.Skip()

