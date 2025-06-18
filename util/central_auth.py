import logging
import multiprocessing
import threading
import queue
import atexit
import uuid
import time
import requests
import keyring
import hashlib
import wx
from util import utils
from util.exception_util import ViewException
from util.logger_util import configure_worker_logging

# --- 配置 ---
AUTH_SERVER_URL = utils.get_config("server_url")
SERVICE_ID = "DesktopAutomation"

# --- 全局事件 (可被其他模块导入使用) ---
_app_instance = None


def set_app_instance(app):
    global _app_instance
    _app_instance = app


EVT_FORCE_RELOGIN_TYPE = wx.NewEventType()
EVT_FORCE_RELOGIN = wx.PyEventBinder(EVT_FORCE_RELOGIN_TYPE, 1)


class ForceReloginEvent(wx.PyEvent):
    def __init__(self, message):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_FORCE_RELOGIN_TYPE)
        self.message = message


# ==============================================================================
# 1. Token 管理器进程 (The "Server" - 唯一的认证中心)
#    这个进程是整个应用中唯一负责调用API、刷新和存储Token的地方。
# ==============================================================================
class TokenManagerProcess(multiprocessing.Process):
    def __init__(self, request_queue, response_queue, log_queue=None):
        super().__init__()
        self.daemon = True  # 设置为守护进程，主程序退出时它也会退出
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.log_queue = log_queue

        # 将原AuthManager的状态变量移到这里
        self.access_token = None
        self.refresh_token = None
        self.access_token_expiry = 0

        # API URLs
        self.auth_url = f"{AUTH_SERVER_URL}/token"
        self.logout_url = f"{AUTH_SERVER_URL}/token/logout"
        self.refresh_url = f"{AUTH_SERVER_URL}/token/refresh"
        self.api_base_url = AUTH_SERVER_URL

    def run(self):
        # 【【【 这就是修复问题的核心 】】】
        # 在子进程开始时，第一件事就是配置它的日志系统
        if self.log_queue:
            configure_worker_logging(self.log_queue)

        """进程启动后执行的主循环"""
        logging.info(f"[TokenManagerProcess] Started with PID: {self.pid}")
        self._load_tokens_from_secure_storage()

        while True:
            try:
                # 阻塞等待来自任何客户端进程的请求
                request_id, command, payload = self.request_queue.get()

                if command == 'shutdown':
                    logging.info("[TokenManagerProcess] Shutdown signal received. Exiting.")
                    break

                # 根据指令执行相应操作
                handler = getattr(self, f"_handle_{command}", self._handle_unknown)
                success, result = handler(payload)

                # 将结果放回响应队列
                self.response_queue.put((request_id, (success, result)))

            except Exception as e:
                logging.error(f"[TokenManagerProcess] Unhandled exception in main loop: {e}")

    # --- 核心Token逻辑 (从原AuthManager迁移并适配) ---

    def _is_access_token_expired(self):
        return self.access_token is None or self.access_token_expiry < time.time() + 10

    def _do_refresh(self):
        """执行实际的Token刷新逻辑，返回 (bool, message)"""
        logging.info("[TokenManagerProcess] Attempting to refresh token...")
        if not self.refresh_token:
            return False, "No refresh token available."

        try:
            response = requests.post(self.refresh_url, json={"refresh_token": self.refresh_token})
            if response.status_code in [401, 403]:
                self._clear_tokens()
                msg = "身份凭证已失效，请重新登录"
                if _app_instance:  # 通过wx事件通知UI
                    evt = ForceReloginEvent(msg)
                    wx.PostEvent(_app_instance.GetTopWindow(), evt)
                return False, msg

            response.raise_for_status()
            data = response.json()
            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")

            if not new_access_token:
                return False, "Refresh response did not contain a new access_token."

            self.access_token = new_access_token
            self.access_token_expiry = time.time() + data.get("expires_in", 0)

            if new_refresh_token and new_refresh_token != self.refresh_token:
                self.refresh_token = new_refresh_token
                self._save_tokens_to_secure_storage()

            logging.info("[TokenManagerProcess] Token refresh successful.")
            return True, "Token refreshed successfully."

        except requests.RequestException as e:
            logging.error(f"[TokenManagerProcess] Token refresh failed: {e}")
            return False, f"Network error during refresh: {e}"

    # --- 指令处理器 ---

    def _handle_login(self, payload):
        username, password = payload['username'], payload['password']
        try:
            response = requests.post(self.auth_url, data={"username": username, "password": password})
            data = response.json()
            if response.status_code >= 400:
                return False, data.get("detail", "登录失败")

            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.access_token_expiry = time.time() + data.get("expires_in", 0)
            self._save_tokens_to_secure_storage()
            return True, "Login successful"
        except Exception as e:
            return False, f"An unexpected error occurred during login: {e}"

    def _handle_logout(self, payload):
        try:
            if self.refresh_token:
                requests.post(self.logout_url, json={"refresh_token": self.refresh_token})
        except Exception:
            pass  # 注销失败也无所谓，直接清理本地
        self._clear_tokens()
        return True, "Logged out"

    def _handle_api_request(self, payload):
        method, endpoint, kwargs = payload['method'], payload['endpoint'], payload['kwargs']

        is_file_download = kwargs.pop('is_file_download', False)
        # 【删除】不再需要主动检查和刷新
        # if self._is_access_token_expired():
        #     success, msg = self._do_refresh()
        #     if not success:
        #         return False, ViewException(f"身份验证失败: {msg}")

        # 准备请求
        if not self.access_token:  # 仍然需要检查是否有token
            return False, ViewException("用户未登录")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        url = f"{self.api_base_url}/{endpoint}"

        request_kwargs = kwargs.copy()  # 复制一份以防修改原始kwargs
        if is_file_download:
            request_kwargs['stream'] = True

        try:
            # --- 直接进行第一次尝试 ---
            response = requests.request(method, url, headers=headers, **request_kwargs)

            # --- 如果失败，进行响应式刷新和重试 ---
            if response.status_code in [401, 403]:
                logging.warning("[TokenManagerProcess] Received 401/403, forcing refresh and retry...")
                success, msg = self._do_refresh()
                if not success:
                    # _do_refresh 已经通知UI了，这里只返回错误
                    return False, ViewException(f"身份验证失败: {msg}")

                # 第二次尝试
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.request(method, url, headers=headers, **request_kwargs)

            # 检查重试后的结果
            response.raise_for_status()

            # 返回成功结果
            if is_file_download:
                # 文件下载模式：直接返回成功的 response 对象，让调用者处理
                return True, response
            else:
                return True, {
                    "status_code": response.status_code,
                    "json": response.json(),
                    "text": response.text,
                    "headers": dict(response.headers)
                }
        except requests.exceptions.HTTPError as e:
            # 捕获 raise_for_status 抛出的异常
            # 此时 response 对象是存在的
            response = e.response
            try:
                # 尝试从失败的响应中获取更有用的错误信息
                detail = response.json().get("detail", response.text)
            except:
                detail = response.text
            return False, ViewException(f"API请求失败 ({response.status_code}): {detail}")
        except Exception as e:
            # 捕获网络错误等其他异常
            return False, ViewException(f"API请求失败: {e}")

    def _handle_unknown(self, payload):
        return False, f"Unknown command: {payload}"

    # --- 本地存储逻辑 (与原版一致) ---
    def _load_tokens_from_secure_storage(self):
        try:
            self.refresh_token = keyring.get_password(SERVICE_ID, "refresh_token")
            if self.refresh_token:
                logging.info("[TokenManagerProcess] Refresh token loaded.")
        except Exception as e:
            logging.error(f"[TokenManagerProcess] Could not load refresh token: {e}")

    def _save_tokens_to_secure_storage(self):
        try:
            if self.refresh_token:
                keyring.set_password(SERVICE_ID, "refresh_token", self.refresh_token)
                logging.info("[TokenManagerProcess] New refresh token saved.")
        except Exception as e:
            logging.error(f"[TokenManagerProcess] Could not save refresh token: {e}")

    def _clear_tokens(self):
        self.access_token = None
        self.refresh_token = None
        self.access_token_expiry = 0
        try:
            keyring.delete_password(SERVICE_ID, "refresh_token")
        except Exception:
            pass

    # 在 TokenManagerProcess 类中添加一个处理器
    def _handle_is_logged_in(self, payload):
        # 判断逻辑：只要有 refresh_token，就认为已登录
        is_logged_in = self.refresh_token is not None
        return True, is_logged_in

    def _handle_refresh_tokens(self, payload):
        """
        处理来自客户端的手动刷新令牌请求。
        payload 在此场景下未使用，但保留签名一致性。
        """
        logging.info("[TokenManagerProcess] Manual token refresh requested by client.")
        # 直接调用您已经写好的、非常完善的刷新逻辑
        success, message = self._do_refresh()
        # _do_refresh 会返回 (bool, str) 或者 (bool, dict)
        # 我们直接将这个结果元组返回即可
        return success, message
