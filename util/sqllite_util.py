import sqlite3
import traceback

DB_FILE = 'my_database.db'

def setup_database():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS keyvaluepairs (key TEXT PRIMARY KEY,value INTEGER  NOT NULL)")
            print("表 'keyvaluepairs' 创建成功。")
            cursor.execute("INSERT OR IGNORE INTO keyvaluepairs (key, value) VALUES (?, ?)", ('index', 0))
            cursor.execute("INSERT OR IGNORE INTO keyvaluepairs (key, value) VALUES (?, ?)", ('step', 1))
            cursor.execute("INSERT OR IGNORE INTO keyvaluepairs (key, value) VALUES (?, ?)", ('flag', 1))
            cursor.execute("INSERT OR IGNORE INTO keyvaluepairs (key, value) VALUES (?, ?)", ('event_status', 0))
            cursor.execute("INSERT OR IGNORE INTO keyvaluepairs (key, value) VALUES (?, ?)", ('thread_status', 0))

    except sqlite3.Error as e:
        print(f"数据库操作发生错误: {e}")
        # 在 with 语句中，如果发生异常，conn 会自动回滚
    print("数据库连接已自动关闭。")

def update(key, value):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE keyvaluepairs SET value = ? WHERE key = ?", (value, key))
            conn.commit()
    except sqlite3.Error as e:
        print(f"更新{key}失败: {e}")
        raise e

def get(key):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row # 设置行工厂，以便按列名访问
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM keyvaluepairs where key = ?", (key,))
            value_row = cursor.fetchone()
            if value_row:
                actual_value = value_row['value']
                print(f"获取到的'{key}': {actual_value}")
                return actual_value  # 返回的是实际的值（例如整数、字符串等），而不是整个 row 对象
            else:
                print(f"键 '{key}' 未找到。")
    except sqlite3.Error as e:
        print(f"获取{key}失败: {e}")
        raise e

setup_database()