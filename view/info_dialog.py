import wx
from wx.lib.agw import aui
from util import utils
from view.config_dialog import ConfigDialog

# 定义每个页面的内容面板
class PagePanel(wx.Panel):
    def __init__(self, parent, step, data):
        super().__init__(parent)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        form_left_panel = wx.Panel(self, size=wx.Size(4, -1))
        form_panel = wx.Panel(self, size=wx.Size(-1, -1))
        sizer.Add(form_left_panel, 0, wx.EXPAND)
        sizer.Add(form_panel, 1, wx.EXPAND)

        form_sizer = wx.GridBagSizer(vgap=5, hgap=0)

        keys_to_delete = []
        for key, value in data.items():  # 这里的 .items() 仍然是原始字典的视图，但我们只是收集要删除的键
            if isinstance(value, int):
                keys_to_delete.append(key)
        for key in keys_to_delete:  # 在迭代完后，再执行删除操作
            del data[key]

        for i,(key,value) in enumerate(data.items()):
            info = utils.get_info(step, {}).get(key)
            if info is not None:
                if " " not in key:
                    exec('self.static_text_'+key+ ' = wx.StaticText(parent=form_panel, label="' + (info if info is not None else key) + '：")')
                    exec('ConfigDialog.draw_static_text(self.static_text_'+key+')')
                    exec('form_sizer.Add(window=self.static_text_'+key+', flag=wx.ALIGN_CENTER | wx.ALL, pos=('+str((2*i)//6)+', '+str((2*i)%6)+'), border=5)')

                    exec('self.text_ctrl_'+key+' = wx.TextCtrl(form_panel, size=wx.Size(140, -1), name="'+key+'", value="'+value+'")')
                    exec('ConfigDialog.draw_text_ctrl(self.text_ctrl_'+key+')')
                    exec('form_sizer.Add(window=self.text_ctrl_'+key+', flag=wx.ALIGN_CENTER | wx.ALL, pos=('+str((2*i)//6)+', '+str((((2*i)%6)+1))+'), border=5)')
                else :
                    pass


        form_panel.SetSizer(form_sizer)
        self.SetSizer(sizer)

class InfoDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="详细信息", size=wx.Size(1000, 600))

        # AuiManager 是管理 AUI 控件布局的核心，对于 AuiNotebook 并非强制，但推荐使用
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        # 创建 AuiNotebook 实例
        # 可以在这里设置样式，例如 aui.AUI_NB_TOP, aui.AUI_NB_TAB_SPLIT, aui.AUI_NB_CLOSE_BUTTON
        self.notebook = aui.AuiNotebook(self, style=aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_CLOSE_BUTTON)

        # art_provider = self.notebook.GetArtProvider()
        # art_provider.SetMetric(aui.AUI_ART_TAB_EXTENT, 150)

        data = utils.get_data()
        for step,data in data.items():
            page = PagePanel(parent=self.notebook, step=step, data=data)  # 浅红色
            self.notebook.AddPage(page, step)

        self._mgr.AddPane(self.notebook, aui.AuiPaneInfo().CenterPane())
        self._mgr.Update()  # 更新布局
        self.Layout()
        self.Centre()
        self.Show()

        # 绑定 AuiNotebook 页面切换事件
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_aui_page_changed)
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_aui_page_close)

        def on_button_click(self, event):
            wx.MessageBox("设置页的按钮被点击了！", "信息", wx.OK | wx.ICON_INFORMATION)

    def on_aui_page_changed(self, event):
        old_sel = event.GetOldSelection()
        new_sel = event.GetSelection()
        page_text = self.notebook.GetPageText(new_sel)
        event.Skip()

    def on_aui_page_close(self, event):
        page_index = event.GetSelection()
        page_text = self.notebook.GetPageText(page_index)
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

