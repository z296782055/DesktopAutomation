import wx
import wx.grid as gridlib
import json
import os
from collections import OrderedDict

# --- 全局常量 ---
DATA_FILE_PATH = "step/step.json"
DEFAULTS_FILE_PATH = "data/data.json"
AUTO_TYPE_CHOICES = [
    "connect_window", "connect_child_window", "control_click", "edit_write",
    "list_select", "check", "table_fill", "tree_click", "table_click",
    "wait", "window_close", "ai_post"
]
CLICK_TYPE_CHOICES = ["click", "double_click", "right_click", "no_click", "set_focus"]
DEFAULT_JSON_DATA_STRING = """
[
    {"AI请求":[{"auto_type" : "ai_post"}]},
    {"点击“实时采集”":[
      {"auto_type" : "connect_window", "title" : "导航"},
      {"auto_type" : "control_click", "window" : "实时采集", "kwargs": [{"child_window":{"title":"实时采集", "auto_id":"btRealTimeAnalysis", "control_type":"Text"}}]}
    ]}
]
"""


class TextEditorDialog(wx.Dialog):
    def __init__(self, parent, title, value):
        super().__init__(parent, title=title, size=(600, 450), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL);
        self.text_ctrl = wx.TextCtrl(self, value=value, style=wx.TE_MULTILINE | wx.TE_DONTWRAP)
        font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL);
        self.text_ctrl.SetFont(font)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5);
        sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.EXPAND | wx.ALL, 5);
        self.SetSizer(sizer)

    def GetValue(self): return self.text_ctrl.GetValue()


