# 文件: logger_util.py (在队列方案基础上增加控制台输出)

import logging
import multiprocessing
import sys
import atexit
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler
from util import utils

# configure_worker_logging 函数完全不需要修改，保持原样
def configure_worker_logging(log_queue: multiprocessing.Queue):
    """
    为工作进程（主进程或子进程）配置日志，使其将日志发送到指定的队列。
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(QueueHandler(log_queue))


# 只需要修改 setup_logging 函数
def setup_logging():
    """
    为应用程序设置基于队列的日志系统。
    这个函数应该只在主进程中被调用一次。

    返回:
        multiprocessing.Queue: 创建的日志队列，需要传递给子进程。
    """
    # 1. 创建一个所有进程共享的队列 (不变)
    log_queue = multiprocessing.Queue(-1)

    # --- 核心修改在这里 ---

    # 2. 创建所有目标处理器 (Handler)
    #    我们现在需要两个：一个用于文件，一个用于控制台。

    # a) 文件处理器 (不变)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(processName)-15s (%(process)d) | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s"
    )
    file_handler = TimedRotatingFileHandler(
        './log/' + utils.get_config("default_log_file_name"),
        encoding='utf-8',
        when='D',
        interval=1,
        backupCount=7
    )
    file_handler.suffix = "%Y-%m-%d.log"
    file_handler.setFormatter(file_formatter)

    # b) 控制台处理器 (新增)
    console_formatter = logging.Formatter(
        "%(levelname)-8s | %(processName)-15s | %(message)s"
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # 3. 创建并启动日志监听器，【关键】将所有处理器都交给它管理
    # QueueListener 可以接收任意数量的处理器作为参数
    listener = QueueListener(log_queue, file_handler, console_handler) # <--- 修改点
    listener.start()

    # 4. 配置主进程，让它把日志发送到队列 (不变)
    configure_worker_logging(log_queue)

    # 5. 【关键】删除之前只为主进程添加控制台输出的代码
    # 因为现在监听器会统一处理所有进程的控制台输出，
    # 如果保留下面这行，主进程的日志会在控制台打印两次。
    # logging.getLogger().addHandler(console_handler)  <--- 删除这一行

    # 6. 配置未捕获异常处理器 (不变)
    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.exception("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_uncaught_exception

    # 7. 注册退出时停止监听器的函数 (不变)
    atexit.register(listener.stop)

    # 8. 返回日志队列 (不变)
    return log_queue