# ==============================================================================
# 2. 客户端代理 (The "Client" - 其他进程使用的接口)
#    这个类提供与原AuthManager相同的API，但它不执行任何实际操作，
#    而是将请求通过队列发送给真正的TokenManagerProcess。
# ==============================================================================
class CentralAuthClient:
    def __init__(self, log_queue=None):
        self.request_queue = multiprocessing.Queue()
        self.response_queue = multiprocessing.Queue()
        self.pending_requests = {}  # {request_id: (threading.Event, result_container)}
        self.lock = threading.Lock()

        # 启动唯一的管理器进程
        self.manager_process = TokenManagerProcess(self.request_queue, self.response_queue, log_queue)
        self.manager_process.start()

        # 启动一个后台线程来监听响应队列
        self.response_listener_thread = threading.Thread(target=self._listen_for_responses, daemon=True)
        self.response_listener_thread.start()

        # 注册程序退出时的清理函数
        atexit.register(self.shutdown)
        logging.info("[CentralAuthClient] Initialized and TokenManagerProcess started.")

    def _listen_for_responses(self):
        """在后台线程中运行，接收来自管理器进程的响应"""
        while True:
            try:
                request_id, result = self.response_queue.get(timeout=36000)
                with self.lock:
                    if request_id in self.pending_requests:
                        event, result_container = self.pending_requests.pop(request_id)
                        result_container['result'] = result
                        event.set()  # 唤醒等待的线程
            except queue.Empty:
                continue  # 正常超时，继续等待
            except Exception as e:
                logging.error(f"[CentralAuthClient] Error in response listener: {e}")

    def _send_request(self, command, payload, timeout=3000):
        """发送请求并同步等待响应的通用方法"""
        request_id = str(uuid.uuid4())
        event = threading.Event()
        result_container = {}

        with self.lock:
            self.pending_requests[request_id] = (event, result_container)

        self.request_queue.put((request_id, command, payload))

        # 等待响应，或超时
        if not event.wait(timeout=timeout):
            # with self.lock:
            #     self.pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request '{command}' timed out after {timeout} seconds.")

        success, result = result_container['result']
        if not success:
            # 如果结果是异常，重新抛出它
            if isinstance(result, Exception):
                raise result
            # 否则抛出通用异常
            raise ViewException(str(result))

        return result

    def login(self, username, password, callback):
        """异步登录"""

        def _worker():
            try:
                result = self._send_request('login', {'username': username, 'password': password})
                wx.CallAfter(callback, True, result)
            except Exception as e:
                wx.CallAfter(callback, False, str(e))

        threading.Thread(target=_worker).start()

    def logout(self):
        """同步注销 (通常很快，可以同步)"""
        try:
            self._send_request('logout', {}, timeout=5)
        except Exception as e:
            logging.error(f"Logout failed: {e}")

    def make_api_request_sync(self, method, endpoint, **kwargs):
        """同步API请求，供后台线程或子进程使用"""
        payload = {'method': method, 'endpoint': endpoint, 'kwargs': kwargs}
        response_data = self._send_request('api_request', payload)
        if kwargs.get("is_file_download"):
            return response_data
        else:
            # 将返回的字典重新包装成一个类似requests.Response的对象
            response = requests.Response()
            response.status_code = response_data['status_code']
            response.headers = response_data['headers']
            response._content = response_data['text'].encode('utf-8')
            return response

    def make_api_request(self, method, endpoint, callback, **kwargs):
        """异步API请求，供UI线程使用"""

        def _worker():
            try:
                response = self.make_api_request_sync(method, endpoint, **kwargs)
                if callback:
                    wx.CallAfter(callback, True, None, response)
            except Exception as e:
                if callback:
                    wx.CallAfter(callback, False, str(e), None)

        threading.Thread(target=_worker).start()

    def refresh_tokens_sync(self, timeout=30):
        """
        同步手动触发令牌刷新。
        如果刷新成功，不返回任何内容。
        如果失败，则会抛出异常。

        :param timeout: 等待响应的超时时间（秒）。
        :raises: TimeoutError 如果超时，ViewException 如果刷新失败。
        """
        logging.info("[CentralAuthClient] Sending manual token refresh request...")
        # _send_request 在失败时会抛出异常，所以我们不需要检查返回值
        # payload 为空字典 {}，因为处理器不需要额外参数
        self._send_request('refresh_tokens', {}, timeout=timeout)
        logging.info("[CentralAuthClient] Manual token refresh completed successfully.")

    def refresh_tokens(self, callback=None):
        """
        异步手动触发令牌刷新。

        :param callback: 一个可选的回调函数，签名应为 callback(success, message)。
                         - success (bool): True 表示成功, False 表示失败。
                         - message (str): 包含成功或失败信息的字符串。
        """

        def _worker():
            try:
                self.refresh_tokens_sync()
                if callback:
                    # 成功时，message 可以是 None 或一个成功信息
                    wx.CallAfter(callback, True, "Tokens refreshed successfully.")
            except Exception as e:
                # 失败时，e 就是异常对象
                if callback:
                    wx.CallAfter(callback, False, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def shutdown(self):
        """优雅地关闭管理器进程"""
        logging.info("[CentralAuthClient] Shutting down TokenManagerProcess...")
        try:
            self.request_queue.put((None, 'shutdown', None))
            self.manager_process.join(timeout=5)
            if self.manager_process.is_alive():
                self.manager_process.terminate()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

    # 在 CentralAuthClient 类中添加一个对应的方法（按钮）
    def is_logged_in_sync(self):
        """同步检查用户是否已登录"""
        try:
            return self._send_request('is_logged_in', {}, timeout=5)
        except Exception:
            return False

    def is_logged_in(self, callback):
        """异步检查用户是否已登录"""
        def _worker():
            result = self.is_logged_in_sync()
            wx.CallAfter(callback, result)

        threading.Thread(target=_worker).start()

    def get_transferable_state(self):
        """
        返回一个可被序列化并传递给子进程的状态字典。
        这包含了与管理器进程通信所需的所有核心组件（队列）。
        """
        return {
            'request_queue': self.request_queue,
            'response_queue': self.response_queue,
        }

    @classmethod
    def from_transferable_state(cls, state):
        """
        一个类方法，用于在子进程中从传递过来的状态重建一个功能客户端。
        注意：这个重建的客户端不会启动新的管理器进程。
        """
        # 创建一个“空”的实例，不执行常规的 __init__ 逻辑
        client = cls.__new__(cls)

        # 直接从 state 字典中填充必要的属性
        client.request_queue = state['request_queue']
        client.response_queue = state['response_queue']

        # 初始化这个客户端实例本地所需的其他属性
        client.pending_requests = {}
        client.lock = threading.Lock()

        # 在这个子进程客户端中，也需要启动响应监听线程
        client.response_listener_thread = threading.Thread(target=client._listen_for_responses, daemon=True)
        client.response_listener_thread.start()

        # 这个客户端不拥有 manager_process，也不负责 shutdown
        client.manager_process = None

        logging.info("[CentralAuthClient] Reconstructed from state in a child process.")
        return client
# ==============================================================================
# 3. 全局实例管理器
#    我们不再在模块加载时自动创建实例。
# ==============================================================================

_global_client = None
_global_client_state = None # 新增一个全局变量来存储可传递的状态
_lock = threading.Lock()

def get_api_client():
    """
    获取全局唯一的 CentralAuthClient 实例。
    在子进程中，它会根据传递的状态来重建客户端。
    """
    global _global_client
    with _lock:
        if _global_client is None:
            # 如果在子进程中，并且状态已经被设置，就用它来重建
            if _global_client_state:
                _global_client = CentralAuthClient.from_transferable_state(_global_client_state)
            else:
                 raise RuntimeError("CentralAuthClient has not been initialized. "
                                    "Please call initialize_api_client() in your main process.")
    return _global_client

def initialize_api_client(log_queue=None):
    """
    这个函数必须且只能在主进程的 __main__ 块中被调用一次。
    """
    global _global_client, _global_client_state
    with _lock:
        if _global_client is None:
            print("[AuthInitializer] Creating the one and only CentralAuthClient...")
            _global_client = CentralAuthClient(log_queue=log_queue)
            # 【关键】创建后，立即获取其可传递的状态
            _global_client_state = _global_client.get_transferable_state()
        return _global_client

def set_initial_state_for_process(state):
    """
    这个函数由主进程在启动子进程前调用，用于在子进程环境中设置初始状态。
    但由于 Windows 的进程创建机制，我们不能直接这样做。
    我们将把 state 作为参数传递给子进程的启动函数。
    """
    global _global_client_state
    _global_client_state = state