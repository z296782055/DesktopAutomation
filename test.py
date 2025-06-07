import wx
import math  # 导入 math 模块，用于处理可能存在的非数字数据（虽然这里都是字符串）


class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(600, 400))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 你的数据
        self.data = {
            "时间(min) row0": "0",
            "流速(mL/min) row0": "1.0",
            "%A row0": "5",
            "时间(min) row1": "2",
            "流速(mL/min) row1": "1.0",
            "%A row1": "5",
            "时间(min) row2": "10",
            "流速(mL/min) row2": "1.0",
            "%A row2": "30",
            "时间(min) row3": "20",
            "流速(mL/min) row3": "1.0",
            "%A row3": "55",
            "时间(min) row4": "23",
            "流速(mL/min) row4": "1.0",
            "%A row4": "95",
            "时间(min) row5": "25",
            "流速(mL/min) row5": "1.0",
            "%A row5": "95",
            "时间(min) row6": "26",
            "流速(mL/min) row6": "1.0",
            "%A row6": "5",
            "时间(min) row7": "31",
            "流速(mL/min) row7": "1.0",
            "%A row7": "5"
        }

        # 1. 确定列头和最大行数
        self.column_headers = ["时间(min)", "流速(mL/min)", "%A"]
        max_row_index = -1
        for key in self.data.keys():
            if "row" in key:
                try:
                    row_num_str = key.split("row")[-1]
                    max_row_index = max(max_row_index, int(row_num_str))
                except ValueError:
                    # 如果键不符合 "key rowN" 格式，忽略
                    continue
        self.num_rows = max_row_index + 1 if max_row_index >= 0 else 0

        # 2. 准备 ListCtrl
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)

        # 3. 插入列头
        for i, header in enumerate(self.column_headers):
            self.list_ctrl.InsertColumn(i, header)
            # 设置列宽，这里使用自动调整宽度以适应列头
            self.list_ctrl.SetColumnWidth(i, wx.LIST_AUTOSIZE_USEHEADER)

        # 4. 填充数据
        for row_idx in range(self.num_rows):
            # 插入第一列的数据，并获取该行的索引
            # list_ctrl.InsertItem(index, text)
            # index 是插入行的位置，text 是第一列的文本
            time_key = f"时间(min) row{row_idx}"
            time_value = self.data.get(time_key, "")  # 使用 .get() 避免 KeyError
            item_index = self.list_ctrl.InsertItem(row_idx, time_value)

            # 填充剩余列的数据
            # list_ctrl.SetItem(item_index, col_idx, text)
            # item_index 是行的索引，col_idx 是列的索引（从0开始），text 是要设置的文本
            for col_idx, header in enumerate(self.column_headers):
                if col_idx == 0:  # 第一列已经在 InsertItem 时设置了
                    continue

                data_key = f"{header} row{row_idx}"
                data_value = self.data.get(data_key, "")
                self.list_ctrl.SetItem(item_index, col_idx, data_value)

        # 5. 再次调整列宽以适应内容（可选，但通常能让表格更好看）
        for i in range(len(self.column_headers)):
            self.list_ctrl.SetColumnWidth(i, wx.LIST_AUTOSIZE)

        vbox.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)  # 1 表示 ListCtrl 占据所有可用空间

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "数据表格")
        self.SetTopWindow(frame)
        return True


if __name__ == '__main__':
    app = MyApp()
    app.MainLoop()
