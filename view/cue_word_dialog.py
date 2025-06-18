# ... (imports and other classes remain the same) ...
import os
import shutil
from pathlib import Path
import wx
import wx.richtext
import wx.lib.scrolledpanel as scrolled
import wx.adv
import wx._xml

import util.utils # Assuming this exists
from util import utils


# --- CollapsiblePane class remains the same ---
class CollapsiblePane(wx.Panel):
    # ... (previous CollapsiblePane code) ...
    def __init__(self, parent, id=wx.ID_ANY, label="", style=wx.BORDER_NONE, initial_state='collapsed', on_toggle_callback=None): wx.Panel.__init__(self, parent, id, style=style); self.parent = parent; self._label = label; self._collapsed = (initial_state != 'expanded'); self._on_toggle_callback = on_toggle_callback; sizer = wx.BoxSizer(wx.VERTICAL); self.toggle_button = wx.Button(self, label=self._get_button_label()); self.toggle_button.Bind(wx.EVT_BUTTON, self.on_toggle); sizer.Add(self.toggle_button, 0, wx.EXPAND | wx.BOTTOM, 2); self._content_panel = wx.Panel(self, style=wx.BORDER_NONE); self._content_panel_sizer = wx.BoxSizer(wx.VERTICAL); self._content_panel.SetSizer(self._content_panel_sizer); sizer.Add(self._content_panel, 1, wx.EXPAND | wx.ALL, 0); self._content_panel.Show(not self._collapsed); self.SetSizer(sizer)
    def GetContentPanel(self): return self._content_panel
    def GetContentSizer(self): return self._content_panel_sizer
    def _get_button_label(self): arrow = "▲" if self._collapsed else "▼"; return f"{self._label} {arrow}"
    def on_toggle(self, event): self.toggle(); self._notify()
    def toggle(self): self._collapsed = not self._collapsed; self._content_panel.Show(not self._collapsed); self.toggle_button.SetLabel(self._get_button_label()); wx.CallAfter(self.Layout); self._notify()
    def is_expanded(self): return not self._collapsed
    def expand(self):
        if self._collapsed: self.toggle();
    def collapse(self):
        if not self._collapsed: self.toggle();
    def _notify(self):
        if callable(self._on_toggle_callback): self._on_toggle_callback(self)
# --- End CollapsiblePane ---


