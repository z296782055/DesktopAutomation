import wx

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="获取子菜单文本示例")

        # 1. 创建菜单栏
        menubar = wx.MenuBar()

        # 2. 创建主菜单 (例如 "文件" 菜单)
        file_menu = wx.Menu()

        # 添加普通菜单项
        file_menu.Append(wx.ID_NEW, "&新建\tCtrl+N")
        file_menu.Append(wx.ID_OPEN, "&打开\tCtrl+O")
        file_menu.AppendSeparator()

        # 3. 创建一个子菜单 (例如 "选项" 子菜单)
        options_submenu = wx.Menu()
        options_submenu.Append(wx.ID_ANY, "选项 A")
        options_submenu.Append(wx.ID_ANY, "选项 B")

        # 4. 将子菜单添加到主菜单中，并指定其在主菜单中的显示文本
        # AppendSubMenu(submenu, text, helpString="")
        # 这里的 "&更多选项" 就是我们想要获取的子菜单的文字
        file_menu.AppendSubMenu(options_submenu, "&更多选项")

        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "退出\tAlt+F4")

        # 将主菜单添加到菜单栏，并记住它的标签
        # 这里的 "&文件" 就是顶层菜单的标签
        top_menu_label = "&文件"
        menubar.Append(file_menu, top_menu_label)
        self.SetMenuBar(menubar)

        # 绑定退出事件
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)

        # --- 获取子菜单文字的逻辑 ---
        # 直接将顶层菜单的标签传递给函数
        self.get_submenu_text_example(file_menu, top_menu_label)

        self.Centre()
        self.Show()

    def on_exit(self, event):
        self.Close()

    def get_submenu_text_example(self, parent_menu, menu_label): # 增加了 menu_label 参数
        """
        遍历父菜单，查找并打印所有子菜单的文本。
        parent_menu: 要遍历的 wx.Menu 对象
        menu_label: 这个 wx.Menu 在其父级（例如菜单栏）中显示的标签
        """
        # 直接使用传入的 menu_label 参数，避免查询 wx.MenuBar
        print(f"正在查找菜单 '{menu_label}' 中的子菜单文本...")

        # 获取菜单中的所有 wx.MenuItem 对象
        menu_items = parent_menu.GetMenuItems()

        found_submenus = False
        for item in menu_items:
            # 检查当前菜单项是否是子菜单
            if item.IsSubMenu():
                found_submenus = True
                # 获取子菜单项的标签文本
                submenu_label = item.GetItemLabel()
                print(f"  找到子菜单: '{submenu_label}'")

                # 如果需要，可以递归地进入子菜单内部查找更深层次的子菜单
                # sub_menu_obj = item.GetSubMenu()
                # self.get_submenu_text_example(sub_menu_obj, submenu_label) # 递归调用时也传递标签

        if not found_submenus:
            print("  没有找到子菜单。")

# 运行应用程序
if __name__ == '__main__':
    # 建议您打印一下 wxPython 的版本，以便了解您当前的环境
    print(f"当前 wxPython 版本: {wx.version()}")
    app = wx.App(False)
    frame = MyFrame()
    app.MainLoop()
