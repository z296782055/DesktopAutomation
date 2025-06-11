import wx
import wx.adv
import requests
import util.utils
from util import keyring_util
from util.keyring_util import api_client
import sqlite3 # Added import for DB setup
import atexit  # Added import for DB setup

# --- 图标资源路径 (定义为常量) ---
# 最好使用绝对路径或相对于项目根目录的路径
# 或者使用像 pkg_resources 或 importlib.resources 这样的库来管理资源
USER_ICON_PATH = "img/icon/login.png" # 替换真实路径
LOCK_ICON_PATH = "img/icon/lock.png" # 替换真实路径

class LoginDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="用户登录")
        self.parent = parent
        self.SetBackgroundColour(wx.Colour(240, 240, 240))

        # --- 在 Dialog 初始化时加载并缩放位图 ---
        TARGET_ICON_SIZE = (32, 32) # *** 定义目标图标大小 (例如 32x32) ***
        try:
            # 1. 加载原始位图
            _user_bmp_orig = wx.Bitmap(USER_ICON_PATH, wx.BITMAP_TYPE_PNG)
            _lock_bmp_orig = wx.Bitmap(LOCK_ICON_PATH, wx.BITMAP_TYPE_PNG)

            if not _user_bmp_orig.IsOk() or not _lock_bmp_orig.IsOk():
                 print(f"警告：无法加载图标文件 '{USER_ICON_PATH}' 或 '{LOCK_ICON_PATH}'。")
                 raise ValueError("无效的位图文件")

            # 2. 转换为 Image 对象进行缩放
            _user_img = _user_bmp_orig.ConvertToImage()
            _lock_img = _lock_bmp_orig.ConvertToImage()

            # 3. 缩放 Image
            _user_img.Rescale(TARGET_ICON_SIZE[0], TARGET_ICON_SIZE[1], wx.IMAGE_QUALITY_HIGH)
            _lock_img.Rescale(TARGET_ICON_SIZE[0], TARGET_ICON_SIZE[1], wx.IMAGE_QUALITY_HIGH)

            # 4. 从缩放后的 Image 创建最终的 Bitmap
            user_bmp = wx.Bitmap(_user_img)
            lock_bmp = wx.Bitmap(_lock_img)

        except (FileNotFoundError, wx.wxAssertionError, ValueError, Exception) as e:
            print(f"警告：加载或缩放图标时出错 ({e})，将使用空白图标。")
            # 创建指定大小的空白位图作为备用
            user_bmp = wx.Bitmap(TARGET_ICON_SIZE[0], TARGET_ICON_SIZE[1])
            lock_bmp = wx.Bitmap(TARGET_ICON_SIZE[0], TARGET_ICON_SIZE[1])
        # ------------------------------------

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- 表单区域 ---
        # 减小垂直间距 vgap，增加水平间距 hgap
        form_sizer = wx.GridBagSizer(vgap=10, hgap=10)

        # 创建控件
        user_icon = wx.StaticBitmap(self, bitmap=user_bmp)
        self.username_static_text = wx.StaticText(self, label="用户名:")
        self.username_text_ctrl = wx.TextCtrl(self, name="username")
        self.username_text_ctrl.SetHint(" 请输入您的账号")

        lock_icon = wx.StaticBitmap(self, bitmap=lock_bmp)
        self.password_static_text = wx.StaticText(self, label="密　码:") # 全角空格对齐
        self.password_text_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER, name="password")
        self.password_text_ctrl.SetHint(" 请输入您的密码")

        # 添加到 Sizer - 仔细设置 flags
        # 行 0: 图标(0,0), 标签(0,1), 输入框(0,2)
        form_sizer.Add(user_icon, pos=(0, 0),
                       flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5) # 图标垂直居中，左右边距
        form_sizer.Add(self.username_static_text, pos=(0, 1),
                       flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL) # 标签右对齐，垂直居中
        form_sizer.Add(self.username_text_ctrl, pos=(0, 2),
                       flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL) # 输入框水平扩展，垂直居中

        # 行 1: 图标(1,0), 标签(1,1), 输入框(1,2)
        form_sizer.Add(lock_icon, pos=(1, 0),
                       flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=5) # 图标垂直居中，左右边距
        form_sizer.Add(self.password_static_text, pos=(1, 1),
                       flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL) # 标签右对齐，垂直居中
        form_sizer.Add(self.password_text_ctrl, pos=(1, 2),
                       flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL) # 输入框水平扩展，垂直居中

        # *** 让输入框列 (第 2 列) 水平伸展 ***
        form_sizer.AddGrowableCol(2)

        # *** 将表单 Sizer 添加到主 Sizer，proportion 改为 0 ***
        # 保持 wx.EXPAND 使 form_sizer 水平填充，但 proportion=0 防止垂直拉伸
        main_sizer.Add(form_sizer, 0, wx.EXPAND | wx.ALL, 25) # proportion=0

        # --- 分隔线 ---
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        # --- 标准按钮 ---
        btn_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.login_btn = self.FindWindowById(wx.ID_OK)
        if self.login_btn:
            self.login_btn.SetLabel("登 录")
            self.Bind(wx.EVT_BUTTON, self.on_login, id=wx.ID_OK)
        cancel_btn = self.FindWindowById(wx.ID_CANCEL)
        if cancel_btn:
            cancel_btn.SetLabel("取 消")
            self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 15)

        # --- 完成布局 ---
        self.SetSizer(main_sizer)
        main_sizer.Fit(self) # Fit 决定最佳尺寸
        self.SetMinSize(self.GetSize()) # 设置最小尺寸防止缩太小
        self.Centre()

        self.password_text_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_login)
        self.username_text_ctrl.SetFocus()

    # --- 其他方法 (on_login, _on_login_complete_safe, etc.) 保持不变 ---
    # ... (省略) ...
    def on_login(self, event):
        username = self.username_text_ctrl.GetValue()
        password = self.password_text_ctrl.GetValue()

        if not username:
            self.show_message("账号不能为空", "输入错误", wx.ICON_WARNING)
            self.username_text_ctrl.SetFocus()
            return
        if not password:
            self.show_message("密码不能为空", "输入错误", wx.ICON_WARNING)
            self.password_text_ctrl.SetFocus()
            return

        if self.login_btn:
            self.login_btn.Disable()
        self._disabler = wx.WindowDisabler(self)
        self._busy_cursor = wx.BusyCursor()

        try:
            if 'api_client' in globals():
                api_client.login(username, password, self._on_login_complete_safe)
            else:
                print("错误：api_client 未定义！")
                wx.CallLater(100, self._on_login_complete_safe, False, "内部错误：API客户端丢失")
        except Exception as e:
            print(f"登录 API 调用失败: {e}")
            self._cleanup_after_login()
            self.show_message(f"登录请求异常: {e}", "错误", wx.ICON_ERROR)


    def _on_login_complete_safe(self, success, message):
        wx.CallAfter(self._on_login_complete, success, message)

    def _on_login_complete(self, success, message):
        self._cleanup_after_login()

        if success:
            print("登录成功!")
            if 'util' in globals() and hasattr(util, 'utils'):
                 util.utils.set_config("username", self.username_text_ctrl.GetValue())
            else:
                 print(f"Skipping set_config for username (util.utils not found)")

            if self.parent:
                try:
                    if hasattr(self.parent, 'init') and callable(self.parent.init):
                        self.parent.init()
                    if hasattr(self.parent, 'token_init') and callable(self.parent.token_init):
                        self.parent.token_init(success, message)
                except AttributeError as e:
                    print(f"调用父窗口方法时出错: {e}")

            self.EndModal(wx.ID_OK)
        else:
            print(f"登录失败: {message}")
            self.show_message(message, "登录失败", wx.ICON_ERROR)
            self.password_text_ctrl.SetValue("")
            self.password_text_ctrl.SetFocus()

    def _cleanup_after_login(self):
        if hasattr(self, '_disabler'): del self._disabler
        if hasattr(self, '_busy_cursor'): del self._busy_cursor
        if self.login_btn: self.login_btn.Enable()

    def show_message(self, message, caption, style=wx.ICON_INFORMATION):
        wx.MessageBox(message, caption, wx.OK | style, parent=self)

    def on_cancel(self, event):
        print("用户取消登录。")
        self.EndModal(wx.ID_CANCEL)

