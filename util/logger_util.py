import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from util import utils

# logging.basicConfig(filename='log/app.log', encoding='utf-8', level=logging.ERROR)

class MessageLogger:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        # 设置TimedRotatingFileHandler处理器，将日志按照日期切分
        handler = TimedRotatingFileHandler('./log/'+utils.get_config("default_log_file_name"), encoding='utf-8', when='D', interval=1, backupCount=7)
        handler.suffix = "%Y-%m-%d.log"
        # 设置日志格式
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        # 绑定处理器到logger
        self.logger.addHandler(handler)
    def log(self, message):
        print(message)
        self.logger.debug(message)

logger = MessageLogger()

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)  # 保留 KeyboardInterrupt 的默认行为
        return
    logging.exception("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))  # 记录异常信息，包括堆栈跟踪
    sys.__excepthook__(exc_type, exc_value, exc_traceback)  # 调用默认异常处理，输出到控制台
sys.excepthook = handle_uncaught_exception