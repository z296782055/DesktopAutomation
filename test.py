import wx
import wx.lib.agw.aui as aui # 导入 AUI 模块

# 定义每个页面的内容面板 (与上面相同)
class PagePanel(wx.Panel):
    def __init__(self, parent, page_name, bg_color):
        super().__init__(parent)
        self.SetBackgroundColour(bg_color)

        sizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(self, label=f"这是 {page_name} 的内容。")
        text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(text, 0, wx.ALL | wx.CENTER, 50)

        if page_name == "动态页":
            self.count = 0
            self.dynamic_text = wx.StaticText(self, label=f"点击次数: {self.count}")
            btn = wx.Button(self, label="增加计数")
            sizer.Add(self.dynamic_text, 0, wx.ALL | wx.CENTER, 5)
            sizer.Add(btn, 0, wx.ALL | wx.CENTER, 10)
            btn.Bind(wx.EVT_BUTTON, self.on_increase_count)

        self.SetSizer(sizer)

    def on_increase_count(self, event):
        self.count += 1
        self.dynamic_text.SetLabel(f"点击次数: {self.count}")


class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(700, 500))

        # AuiManager 是管理 AUI 控件布局的核心，对于 AuiNotebook 并非强制，但推荐使用
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        # 创建 AuiNotebook 实例
        # 可以在这里设置样式，例如 aui.AUI_NB_TOP, aui.AUI_NB_TAB_SPLIT, aui.AUI_NB_CLOSE_BUTTON
        self.notebook = aui.AuiNotebook(self, style=aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_CLOSE_BUTTON)

        # 创建并添加页面
        page1 = PagePanel(self.notebook, "主页", wx.Colour(255, 220, 220))
        self.notebook.AddPage(page1, "主页", True) # True 表示默认选中

        page2 = PagePanel(self.notebook, "设置", wx.Colour(220, 255, 220))
        self.notebook.AddPage(page2, "设置")

        page3 = PagePanel(self.notebook, "动态页", wx.Colour(220, 220, 255))
        self.notebook.AddPage(page3, "动态页")

        # 将 AuiNotebook 添加到 AuiManager
        self._mgr.AddPane(self.notebook, aui.AuiPaneInfo().CenterPane())
        self._mgr.Update() # 更新布局

        self.Centre()
        self.Show()

        # 绑定 AuiNotebook 页面切换事件
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_aui_page_changed)
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_aui_page_close)

        # 确保在关闭 Frame 时释放 AuiManager 资源
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_aui_page_changed(self, event):
        old_sel = event.GetOldSelection()
        new_sel = event.GetSelection()
        page_text = self.notebook.GetPageText(new_sel)
        print(f"AuiNotebook 页面已切换：从索引 {old_sel} 到索引 {new_sel} ({page_text})")
        event.Skip()

    def on_aui_page_close(self, event):
        page_index = event.GetSelection()
        page_text = self.notebook.GetPageText(page_index)
        print(f"AuiNotebook 页面 '{page_text}' (索引 {page_index}) 正在关闭。")
        # 如果你想阻止页面关闭，可以调用 event.Veto()
        # if page_text == "设置":
        #     wx.MessageBox("设置页不能关闭！", "警告", wx.OK | wx.ICON_WARNING)
        #     event.Veto()
        event.Skip()

    def on_close(self, event):
        # 释放 AuiManager 资源，重要！
        self._mgr.Uninit()
        self.Destroy()
        event.Skip()

if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame(None, "AuiNotebook 分页示例")
    app.MainLoop()
