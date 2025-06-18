
class ThreadException(Exception):
    def __init__(self, message):
        super().__init__(message)

class ViewException(Exception):
    def __init__(self, message):
        super().__init__(message)

class ProcessException(Exception):
    def __init__(self, message):
        super().__init__(message)