class GenericJsonEditorDialog(wx.Dialog):
    def __init__(self, parent, title, data):
        super().__init__(parent, title=title, size=(700, 500), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.data = json.loads(json.dumps(data));
        self.is_dict_mode = True;
        self.is_list_passthrough_mode = False
        if isinstance(self.data, list):
            if all(isinstance(item, dict) and len(item) == 1 for item in self.data):
                self.is_list_passthrough_mode = True
                self.is_dict_mode = False
            else:
                self.is_dict_mode = False
        main_sizer = wx.BoxSizer(wx.VERTICAL);
        self.grid = gridlib.Grid(self)
        if self.is_dict_mode or self.is_list_passthrough_mode:
            self.grid.CreateGrid(0, 2);
            self.grid.SetColLabelValue(0, "键");
            self.grid.SetColLabelValue(1, "值")
            self.grid.SetColSize(0, 200);
            self.grid.SetColSize(1, 400)
        else:
            self.grid.CreateGrid(0, 1);
            self.grid.SetColLabelValue(0, "值");
            self.grid.SetColSize(0, 600)
        self.grid.SetRowLabelSize(40);
        self.populate_grid()
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL);
        add_btn = wx.Button(self, label="添加");
        del_btn = wx.Button(self, label="删除")
        btn_sizer.Add(add_btn, 0, wx.ALL, 5);
        btn_sizer.Add(del_btn, 0, wx.ALL, 5)
        dialog_btn_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5);
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        main_sizer.Add(dialog_btn_sizer, 0, wx.EXPAND | wx.ALL, 5);
        self.SetSizer(main_sizer)
        add_btn.Bind(wx.EVT_BUTTON, self.on_add);
        del_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        self.grid.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.on_cell_changed);
        self.grid.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.on_cell_dclick)
        self.grid.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.on_grid_right_click)

    def populate_grid(self):
        if self.grid.GetNumberRows() > 0: self.grid.DeleteRows(0, self.grid.GetNumberRows())
        if self.is_list_passthrough_mode:
            self.grid.AppendRows(len(self.data))
            for row, item_dict in enumerate(self.data):
                key = list(item_dict.keys())[0];
                value = item_dict[key]
                self.grid.SetCellValue(row, 0, key);
                self.grid.SetReadOnly(row, 0, True);
                self._render_value_cell(row, 1, value)
        elif self.is_dict_mode:
            self.grid.AppendRows(len(self.data))
            for row, (key, value) in enumerate(self.data.items()):
                self.grid.SetCellValue(row, 0, key);
                self._render_value_cell(row, 1, value)
        else:
            self.grid.AppendRows(len(self.data))
            for row, value in enumerate(self.data): self._render_value_cell(row, 0, value)
        self.grid.ForceRefresh()

    def _render_value_cell(self, row, col, value):
        if isinstance(value, (dict, list)):
            self.grid.SetCellValue(row, col, json.dumps(value, ensure_ascii=False));
            self.grid.SetReadOnly(row, col, True)
            self.grid.SetCellBackgroundColour(row, col, wx.Colour(230, 230, 230))
        else:
            self.grid.SetCellValue(row, col, str(value));
            self.grid.SetReadOnly(row, col, False)
            self.grid.SetCellBackgroundColour(row, col, wx.WHITE)

    def on_cell_dclick(self, event):
        row, col = event.GetRow(), event.GetCol();
        target_data, is_editable = None, False
        if self.is_list_passthrough_mode and col == 1:
            key = list(self.data[row].keys())[0];
            target_data = self.data[row][key];
            is_editable = True
        elif self.is_dict_mode and col == 1:
            key = list(self.data.keys())[row];
            target_data = self.data[key];
            is_editable = True
        elif not self.is_dict_mode and col == 0:
            target_data = self.data[row]; is_editable = True
        if is_editable and isinstance(target_data, (dict, list)):
            dlg = GenericJsonEditorDialog(self, "编辑嵌套数据", target_data)
            if dlg.ShowModal() == wx.ID_OK:
                new_value = dlg.GetValue()
                if self.is_list_passthrough_mode:
                    self.data[row][list(self.data[row].keys())[0]] = new_value
                elif self.is_dict_mode:
                    self.data[list(self.data.keys())[row]] = new_value
                else:
                    self.data[row] = new_value
                self.populate_grid()
            dlg.Destroy()
        event.Skip()

    def on_cell_changed(self, event):
        row, col = event.GetRow(), event.GetCol()
        if self.is_list_passthrough_mode:
            if col == 1: self.data[row][list(self.data[row].keys())[0]] = self.grid.GetCellValue(row, col)
        elif self.is_dict_mode:
            if col == 0:
                old_key = list(self.data.keys())[row];
                new_key = self.grid.GetCellValue(row, col)
                if new_key == old_key: return
                if not new_key or new_key in self.data:
                    wx.MessageBox(f"键 '{new_key}' 无效或已存在!", "错误", wx.OK | wx.ICON_ERROR);
                    self.grid.SetCellValue(row, col, old_key);
                    return
                self.data = dict(OrderedDict((new_key if k == old_key else k, v) for k, v in self.data.items()))
            else:
                self.data[list(self.data.keys())[row]] = self.grid.GetCellValue(row, col)
        else:
            self.data[row] = self.grid.GetCellValue(row, col)

    def on_add(self, event):
        if self.is_list_passthrough_mode:
            self.data.append({"新项目": {}})
        elif self.is_dict_mode:
            new_key = f"新键_{len(self.data)}";
            while new_key in self.data: new_key += "_"
            self.data[new_key] = "新值"
        else:
            self.data.append("新项目")
        self.populate_grid()

    def on_delete(self, event):
        row = self.grid.GetGridCursorRow();
        if row < 0: return
        if self.is_dict_mode:
            del self.data[list(self.data.keys())[row]]
        else:
            self.data.pop(row)
        self.populate_grid()

    def GetValue(self):
        return self.data

    def on_grid_right_click(self, event):
        row, col = event.GetRow(), event.GetCol();
        target_data, is_editable_col = None, False
        if (self.is_dict_mode or self.is_list_passthrough_mode) and col == 1:
            is_editable_col = True
        elif not self.is_dict_mode and col == 0:
            is_editable_col = True
        if not is_editable_col: event.Skip(); return
        self.grid.SetGridCursor(row, col)
        if self.is_list_passthrough_mode:
            target_data = self.data[row][list(self.data[row].keys())[0]]
        elif self.is_dict_mode:
            target_data = self.data[list(self.data.keys())[row]]
        else:
            target_data = self.data[row]
        if isinstance(target_data, (dict, list)):
            menu = wx.Menu();
            edit_item = menu.Append(wx.ID_ANY, "编辑...")
            self.Bind(wx.EVT_MENU, lambda evt: self.open_nested_text_editor(row, target_data), edit_item)
            self.PopupMenu(menu);
            menu.Destroy()
        event.Skip()

    def open_nested_text_editor(self, row, data_to_edit):
        current_val_str = json.dumps(data_to_edit, indent=2, ensure_ascii=False)
        dlg = TextEditorDialog(self, "编辑文本值", current_val_str)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                new_val = json.loads(dlg.GetValue())
                if self.is_list_passthrough_mode:
                    self.data[row][list(self.data[row].keys())[0]] = new_val
                elif self.is_dict_mode:
                    self.data[list(self.data.keys())[row]] = new_val
                else:
                    self.data[row] = new_val
                self.populate_grid()
            except json.JSONDecodeError as e:
                wx.MessageBox(f"无效的JSON格式！\n\n错误: {e}", "解析错误", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()


class JsonEditorFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title=f"自动化流程JSON编辑器 - [{DATA_FILE_PATH}]", size=(1200, 800))
        self.file_path = DATA_FILE_PATH
        self.data = self._load_data_from_file();
        self.defaults_data = self._load_defaults_from_file()
        self.dragged_item = None;
        self.clipboard = None
        splitter = wx.SplitterWindow(self);
        self.left_panel = wx.Panel(splitter);
        self.right_panel = wx.Panel(splitter)
        splitter.SplitVertically(self.left_panel, self.right_panel, 400);
        splitter.SetMinimumPaneSize(200)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree = wx.TreeCtrl(self.left_panel, style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HIDE_ROOT)
        add_step_btn = wx.Button(self.left_panel, label="添加步骤")
        left_sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(add_step_btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self.left_panel.SetSizer(left_sizer)
        right_sizer = wx.BoxSizer(wx.VERTICAL);
        self.prop_grid = gridlib.Grid(self.right_panel)
        self.prop_grid.CreateGrid(0, 2);
        self.prop_grid.SetColLabelValue(0, "属性");
        self.prop_grid.SetColLabelValue(1, "值")
        self.prop_grid.SetRowLabelSize(0);
        self.prop_grid.SetColSize(0, 150);
        self.prop_grid.SetColSize(1, 450)
        prop_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_prop_btn = wx.Button(self.right_panel, label="添加属性");
        self.del_prop_btn = wx.Button(self.right_panel, label="删除属性")
        prop_btn_sizer.Add(self.add_prop_btn, 0, wx.ALL, 5);
        prop_btn_sizer.Add(self.del_prop_btn, 0, wx.ALL, 5)
        right_sizer.Add(self.prop_grid, 1, wx.EXPAND | wx.ALL, 5);
        right_sizer.Add(prop_btn_sizer, 0, wx.EXPAND | wx.RIGHT | wx.BOTTOM, 5)
        self.right_panel.SetSizer(right_sizer);
        self.populate_tree()
        add_step_btn.Bind(wx.EVT_BUTTON, self.on_add_step)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_select);
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_tree_right_click)
        self.tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.on_begin_drag);
        self.tree.Bind(wx.EVT_TREE_END_DRAG, self.on_end_drag)
        self.prop_grid.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.on_prop_edit);
        self.prop_grid.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.on_prop_dclick)
        self.prop_grid.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.on_prop_right_click)
        self.add_prop_btn.Bind(wx.EVT_BUTTON, self.on_add_prop);
        self.del_prop_btn.Bind(wx.EVT_BUTTON, self.on_del_prop)
        self.update_button_states();
        self.Centre();
        self.Show()

    # --- 新增：获取当前展开节点的方法 ---
    def _get_expanded_items(self):
        expanded = set()
        root = self.tree.GetRootItem()
        if not root.IsOk(): return expanded

        item, cookie = self.tree.GetFirstChild(root)
        while item.IsOk():
            if self.tree.IsExpanded(item):
                item_data = self.tree.GetItemData(item)
                if item_data: expanded.add(item_data)
            item, cookie = self.tree.GetNextChild(root, cookie)
        return expanded

    def _load_defaults_from_file(self):
        if not os.path.exists(DEFAULTS_FILE_PATH): return {}
        try:
            with open(DEFAULTS_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f);
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_defaults_to_file(self):
        try:
            with open(DEFAULTS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.defaults_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"警告: 无法保存默认值文件: {e}")

    def _validate_and_sanitize_data(self, loaded_data):
        if not isinstance(loaded_data, list):
            print("警告: 文件中的数据不是一个列表，将重置为默认值。");
            return json.loads(DEFAULT_JSON_DATA_STRING)
        clean_data = []
        for item in loaded_data:
            if isinstance(item, dict) and len(item) == 1 and isinstance(list(item.values())[0], list):
                clean_data.append(item)
            else:
                print(f"警告: 跳过文件中的无效项目: {item}")
        return clean_data

    def _load_data_from_file(self):
        if not os.path.exists(self.file_path):
            print(f"'{self.file_path}' 未找到，将使用默认数据创建。")
            default_data = self._validate_and_sanitize_data(json.loads(DEFAULT_JSON_DATA_STRING))
            self.data = default_data;
            self._save_data_to_file();
            return default_data
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return self._validate_and_sanitize_data(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载 '{self.file_path}' 出错: {e}，将使用默认数据。")
            return self._validate_and_sanitize_data(json.loads(DEFAULT_JSON_DATA_STRING))

    def _save_data_to_file(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            wx.MessageBox(f"无法保存文件到 '{self.file_path}'！\n错误: {e}", "保存失败", wx.OK | wx.ICON_ERROR)

    # --- 改动点：commit方法现在会保存和传递树的展开状态 ---
    def _commit_changes(self):
        expanded_items = self._get_expanded_items()
        self.populate_tree(expanded_items_to_restore=expanded_items)
        self.populate_prop_list()
        self._save_data_to_file()

    def _get_default_key_from_action(self, action_dict):
        kwargs = action_dict.get('kwargs')
        if isinstance(kwargs, list) and kwargs:
            last_kwarg = kwargs[-1]
            first_key = next(iter(last_kwarg))
            if isinstance(last_kwarg, dict): return last_kwarg.get(first_key).get('auto_id')
        return None

    def populate_prop_list(self):
        if self.prop_grid.GetNumberRows() > 0: self.prop_grid.DeleteRows(0, self.prop_grid.GetNumberRows())
        if self.selected_item and self.selected_item.IsOk():
            try:
                item_data = self.tree.GetItemData(self.selected_item)
                if not (item_data and item_data[1] != -1): return
                step_idx, action_idx = item_data;
                step_title = list(self.data[step_idx].keys())[0]
                action_dict = self.data[step_idx][step_title][action_idx];
                self.prop_grid.AppendRows(len(action_dict))
                for row, (key, value) in enumerate(action_dict.items()):
                    self.prop_grid.SetCellValue(row, 0, key)
                    self.prop_grid.SetReadOnly(row, 0, key == 'auto_type')
                    self.prop_grid.SetCellBackgroundColour(row, 0,
                                                           wx.Colour(240, 240, 240) if key == 'auto_type' else wx.WHITE)
                    if isinstance(value, (dict, list)):
                        self.prop_grid.SetCellValue(row, 1, json.dumps(value, ensure_ascii=False, indent=2))
                        self.prop_grid.SetReadOnly(row, 1, True);
                        self.prop_grid.SetCellBackgroundColour(row, 1, wx.Colour(230, 230, 230))
                    else:
                        self.prop_grid.SetCellValue(row, 1, str(value));
                        self.prop_grid.SetReadOnly(row, 1, False)
                        self.prop_grid.SetCellBackgroundColour(row, 1, wx.WHITE)
                    if key == 'auto_type':
                        self.prop_grid.SetCellEditor(row, 1, gridlib.GridCellChoiceEditor(AUTO_TYPE_CHOICES, False))
                    elif key == 'click_type':
                        self.prop_grid.SetCellEditor(row, 1, gridlib.GridCellChoiceEditor(CLICK_TYPE_CHOICES, False))
                trigger_types = {'edit_write', 'list_select', 'check'}
                if action_dict.get('auto_type') in trigger_types:
                    default_key = self._get_default_key_from_action(action_dict)
                    if default_key:
                        default_value = self.defaults_data.get(step_title, {}).get(default_key, "")
                        self.prop_grid.AppendRows(1);
                        row_idx = self.prop_grid.GetNumberRows() - 1
                        self.prop_grid.SetCellValue(row_idx, 0, default_key);
                        self.prop_grid.SetReadOnly(row_idx, 0, True)
                        self.prop_grid.SetCellBackgroundColour(row_idx, 0, wx.Colour(220, 255, 220))
                        self.prop_grid.SetCellValue(row_idx, 1, default_value);
                        self.prop_grid.SetReadOnly(row_idx, 1, False)
            except (IndexError, wx.wxAssertionError, TypeError):
                pass
        self.prop_grid.ForceRefresh()

    def on_prop_edit(self, event):
        row, col = event.GetRow(), event.GetCol();
        item_data = self.tree.GetItemData(self.selected_item)
        if not item_data or col != 1: return
        step_idx, action_idx = item_data;
        step_title = list(self.data[step_idx].keys())[0]
        action_dict = self.data[step_idx][step_title][action_idx]
        key = self.prop_grid.GetCellValue(row, 0);
        new_value_str = self.prop_grid.GetCellValue(row, 1)
        if key in action_dict:
            if not self.prop_grid.IsReadOnly(row, col):
                try:
                    new_value = json.loads(new_value_str)
                except json.JSONDecodeError:
                    new_value = new_value_str
                action_dict[key] = new_value;
                self._commit_changes()
        else:
            self.defaults_data.setdefault(step_title, {})[key] = new_value_str;
            self._save_defaults_to_file()

    def on_prop_right_click(self, event):
        row, col = event.GetRow(), event.GetCol()
        if col != 1: event.Skip(); return
        self.prop_grid.SetGridCursor(row, col);
        item_data = self.tree.GetItemData(self.selected_item)
        if not item_data: return
        step_idx, action_idx = item_data;
        step_title = list(self.data[step_idx].keys())[0]
        action_dict = self.data[step_idx][step_title][action_idx];
        key = self.prop_grid.GetCellValue(row, 0)
        target_data = action_dict.get(key)
        if isinstance(target_data, (dict, list)):
            menu = wx.Menu();
            edit_item = menu.Append(wx.ID_ANY, "编辑...")
            self.Bind(wx.EVT_MENU, lambda evt: self.open_text_editor(key, target_data, step_idx, action_idx), edit_item)
            self.PopupMenu(menu);
            menu.Destroy()
        event.Skip()

    def open_text_editor(self, key, data_to_edit, step_idx, action_idx):
        current_val_str = json.dumps(data_to_edit, indent=2, ensure_ascii=False)
        dlg = TextEditorDialog(self, f"编辑属性 '{key}' 的文本值", current_val_str)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                new_val = json.loads(dlg.GetValue());
                step_title = list(self.data[step_idx].keys())[0]
                self.data[step_idx][step_title][action_idx][key] = new_val;
                self._commit_changes()
            except json.JSONDecodeError as e:
                wx.MessageBox(f"无效的JSON格式！\n\n错误: {e}", "解析错误", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

    def on_prop_dclick(self, event):
        row, col = event.GetRow(), event.GetCol()
        if col != 1: event.Skip(); return
        item_data = self.tree.GetItemData(self.selected_item);
        step_idx, action_idx = item_data
        step_title = list(self.data[step_idx].keys())[0];
        action_dict = self.data[step_idx][step_title][action_idx]
        key = self.prop_grid.GetCellValue(row, 0);
        target_data = action_dict.get(key)
        if isinstance(target_data, (dict, list)):
            dlg = GenericJsonEditorDialog(self, f"编辑属性 '{key}' 的值", target_data)
            if dlg.ShowModal() == wx.ID_OK:
                step_title = list(self.data[step_idx].keys())[0]
                self.data[step_idx][step_title][action_idx][key] = dlg.GetValue();
                self._commit_changes()
            dlg.Destroy()
        else:
            event.Skip()

    def on_add_prop(self, event):
        if not self.selected_item or not self.selected_item.IsOk(): return
        item_data = self.tree.GetItemData(self.selected_item)
        if not (item_data and item_data[1] != -1): return
        choices = ["普通属性 (文本值)", "复杂属性 (字典)", "复杂属性 (列表)"]
        dlg = wx.SingleChoiceDialog(self, "请选择要添加的属性类型:", "添加属性", choices)
        if dlg.ShowModal() != wx.ID_OK: dlg.Destroy(); return
        prop_type = dlg.GetStringSelection();
        dlg.Destroy()
        key_dlg = wx.TextEntryDialog(self, "请输入新属性的名称(Key):", "添加属性")
        if key_dlg.ShowModal() != wx.ID_OK: key_dlg.Destroy(); return
        key = key_dlg.GetValue();
        key_dlg.Destroy()
        if not key: wx.MessageBox("属性名不能为空！", "错误", wx.OK | wx.ICON_ERROR); return
        step_idx, action_idx = item_data;
        step_title = list(self.data[step_idx].keys())[0]
        action_dict = self.data[step_idx][step_title][action_idx]
        if key in action_dict: wx.MessageBox(f"属性名 '{key}' 已存在！", "错误", wx.OK | wx.ICON_ERROR); return
        if prop_type == choices[0]:
            action_dict[key] = "新值"
        elif prop_type == choices[1]:
            action_dict[key] = {}
        else:
            action_dict[key] = []
        self._commit_changes()

    def on_del_prop(self, event):
        row = self.prop_grid.GetGridCursorRow()
        if row < 0: return
        key_to_del = self.prop_grid.GetCellValue(row, 0)
        item_data = self.tree.GetItemData(self.selected_item);
        step_idx, action_idx = item_data
        step_title = list(self.data[step_idx].keys())[0];
        action_dict = self.data[step_idx][step_title][action_idx]
        if key_to_del in action_dict:
            if key_to_del == 'auto_type': wx.MessageBox("'auto_type' 是必需属性，无法删除。", "操作无效",
                                                        wx.OK | wx.ICON_WARNING); return
            del action_dict[key_to_del];
            self._commit_changes()
        else:
            self.defaults_data.setdefault(step_title, {}).pop(key_to_del, None)
            self._save_defaults_to_file();
            self.populate_prop_list()

    def on_tree_select(self, event):
        self.selected_item = self.tree.GetSelection(); self.populate_prop_list(); self.update_button_states()

    def update_button_states(self):
        item = self.tree.GetSelection();
        is_item_selected = item and item.IsOk()
        if not is_item_selected: self.add_prop_btn.Disable(); self.del_prop_btn.Disable(); return
        try:
            data = self.tree.GetItemData(item);
            is_action = data and data[1] != -1
            self.add_prop_btn.Enable(is_action);
            self.del_prop_btn.Enable(is_action and self.prop_grid.GetGridCursorRow() >= 0)
        except (wx.wxAssertionError, TypeError):
            self.add_prop_btn.Disable(); self.del_prop_btn.Disable()

    # --- 改动点：populate_tree现在会使用传入的状态来恢复展开的节点 ---
    def populate_tree(self, expanded_items_to_restore=None):
        if expanded_items_to_restore is None: expanded_items_to_restore = set()
        selected_item_data = None
        if self.tree.GetSelection():
            try:
                selected_item_data = self.tree.GetItemData(self.tree.GetSelection())
            except wx.wxAssertionError:
                selected_item_data = None
        self.tree.DeleteAllItems();
        root = self.tree.AddRoot("Root");
        new_selection_item = None
        for i, step_dict in enumerate(self.data):
            step_title = list(step_dict.keys())[0];
            step_item = self.tree.AppendItem(root, step_title)
            self.tree.SetItemData(step_item, (i, -1))
            if selected_item_data and selected_item_data == (i, -1): new_selection_item = step_item
            actions = step_dict[step_title]
            for j, action_dict in enumerate(actions):
                action_title = f"({j + 1}) {action_dict.get('auto_type', '未定义')}"
                action_item = self.tree.AppendItem(step_item, action_title)
                self.tree.SetItemData(action_item, (i, j))
                if selected_item_data and selected_item_data == (i, j): new_selection_item = action_item
            if self.tree.GetItemData(step_item) in expanded_items_to_restore:
                self.tree.Expand(step_item)
        if new_selection_item: self.tree.SelectItem(new_selection_item)

    def on_tree_right_click(self, event):
        item = event.GetItem();
        menu = wx.Menu()
        if not item.IsOk():
            if self.clipboard and self.clipboard['type'] == 'step':
                paste_step_item = menu.Append(wx.ID_ANY, "粘贴步骤")
                self.Bind(wx.EVT_MENU, self.on_paste_step, paste_step_item)
        else:
            self.tree.SelectItem(item);
            item_data = self.tree.GetItemData(item)
            if item_data is None: return
            is_step = (item_data[1] == -1)
            copy_item = menu.Append(wx.ID_ANY, "复制")
            self.Bind(wx.EVT_MENU, self.on_copy_item, copy_item)
            menu.AppendSeparator()
            if is_step:
                if self.clipboard and self.clipboard['type'] == 'action':
                    paste_action_item = menu.Append(wx.ID_ANY, "粘贴动作")
                    self.Bind(wx.EVT_MENU, self.on_paste_action, paste_action_item)
                if self.clipboard and self.clipboard['type'] == 'step':
                    paste_step_item = menu.Append(wx.ID_ANY, "粘贴步骤")
                    self.Bind(wx.EVT_MENU, self.on_paste_step, paste_step_item)
                menu.AppendSeparator()
                rename_item = menu.Append(wx.ID_ANY, "重命名步骤");
                add_action_item = menu.Append(wx.ID_ANY, "添加动作");
                del_step_item = menu.Append(wx.ID_ANY, "删除此步骤")
                self.Bind(wx.EVT_MENU, self.on_rename_step, rename_item);
                self.Bind(wx.EVT_MENU, self.on_add_action, add_action_item)
                self.Bind(wx.EVT_MENU, self.on_del_step, del_step_item)
            else:
                del_action_item = menu.Append(wx.ID_ANY, "删除此动作");
                self.Bind(wx.EVT_MENU, self.on_del_action, del_action_item)
        self.PopupMenu(menu);
        menu.Destroy()

    def on_rename_step(self, event):
        item = self.tree.GetSelection();
        if not item or not item.IsOk(): return
        item_data = self.tree.GetItemData(item)
        if not (item_data and item_data[1] == -1): return
        step_idx, _ = item_data;
        old_title = self.tree.GetItemText(item)
        dlg = wx.TextEntryDialog(self, "请输入新的步骤标题:", "重命名步骤", old_title)
        if dlg.ShowModal() == wx.ID_OK:
            new_title = dlg.GetValue()
            if new_title and new_title != old_title:
                if old_title in self.defaults_data:
                    self.defaults_data[new_title] = self.defaults_data.pop(old_title)
                    self._save_defaults_to_file()
                self.data[step_idx] = {new_title: list(self.data[step_idx].values())[0]};
                self._commit_changes()
        dlg.Destroy()

    def on_begin_drag(self, event):
        self.dragged_item = event.GetItem(); event.Allow()

    def on_end_drag(self, event):
        if not self.dragged_item: return
        drag_item, drop_target = self.dragged_item, event.GetItem();
        self.dragged_item = None
        if not drop_target.IsOk() or drag_item == drop_target: return
        parent = drop_target
        while parent.IsOk() and parent != self.tree.GetRootItem():
            if parent == drag_item: return
            parent = self.tree.GetItemParent(parent)
        try:
            drag_data, drop_data = self.tree.GetItemData(drag_item), self.tree.GetItemData(drop_target)
        except (wx.wxAssertionError, TypeError):
            return
        is_drag_step, is_drop_step = drag_data[1] == -1, drop_data[1] == -1
        if is_drag_step:
            if not is_drop_step: drop_data = self.tree.GetItemData(self.tree.GetItemParent(drop_target))
            item_to_move = self.data.pop(drag_data[0]);
            self.data.insert(drop_data[0], item_to_move)
        else:
            drag_step_idx, drag_action_idx = drag_data
            drop_step_idx, drop_action_idx = drop_data if not is_drop_step else (drop_data[0], -1)
            drag_step_title = list(self.data[drag_step_idx].keys())[0]
            action_to_move = self.data[drag_step_idx][drag_step_title].pop(drag_action_idx)
            drop_step_title = list(self.data[drop_step_idx].keys())[0]
            target_actions = self.data[drop_step_idx][drop_step_title]
            if drop_action_idx == -1:
                target_actions.append(action_to_move)
            else:
                target_actions.insert(drop_action_idx, action_to_move)
        self._commit_changes()

    def on_add_step(self, event):
        dlg = wx.TextEntryDialog(self, "请输入新步骤的标题:", "添加步骤")
        if dlg.ShowModal() == wx.ID_OK:
            title = dlg.GetValue()
            if title: self.data.append({title: []}); self._commit_changes()
        dlg.Destroy()

    def on_del_step(self, event):
        if not self.selected_item or not self.selected_item.IsOk(): return
        item_data = self.tree.GetItemData(self.selected_item)
        if item_data and item_data[1] == -1:
            step_idx, _ = item_data;
            step_name = list(self.data[step_idx].keys())[0]
            if step_name in self.defaults_data:
                del self.defaults_data[step_name];
                self._save_defaults_to_file()
            del self.data[step_idx];
            self._commit_changes()
            if self.prop_grid.GetNumberRows() > 0: self.prop_grid.DeleteRows(0, self.prop_grid.GetNumberRows())

    def on_add_action(self, event):
        if not self.selected_item or not self.selected_item.IsOk(): return
        item_data = self.tree.GetItemData(self.selected_item)
        if item_data and item_data[1] == -1:
            step_title = list(self.data[item_data[0]].keys())[0]
            self.data[item_data[0]][step_title].append({"auto_type": AUTO_TYPE_CHOICES[0]})
            self._commit_changes()

    def on_del_action(self, event):
        if not self.selected_item or not self.selected_item.IsOk(): return
        item_data = self.tree.GetItemData(self.selected_item)
        if item_data and item_data[1] != -1:
            step_idx, action_idx = item_data;
            step_title = list(self.data[step_idx].keys())[0]
            action_dict = self.data[step_idx][step_title][action_idx]
            default_key = self._get_default_key_from_action(action_dict)
            if default_key and step_title in self.defaults_data:
                self.defaults_data[step_title].pop(default_key, None)
                if not self.defaults_data[step_title]: del self.defaults_data[step_title]
                self._save_defaults_to_file()
            del self.data[step_idx][step_title][action_idx];
            self._commit_changes()
            if self.prop_grid.GetNumberRows() > 0: self.prop_grid.DeleteRows(0, self.prop_grid.GetNumberRows())

    def on_copy_item(self, event):
        if not self.selected_item or not self.selected_item.IsOk(): return
        item_data = self.tree.GetItemData(self.selected_item)
        is_step = item_data[1] == -1
        if is_step:
            step_idx = item_data[0]
            copied_data = json.loads(json.dumps(self.data[step_idx]))
            self.clipboard = {'type': 'step', 'data': copied_data}
        else:
            step_idx, action_idx = item_data
            step_title = list(self.data[step_idx].keys())[0]
            copied_data = json.loads(json.dumps(self.data[step_idx][step_title][action_idx]))
            self.clipboard = {'type': 'action', 'data': copied_data}
        wx.LogMessage(f"已复制: {self.clipboard['type']}")

    def on_paste_step(self, event):
        if not self.clipboard or self.clipboard['type'] != 'step': return
        self.data.append(self.clipboard['data'])
        self._commit_changes()

    def on_paste_action(self, event):
        if not self.clipboard or self.clipboard['type'] != 'action': return
        if not self.selected_item or not self.selected_item.IsOk(): return
        item_data = self.tree.GetItemData(self.selected_item)
        is_step = item_data[1] == -1
        if not is_step:
            item_data = self.tree.GetItemData(self.tree.GetItemParent(self.selected_item))
        step_idx = item_data[0]
        step_title = list(self.data[step_idx].keys())[0]
        self.data[step_idx][step_title].append(self.clipboard['data'])
        self._commit_changes()


if __name__ == '__main__':
    app = wx.App(False)
    frame = JsonEditorFrame()
    app.MainLoop()
