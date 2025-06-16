# 文件: logger_util.py (或你的日志配置文件)

import logging
import multiprocessing
import sys
import atexit
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler
from util import utils


# 新增：一个可被任何进程复用的配置函数
def configure_worker_logging(log_queue: multiprocessing.Queue):
    """
    为工作进程（主进程或子进程）配置日志，使其将日志发送到指定的队列。
    """
    # 获取根logger
    root_logger = logging.getLogger()

    # 【关键】设置日志级别，否则INFO级别的日志会被默认的WARNING级别过滤掉
    root_logger.setLevel(logging.INFO)

    # 清理掉任何可能存在的旧处理器
    root_logger.handlers.clear()

    # 添加队列处理器
    root_logger.addHandler(QueueHandler(log_queue))


# 修改：主日志设置函数
def setup_logging():
    """
    为应用程序设置基于队列的日志系统。
    这个函数应该只在主进程中被调用一次。

    返回:
        multiprocessing.Queue: 创建的日志队列，需要传递给子进程。
    """
    # 1. 创建一个所有进程共享的队列
    log_queue = multiprocessing.Queue(-1)

    # 2. 配置将由监听器使用的文件处理器
    formatter = logging.Formatter(
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
    file_handler.setFormatter(formatter)

    # 3. 创建并启动日志监听器
    listener = QueueListener(log_queue, file_handler)
    listener.start()

    # 4. 使用新的辅助函数来配置主进程本身的日志
    configure_worker_logging(log_queue)

    # (可选) 为主进程添加一个控制台输出，方便调试
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(levelname)-8s | %(message)s")
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

    # 5. 配置未捕获异常处理器
    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.exception("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_uncaught_exception

    # 6. 注册退出时停止监听器的函数
    atexit.register(listener.stop)

    # 7. 【关键】返回日志队列，以便主进程可以将其传递出去
    return log_queue