# --- 示例用法 (保持不变) ---
if __name__ == '__main__':
    # --- Mocking 和数据库设置 (保持不变) ---
    # ... (省略 Mocking 和 DB setup 代码) ...
    DB_NAME = 'mydatabase.db'
    conn = None
    def get_db_connection():
        global conn
        if conn is None: conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row
        return conn
    def close_db_connection():
        global conn
        if conn: conn.close(); conn = None; print("数据库连接已自动关闭。")
    def setup_database():
        db = get_db_connection(); cursor = db.cursor()
        try:
            cursor.execute('CREATE TABLE IF NOT EXISTS keyvaluepairs (key TEXT PRIMARY KEY, value TEXT)')
            db.commit(); print("表 'keyvaluepairs' 创建成功或已存在。")
        except sqlite3.Error as e: print(f"数据库设置错误: {e}")
    atexit.register(close_db_connection)

    class MockApiClient:
        def login(self,u,p,cb): print(f"模拟登录: {u}"); wx.CallLater(500,lambda: cb(True,"模拟Token") if u=="test" and p=="pass" else cb(False,"无效凭证"))
    class MockUtils:
        _cfg={};
        def set_config(self,k,v): print(f"模拟设置: {k}={v}"); MockUtils._cfg[k]=v; db=get_db_connection(); c=db.cursor(); c.execute("INSERT OR REPLACE INTO keyvaluepairs VALUES (?,?)",(k,str(v))); db.commit()
        def get_config(self,k,d=None): print(f"模拟获取: {k}"); v=d; db=get_db_connection(); c=db.cursor(); c.execute("SELECT value FROM keyvaluepairs WHERE key=?",(k,)); r=c.fetchone(); v=r['value'] if r else MockUtils._cfg.get(k,d); print(f" -> 值: {v}"); return v
    class MockKeyring: pass
    api_client=MockApiClient(); util=wx.NewIdRef(); util.utils=MockUtils(); keyring_util=MockKeyring()

    app = wx.App(False)
    setup_database()

    class DummyParentFrame(wx.Frame):
        def __init__(self):
            super().__init__(None, title="主程序窗口")
            self.token = None
            p = wx.Panel(self); s = wx.BoxSizer(wx.VERTICAL)
            b = wx.Button(p, label="显示美化登录窗口")
            b.Bind(wx.EVT_BUTTON, self.show_login_dialog)
            s.Add(b, 0, wx.ALL | wx.CENTER, 20); p.SetSizer(s)
            self.SetSize((400, 300)); self.Centre(); self.Show()
        def show_login_dialog(self, e):
            dlg = LoginDialog(self); r = dlg.ShowModal()
            if r == wx.ID_OK: print("登录 OK"); self.SetTitle(f"主程序 - 用户:{util.utils.get_config('username','?')} (Token:{self.token})")
            else: print("登录 Cancel/Close")
            dlg.Destroy()
        def init(self): print("父 Frame.init()")
        def token_init(self, s, m): print(f"父 Frame.token_init({s}, '{m}')"); self.token=m if s else None

    frame = DummyParentFrame()
    app.MainLoop()