class CueWordDialog(wx.Dialog):
    # ... (__init__ remains the same) ...
    def __init__(self, parent):
        super().__init__(parent, title="AI提示词", size=(700, 800))
        panel = wx.Panel(self, -1)
        self.main_vbox = wx.BoxSizer(wx.VERTICAL)
        # --- Sections 1, 2, 3 setup ---
        rtf_title_hbox = wx.BoxSizer(wx.HORIZONTAL); title_text = wx.StaticText(panel, label="AI提示词:"); rtf_title_hbox.Add(title_text, 0, wx.ALIGN_CENTER_VERTICAL); required_indicator = wx.StaticText(panel, label="*"); required_indicator.SetForegroundColour(wx.RED); font = required_indicator.GetFont(); font.SetWeight(wx.FONTWEIGHT_BOLD); required_indicator.SetFont(font); rtf_title_hbox.Add(required_indicator, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 2); self.main_vbox.Add(rtf_title_hbox, 0, wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, 10); self.cue_word_text_ctrl = wx.richtext.RichTextCtrl(panel, style=wx.VSCROLL | wx.HSCROLL | wx.BORDER_SIMPLE, size=(-1, 150)); self.rtf_sizer_item = self.main_vbox.Add(self.cue_word_text_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10); self.collapsible_image_pane = CollapsiblePane(panel, label="AI提示图片", initial_state='collapsed', on_toggle_callback=self.on_pane_toggled); self.pane_sizer_item = self.main_vbox.Add(self.collapsible_image_pane, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10); image_content_panel = self.collapsible_image_pane.GetContentPanel(); image_content_sizer = self.collapsible_image_pane.GetContentSizer(); self.choose_image_btn = wx.Button(image_content_panel, label="选择图片..."); self.choose_image_btn.Bind(wx.EVT_BUTTON, self.on_choose_image); image_content_sizer.Add(self.choose_image_btn, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_LEFT, 5); self.image_scroll_window = scrolled.ScrolledPanel(image_content_panel, style=wx.BORDER_SUNKEN); self.image_scroll_window.SetupScrolling(scroll_x=False, scroll_y=True); image_content_sizer.Add(self.image_scroll_window, 1, wx.EXPAND | wx.ALL, 5); self.image_display = wx.StaticBitmap(self.image_scroll_window, wx.ID_ANY, wx.Bitmap(1, 1)); button_hbox = wx.BoxSizer(wx.HORIZONTAL); self.save_btn = wx.Button(panel, label="保存"); self.save_btn.Bind(wx.EVT_BUTTON, self.on_save); button_hbox.Add(self.save_btn, 0, wx.RIGHT, 10); self.clear_btn = wx.Button(panel, label="清空"); self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear); button_hbox.Add(self.clear_btn, 0); self.main_vbox.Add(button_hbox, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10);
        # --- Final Sizer Setup ---
        panel.SetSizer(self.main_vbox); dialog_sizer = wx.BoxSizer(wx.VERTICAL); dialog_sizer.Add(panel, 1, wx.EXPAND); self.SetSizer(dialog_sizer); self.Layout();
        self._update_proportions(self.collapsible_image_pane.is_expanded()); self.Centre(); self.selected_image_path = None; self.current_image_path = None; self.init_content();


    def _update_proportions(self, is_pane_expanded):
        """Sets the sizer proportions based on the pane's state."""
        # --- Removed Show/Hide calls for self.collapsible_image_pane ---
        if is_pane_expanded:
            # Pane expanded: RTF=0 (min size), Pane=1 (takes space)
            self.rtf_sizer_item.SetProportion(0)
            self.pane_sizer_item.SetProportion(1)
            # self.collapsible_image_pane.Show() # REMOVED
        else:
            # Pane collapsed: RTF=1 (takes space), Pane=0 (min size)
            self.rtf_sizer_item.SetProportion(1)
            self.pane_sizer_item.SetProportion(0)
            # self.collapsible_image_pane.Hide() # REMOVED
        # --- End Change ---


    def on_pane_toggled(self, pane):
        """Callback function when the CollapsiblePane is toggled."""
        is_expanded = pane.is_expanded()
        # Update proportions only
        self._update_proportions(is_expanded)
        # Trigger layout update
        wx.CallAfter(self.Layout)


    # --- init_content remains the same as previous version ---
    def init_content(self):
        """Load initial content and set pane state correctly."""
        self.cue_word_text_ctrl.SetValue(utils.get_cue_word())
        img_url = utils.get_cue_img_url()
        img_url_path = Path(img_url)
        has_image = img_url_path.exists() and img_url_path.is_file()

        if has_image:
            self.current_image_path = img_url
            self.display_image(self.current_image_path)
        else:
            self.current_image_path = None
            self.display_image(None)

        def set_initial_pane_state():
            if has_image:
                self.collapsible_image_pane.expand()
            else:
                self.collapsible_image_pane.collapse()
            # Ensure proportions and layout are correct for the final state
            self._update_proportions(self.collapsible_image_pane.is_expanded())
            self.Layout()
        wx.CallAfter(set_initial_pane_state)


    # ... (display_image, on_choose_image, on_save, on_clear remain the same) ...
    def display_image(self, image_path):
        if not image_path or not Path(image_path).exists():
            self.image_display.SetBitmap(wx.Bitmap(1, 1)); self.image_display.SetSize(1, 1); self.current_image_path = None
            def finalize_clear():
                self.image_scroll_window.SetVirtualSize(1, 1); self.image_scroll_window.Scroll(0, 0); self.Layout()
            wx.CallAfter(finalize_clear); return
        try:
            dialog_width = self.GetClientSize().width; h_padding = 30; scrollbar_allowance = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X, self.image_scroll_window); available_width = max(50, dialog_width - h_padding - scrollbar_allowance)
            img = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
            if not img.IsOk(): raise ValueError("wx.Image failed to load")
            img_width, img_height = img.GetWidth(), img.GetHeight(); new_w, new_h = img_width, img_height
            if img_width > available_width: scale = available_width / img_width; new_w = available_width; new_h = max(1, int(img_height * scale)); img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
            bitmap = wx.Bitmap(img); final_w, final_h = new_w, new_h
            self.image_display.SetBitmap(bitmap); self.image_display.SetSize(final_w, final_h); self.current_image_path = image_path
            def finalize_scroll_setup():
                if self.current_image_path == image_path:
                    self.image_scroll_window.SetVirtualSize(final_w, final_h); self.image_scroll_window.Scroll(0, 0); self.Layout()
                else: print("Image path changed before finalize_scroll_setup executed.")
            wx.CallAfter(finalize_scroll_setup)
        except Exception as e:
            print(f"Error in display_image: {e}"); wx.MessageBox(f"无法加载或显示图片: {e}\n路径: {image_path}", "图片错误", wx.OK | wx.ICON_ERROR)
            self.image_display.SetBitmap(wx.Bitmap(1, 1)); self.image_display.SetSize(1, 1); self.current_image_path = None
            def finalize_error_clear():
                self.image_scroll_window.SetVirtualSize(1, 1); self.image_scroll_window.Scroll(0, 0); self.Layout()
            wx.CallAfter(finalize_error_clear)

    def on_choose_image(self, event):
        wildcard = "Image files (*.png;*.jpg;*.jpeg;*.bmp;*.gif)|*.png;*.jpg;*.jpeg;*.bmp;*.gif|All files (*.*)|*.*"
        with wx.FileDialog(self, "选择图片文件", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            pathname = fileDialog.GetPath(); self.selected_image_path = pathname; self.display_image(pathname)
            wx.CallAfter(self.collapsible_image_pane.expand)

    def on_save(self, event):
        cue_word = self.cue_word_text_ctrl.GetValue().strip()
        if not cue_word: wx.MessageBox("AI提示词不能为空！", "提示", wx.OK | wx.ICON_WARNING); return
        try:
            utils.set_cue_word(cue_word); target_img_path = utils.get_cue_img_url(); target_img_path_obj = Path(target_img_path)
            if self.selected_image_path:
                selected_path_obj = Path(self.selected_image_path)
                if selected_path_obj.exists(): shutil.copy(self.selected_image_path, target_img_path); print(f"Copied {self.selected_image_path} to {target_img_path}")
                else: wx.MessageBox(f"选择的图片文件 '{self.selected_image_path}' 不再存在，无法保存。", "保存错误", wx.OK | wx.ICON_ERROR); return
            elif self.current_image_path is None:
                 if target_img_path_obj.exists():
                    try: os.remove(target_img_path); print(f"Removed {target_img_path}")
                    except OSError as e: print(f"Error removing existing image: {e}"); wx.MessageBox(f"无法删除旧图片: {e}", "保存错误", wx.OK | wx.ICON_ERROR)
            wx.MessageBox("保存成功！", "提示", wx.OK | wx.ICON_INFORMATION); self.EndModal(wx.ID_OK)
        except Exception as e: print(f"Error saving data: {e}"); wx.MessageBox(f"保存时发生错误: {e}", "保存失败", wx.OK | wx.ICON_ERROR)

    def on_clear(self, event):
        self.cue_word_text_ctrl.SetValue(""); self.selected_image_path = None
        self.display_image(None)
        wx.CallAfter(self.collapsible_image_pane.collapse)