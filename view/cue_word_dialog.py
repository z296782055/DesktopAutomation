import os
import shutil
from pathlib import Path
import wx._xml
import wx
import wx.richtext

import util.utils
from util import utils, keyring_util
from util.keyring_util import api_client
from view.config_dialog import ConfigDialog

class CueWordDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="AI提示词", size=(700, 750))

        panel = wx.Panel(self)
        main_vbox = wx.BoxSizer(wx.VERTICAL)  # 主垂直布局器
        # --- 1. 富文本框部分 ---
        # 标题和必填标识的水平布局器
        rtf_title_hbox = wx.BoxSizer(wx.HORIZONTAL)

        # 富文本框标题
        title_text = wx.StaticText(panel, label="AI提示词:")
        rtf_title_hbox.Add(title_text, 0, wx.ALIGN_CENTER_VERTICAL)

        # 必填标识 (红色星号)
        required_indicator = wx.StaticText(panel, label="*")
        required_indicator.SetForegroundColour(wx.RED)  # 设置为红色
        # 可以选择加粗或放大字体以更醒目
        font = required_indicator.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        # font.SetPointSize(font.GetPointSize() + 1) # 可选：稍微增大字体
        required_indicator.SetFont(font)
        rtf_title_hbox.Add(required_indicator, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 2)  # 左侧留2像素间距

        # 将标题和标识的水平布局器添加到主垂直布局器
        main_vbox.Add(rtf_title_hbox, 0, wx.LEFT | wx.TOP, 10)
        # --- 1. 富文本框部分 ---
        # 标题
        # 富文本框
        self.cue_word_text_ctrl = wx.richtext.RichTextCtrl(panel, style=wx.VSCROLL | wx.HSCROLL | wx.NO_BORDER)
        main_vbox.Add(self.cue_word_text_ctrl, 1, wx.EXPAND | wx.ALL, 10)  # 比例1，允许扩展

        # --- 2. 图片操作部分 ---
        # 标题
        # main_vbox.Add(wx.StaticText(panel, label="AI提示图片:"), 0, wx.LEFT | wx.TOP, 10)

        # 按钮和路径显示使用水平布局器
        image_ops_hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.choose_image_btn = wx.Button(panel, label="AI提示图片")
        self.choose_image_btn.Bind(wx.EVT_BUTTON, self.on_choose_image)
        image_ops_hbox.Add(self.choose_image_btn, 0, wx.RIGHT, 5)  # 按钮右侧留白
        main_vbox.Add(image_ops_hbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # --- 3. 图片显示区域 ---
        # 初始时显示一个空白的位图，避免未加载图片时的错误
        self.image_display = wx.StaticBitmap(panel, wx.ID_ANY, wx.Bitmap(1, 1))
        main_vbox.Add(self.image_display, 2, wx.EXPAND | wx.ALL, 10)  # 比例2，比富文本框占用更多空间

        # --- 4. 保存和清空按钮 (在最下方水平居中) ---
        button_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.save_btn = wx.Button(panel, label="保存")
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        button_hbox.Add(self.save_btn, 0, wx.RIGHT, 10)  # 在保存按钮右侧添加10像素间距

        self.clear_btn = wx.Button(panel, label="清空")
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)  # 绑定清空事件
        button_hbox.Add(self.clear_btn, 0)

        main_vbox.Add(button_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)  # 将水平Sizer添加到主Sizer

        panel.SetSizer(main_vbox)
        self.Layout()  # 确保布局生效
        self.Centre()  # 窗口居中
        self.Show()
        self.init()
        self.selected_image_path = None  # 用于存储选中的图片路径

    def init(self):
        self.cue_word_text_ctrl.SetValue(utils.get_cue_word())
        img_url = Path(utils.get_cue_img_url())
        if img_url.exists():
            self.display_image(utils.get_cue_img_url())

    def on_choose_image(self, event):
        """
        处理选择图片按钮点击事件
        """
        # 定义文件类型过滤器
        wildcard = "Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp|" \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="选择图片文件",
            defaultDir=os.getcwd(),  # 默认打开当前工作目录
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST  # 打开模式，且文件必须存在
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.selected_image_path = dlg.GetPath()
            self.display_image(self.selected_image_path)
        dlg.Destroy()

    def display_image(self, image_path):
        """
        在 StaticBitmap 中显示图片：
        - 如果图片小于分配空间，按原始尺寸居中显示。
        - 如果图片大于分配空间，按比例缩小居中显示。
        """
        if not image_path:
            self.image_display.SetBitmap(wx.Bitmap(1, 1)) # 清空显示
            self.selected_image_path = None
            self.Layout()
            return
        try:
            img = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
            # 获取 StaticBitmap 的当前尺寸
            display_width, display_height = self.image_display.GetSize()
            if display_width <= 1 or display_height <= 1:
                # 初始布局时可能获取不到正确尺寸，给一个合理的默认值
                # 这里的默认值应该与Sizer分配给StaticBitmap的大小相近
                display_width, display_height = self.GetSize().width - 40, self.GetSize().height // 2 - 100
                if display_width <= 0: display_width = 680
                if display_height <= 0: display_height = 450

            img_width, img_height = img.GetWidth(), img.GetHeight()

            # 计算缩放后的尺寸
            new_w, new_h = img_width, img_height # 默认不缩放

            # 只有当图片尺寸大于显示区域时才进行缩放
            if img_width > display_width or img_height > display_height:
                scale_w = display_width / img_width
                scale_h = display_height / img_height
                scale = min(scale_w, scale_h) # 取较小比例，确保图片能完全放入

                new_w = int(img_width * scale)
                new_h = int(img_height * scale)

            # 缩放图片（如果需要）
            if new_w != img_width or new_h != img_height:
                scaled_img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
            else:
                scaled_img = img # 不需要缩放，直接使用原始图片

            # 创建一个新的位图，其大小与 StaticBitmap 的显示区域相同
            final_bitmap = wx.Bitmap(display_width, display_height)
            dc = wx.MemoryDC(final_bitmap)

            # 清除背景
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()

            # 计算绘制位置，使缩放后的图片在画布上居中
            x_offset = (display_width - new_w) // 2
            y_offset = (display_height - new_h) // 2

            # 将缩放后的图片绘制到中心位置
            dc.DrawBitmap(wx.Bitmap(scaled_img), x_offset, y_offset, True)

            # 释放设备上下文
            del dc
            # 将绘制好的位图设置给 StaticBitmap
            self.image_display.SetBitmap(final_bitmap)
            self.Layout()
        except Exception as e:
            wx.MessageBox(f"无法加载图片: {e}\n请确保文件是有效的图片格式。", "错误", wx.OK | wx.ICON_ERROR)
            self.image_display.SetBitmap(wx.Bitmap(1, 1))
            self.selected_image_path = None
            def init(self):
                self.cue_word_text_ctrl.SetValue(utils.get_cue_word())

    def on_save(self, event):
        if not self.cue_word_text_ctrl.GetValue():
            dlg = wx.MessageDialog(self, "AI提示词不能为空！", "提示", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()  # 显示对话框
            dlg.Destroy()  # 销毁对话框，释放资源
            return
        util.utils.set_cue_word(self.cue_word_text_ctrl.GetValue())
        if self.selected_image_path:
            shutil.copy(self.selected_image_path, utils.get_cue_img_url())
        else:
            if Path(utils.get_cue_img_url()).exists():
                os.remove(utils.get_cue_img_url())
        self.Close()
        dlg = wx.MessageDialog(self, "保存成功！", "提示", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()  # 显示对话框
        dlg.Destroy()  # 销毁对话框，释放资源

    def on_clear(self, event):
        self.cue_word_text_ctrl.SetValue("")
        self.selected_image_path = None
        self.display_image(image_path=None)

    def on_cancel(self, event):
        # 关闭对话框
        self.Close()

