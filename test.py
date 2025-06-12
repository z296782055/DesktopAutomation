import wx
import wx.adv # 导入 wx.adv 模块
import os
import sys

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="HyperlinkCtrl 示例", size=(400, 300))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 示例：打开一个网页链接
        web_link = wx.adv.HyperlinkCtrl(panel, wx.ID_ANY,
                                        label="访问 wxPython 官网",
                                        url="https://www.wxpython.org/")
        sizer.Add(web_link, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        # 示例文件路径 (请替换为你系统中实际存在的文件或目录)
        # 你的截图显示路径是 D:\Dliktest20250608193615.pdf
        example_file_path = r"D:\Dliktest20250608193615.pdf" # 使用原始路径
        # 假设这个文件是存在的，并且关联了PDF阅读器

        # 示例：打开本地文件或目录
        # 注意：对于本地文件，url 参数需要使用 file:// 协议
        file_link = wx.adv.HyperlinkCtrl(panel, wx.ID_ANY,
                                         label=f"点击打开本地文件: {os.path.basename(example_file_path)}",
                                         url=f"file://{example_file_path}")
        # 绑定 EVT_HYPERLINK 事件来自定义行为（例如，处理错误或执行额外操作）
        file_link.Bind(wx.adv.EVT_HYPERLINK, self.OnOpenFileLink)
        sizer.Add(file_link, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        # 示例：自定义点击行为（不使用url参数，只用事件）
        custom_link = wx.adv.HyperlinkCtrl(panel, wx.ID_ANY,
                                           label="点击执行自定义操作",
                                           url="") # url 可以为空，如果只用事件
        custom_link.Bind(wx.adv.EVT_HYPERLINK, self.OnCustomLinkClick)
        sizer.Add(custom_link, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        panel.SetSizer(sizer)
        self.Center()
        self.Show()

    def OnOpenFileLink(self, event):
        """处理点击本地文件链接的事件"""
        url = event.GetURL()
        file_path = url.replace("file://", "") # 移除 file:// 前缀，获取实际路径

        print(f"尝试打开文件: {file_path}") # 这一行已经证明路径是正确的

        if not os.path.exists(file_path):
            wx.MessageBox(f"文件或目录不存在:\n{file_path}", "错误", wx.OK | wx.ICON_ERROR)
            return

        try:
            # 核心修改在这里：调用实际打开文件的函数
            self._open_path_with_system_default(file_path)
            # HyperlinkCtrl 默认会尝试打开 URL，但对于本地文件，我们最好显式控制
            # pass # 这一行是导致问题的原因，请删除或注释掉
        except Exception as e:
            wx.MessageBox(f"无法打开文件或目录:\n{file_path}\n错误: {e}", "错误", wx.OK | wx.ICON_ERROR)

    def OnCustomLinkClick(self, event):
        """处理点击自定义链接的事件"""
        wx.MessageBox("你点击了自定义链接！", "信息", wx.OK | wx.ICON_INFORMATION)

    # 辅助函数：根据操作系统打开文件
    def _open_path_with_system_default(self, path):
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin": # macOS
            # 在macOS上，wx.LaunchDefaultBrowser 也能很好地处理 file:// 协议
            wx.LaunchDefaultBrowser(f"file://{path}")
        else: # Linux
            # 在Linux上，xdg-open 是常用的命令，wx.LaunchDefaultBrowser 也适用
            wx.LaunchDefaultBrowser(f"file://{path}")


if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame()
    app.MainLoop()
