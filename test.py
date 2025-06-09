import wx
import wx.richtext
import os
import json

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(700, 750))

        panel = wx.Panel(self)
        main_vbox = wx.BoxSizer(wx.VERTICAL)

        # --- 1. 富文本框部分 ---
        # 标题和必填标识的水平布局器
        rtf_title_hbox = wx.BoxSizer(wx.HORIZONTAL)

        # 富文本框标题
        title_text = wx.StaticText(panel, label="富文本内容:")
        rtf_title_hbox.Add(title_text, 0, wx.ALIGN_CENTER_VERTICAL)

        # 必填标识 (红色星号)
        required_indicator = wx.StaticText(panel, label="*")
        required_indicator.SetForegroundColour(wx.RED) # 设置为红色
        # 可以选择加粗或放大字体以更醒目
        font = required_indicator.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        # font.SetPointSize(font.GetPointSize() + 1) # 可选：稍微增大字体
        required_indicator.SetFont(font)
        rtf_title_hbox.Add(required_indicator, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 2) # 左侧留2像素间距

        # 将标题和标识的水平布局器添加到主垂直布局器
        main_vbox.Add(rtf_title_hbox, 0, wx.LEFT | wx.TOP, 10)

        # 富文本框
        self.rtc = wx.richtext.RichTextCtrl(panel, style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER)
        self.rtc.WriteText("在这里输入或编辑富文本内容。\n")
        self.rtc.BeginBold()
        self.rtc.WriteText("你可以尝试修改文字格式，比如加粗。\n")
        self.rtc.EndBold()
        self.rtc.BeginTextColour(wx.BLUE)
        self.rtc.WriteText("或者改变颜色。\n")
        self.rtc.EndTextColour()
        main_vbox.Add(self.rtc, 1, wx.EXPAND | wx.ALL, 10)

        # --- 2. 图片操作部分 ---
        main_vbox.Add(wx.StaticText(panel, label="图片操作:"), 0, wx.LEFT | wx.TOP, 10)
        image_ops_hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.choose_image_btn = wx.Button(panel, label="选择图片")
        self.choose_image_btn.Bind(wx.EVT_BUTTON, self.on_choose_image)
        image_ops_hbox.Add(self.choose_image_btn, 0, wx.RIGHT, 5)

        # 注意：如果你的wxPython版本过低，不支持TE_ELLIPSIZE_START，请删除此样式
        # 例如：style=wx.TE_READONLY
        self.image_path_text = wx.TextCtrl(panel, style=wx.TE_READONLY)
        image_ops_hbox.Add(self.image_path_text, 1, wx.EXPAND)

        main_vbox.Add(image_ops_hbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # --- 3. 图片显示区域 ---
        self.image_display = wx.StaticBitmap(panel, wx.ID_ANY, wx.Bitmap(1, 1))
        main_vbox.Add(self.image_display, 2, wx.EXPAND | wx.ALL, 10)

        # --- 4. 保存按钮 (在最下方水平居中) ---
        self.save_btn = wx.Button(panel, label="保存内容")
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_content)
        main_vbox.Add(self.save_btn, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)

        panel.SetSizer(main_vbox)
        self.Layout()
        self.Centre()
        self.Show()

        self.selected_image_path = None
        self.Bind(wx.EVT_SIZE, self.on_resize)

    def on_resize(self, event):
        if self.selected_image_path:
            self.display_image(self.selected_image_path)
        event.Skip()

    def on_choose_image(self, event):
        wildcard = "Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp|" \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="选择图片文件",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.selected_image_path = dlg.GetPath()
            self.image_path_text.SetValue(self.selected_image_path)
            self.display_image(self.selected_image_path)
        dlg.Destroy()

    def display_image(self, image_path):
        if not image_path:
            self.image_display.SetBitmap(wx.Bitmap(1, 1))
            self.image_path_text.SetValue("")
            self.selected_image_path = None
            self.Layout()
            return

        try:
            img = wx.Image(image_path, wx.BITMAP_TYPE_ANY)

            display_width, display_height = self.image_display.GetSize()
            if display_width <= 1 or display_height <= 1:
                display_width, display_height = self.GetSize().width - 40, self.GetSize().height // 2 - 100
                if display_width <= 0: display_width = 680
                if display_height <= 0: display_height = 450

            img_width, img_height = img.GetWidth(), img.GetHeight()

            new_w, new_h = img_width, img_height

            if img_width > display_width or img_height > display_height:
                scale_w = display_width / img_width
                scale_h = display_height / img_height
                scale = min(scale_w, scale_h)

                new_w = int(img_width * scale)
                new_h = int(img_height * scale)

            if new_w != img_width or new_h != img_height:
                scaled_img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
            else:
                scaled_img = img

            final_bitmap = wx.Bitmap(display_width, display_height)
            dc = wx.MemoryDC(final_bitmap)

            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()

            x_offset = (display_width - new_w) // 2
            y_offset = (display_height - new_h) // 2

            dc.DrawBitmap(wx.Bitmap(scaled_img), x_offset, y_offset, True)

            del dc

            self.image_display.SetBitmap(final_bitmap)
            self.Layout()

        except Exception as e:
            wx.MessageBox(f"无法加载图片: {e}\n请确保文件是有效的图片格式。", "错误", wx.OK | wx.ICON_ERROR)
            self.image_display.SetBitmap(wx.Bitmap(1, 1))
            self.image_path_text.SetValue("")
            self.selected_image_path = None

    def on_save_content(self, event):
        wildcard = "Rich Text Format (*.rtf)|*.rtf|" \
                   "HTML files (*.html)|*.html|" \
                   "Plain text files (*.txt)|*.txt"
        dlg = wx.FileDialog(
            self, message="保存文件",
            defaultDir=os.getcwd(),
            defaultFile="my_document.rtf",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )

        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
            file_ext = os.path.splitext(file_path)[1].lower()

            save_type = wx.richtext.RICHTEXT_TYPE_RTF
            if file_ext == '.html':
                save_type = wx.richtext.RICHTEXT_TYPE_HTML
            elif file_ext == '.txt':
                save_type = wx.richtext.RICHTEXT_TYPE_TEXT

            try:
                self.rtc.SaveFile(file_path, save_type)

                img_path_file = file_path + ".imgpath"
                data_to_save = {"image_path": self.selected_image_path}
                with open(img_path_file, 'w') as f:
                    json.dump(data_to_save, f)

                wx.MessageBox("内容和图片路径已成功保存！", "保存成功", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"保存失败: {e}", "保存错误", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame(None, "wxPython 综合界面示例 (必填标识)")
    app.MainLoop()
