import keyring
import requests
import time
import threading
import wx
from util import utils

# --- 配置 ---
AUTH_SERVER_URL = utils.get_config("server_url")  # FastAPI 后端地址
SERVICE_ID = "DesktopAutomation" # 你的应用的服务ID

# --- 全局变量和事件 ---
_app_instance = None  # 用于从线程回调到主UI线程


def set_app_instance(app):
    global _app_instance
    _app_instance = app


# 1. 定义一个新的事件类型
EVT_FORCE_RELOGIN_TYPE = wx.NewEventType()

# 2. 定义一个事件绑定器
# 第一个参数是事件类型，第二个参数是事件ID的数量（通常为1）
EVT_FORCE_RELOGIN = wx.PyEventBinder(EVT_FORCE_RELOGIN_TYPE, 1)

# 3. 定义自定义事件类
class ForceReloginEvent(wx.PyEvent):
    def __init__(self, message):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_FORCE_RELOGIN_TYPE) # 使用上面定义的事件类型
        self.message = message


# --- AuthManager 类 ---
class AuthManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.access_token_expiry = 0  # Unix timestamp

        self.auth_url = f"{AUTH_SERVER_URL}/token"
        self.logout_url = f"{AUTH_SERVER_URL}/token/logout"
        self.refresh_url = f"{AUTH_SERVER_URL}/token/refresh"
        self.api_base_url = AUTH_SERVER_URL  # 假设API都在同一个根路径

        self._refresh_lock = threading.Lock()  # 用于防止并发刷新请求

        # 尝试从安全存储加载refresh token
        self._load_tokens_from_secure_storage()

    def _load_tokens_from_secure_storage(self):
        try:
            stored_refresh_token = keyring.get_password(SERVICE_ID, "refresh_token")
            if stored_refresh_token:
                self.refresh_token = stored_refresh_token
                print("[AuthManager] Refresh token loaded from secure storage.")
        except Exception as e:
            print(f"[AuthManager] Could not load refresh token from secure storage: {e}")

    def _save_tokens_to_secure_storage(self):
        try:
            if self.refresh_token:
                keyring.set_password(SERVICE_ID, "refresh_token", self.refresh_token)
                print("[AuthManager] Refresh token saved to secure storage.")
        except Exception as e:
            print(f"[AuthManager] Could not save refresh token to secure storage: {e}")

    def _clear_tokens(self):
        self.access_token = None
        self.refresh_token = None
        self.access_token_expiry = 0
        try:
            keyring.delete_password(SERVICE_ID, "refresh_token")
            print("[AuthManager] Tokens cleared from memory and secure storage.")
        except Exception as e:
            print(f"[AuthManager] Could not clear refresh token from secure storage: {e}")

    def is_access_token_expired(self):
        # 提前10秒刷新，避免临界情况
        return self.access_token is None or self.access_token_expiry < time.time() + 10

    def login(self, username, password, callback):
        """
        处理用户登录。
        callback(success: bool, message: str)
        """
        def _do_login():
            try:
                payload = {
                        "username" : username,
                        "password" : password
                    }
                response = requests.post(self.auth_url, data=payload)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                # expires_in 是 Access Token 的秒数
                self.access_token_expiry = time.time() + data.get("expires_in", 0)

                self._save_tokens_to_secure_storage()
                wx.CallAfter(callback, True, None)  # 登录成功
            except requests.exceptions.RequestException as e:
                wx.CallAfter(callback, False, "登录失败")
            except Exception as e:
                wx.CallAfter(callback, False, f"An unexpected error occurred during login: {e}")

        threading.Thread(target=_do_login).start()

    def refresh_access_token(self, callback=None, completion_event=None):  # 添加 completion_event 参数
        """
        使用 Refresh Token 刷新 Access Token。
        callback(success: bool, message: str) - 用于异步调用
        completion_event: threading.Event - 用于同步调用，刷新完成后会设置此事件
        """
        # 确保只有一个刷新请求在进行
        if not self._refresh_lock.acquire(blocking=False):
            # 另一个刷新请求正在进行，等待它完成
            # 对于同步调用，这里可以等待，但为了简化，我们假设调用方会处理
            print("[AuthManager] Another refresh in progress, skipping.")
            if callback:
                wx.CallAfter(callback, False, "正在验证身份凭证，请稍等")
            if completion_event:
                completion_event.set()  # 即使跳过，也要设置事件，避免调用方无限等待
            return

        def _do_refresh():
            try:
                if not self.refresh_token:
                    raise ValueError("No refresh token available. Cannot refresh.")

                response = requests.post(self.refresh_url, json={"refresh_token": self.refresh_token})
                response.raise_for_status()
                data = response.json()

                self.access_token = data.get("access_token")
                # 后端可能返回新的 refresh token，也可能返回旧的
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                self.access_token_expiry = time.time() + data.get("expires_in", 0)

                self._save_tokens_to_secure_storage()
                print("[AuthManager] Token refreshed successfully.")
                if callback:  # 只有当提供了回调函数时才调用 wx.CallAfter
                    wx.CallAfter(callback, True, None)
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"[AuthManager] Token refresh failed: {e}")
                self._clear_tokens()  # 刷新失败，清除所有token，强制重新登录
                if callback:  # 只有当提供了回调函数时才调用 wx.CallAfter
                    wx.CallAfter(callback, False, f"Token refresh failed: {e}. Please re-login.")
                # 发送自定义事件，通知主UI线程强制重新登录
                if _app_instance:
                    evt = ForceReloginEvent(f"Session expired or invalid: {e}")
                    wx.PostEvent(_app_instance.GetTopWindow(), evt)  # 发送到主窗口
            except Exception as e:
                print(f"[AuthManager] An unexpected error occurred during refresh: {e}")
                self._clear_tokens()
                if callback:  # 只有当提供了回调函数时才调用 wx.CallAfter
                    wx.CallAfter(callback, False, f"An unexpected error occurred during refresh: {e}. Please re-login.")
                if _app_instance:
                    evt = ForceReloginEvent(f"An unexpected error occurred: {e}")
                    wx.PostEvent(_app_instance.GetTopWindow(), evt)
            finally:
                self._refresh_lock.release()
                if completion_event:  # 无论成功失败，都设置事件
                    completion_event.set()

        threading.Thread(target=_do_refresh).start()

    def _perform_http_request(self, method, endpoint, json_data=None, data=None, files=None):
        """
        内部方法：实际执行HTTP请求，不包含刷新逻辑，直接抛出异常。
        """
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        url = f"{self.api_base_url}/{endpoint}"

        response = requests.request(method, url, json=json_data, headers=headers, data=data, files=files)
        # response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response

    def make_api_request(self, method, endpoint, json_data=None, callback=None):
        """
        异步发起受保护的API请求，包含自动刷新逻辑。
        callback(success: bool, message: str, data: dict)
        """

        def _do_request_with_refresh_check():
            if self.is_access_token_expired():
                print("[AuthManager] Access Token expired, attempting to refresh...")

                # Access Token 过期，尝试刷新
                def _on_refresh_complete(success, message):
                    if success:
                        # 刷新成功，重试原始请求
                        print("[AuthManager] Refresh successful, retrying original request.")
                        try:
                            data = self._perform_http_request(method, endpoint, json_data)
                            if callback:
                                wx.CallAfter(callback, True, None, data)
                        except requests.exceptions.HTTPError as e:
                            print(f"[AuthManager] HTTP Error on retry: {e.response.status_code} - {e.response.text}")
                            if callback:
                                wx.CallAfter(callback, False,
                                             f"API error on retry: {e.response.status_code} - {e.response.text}", None)
                        except requests.exceptions.RequestException as e:
                            print(f"[AuthManager] Network error on retry: {e}")
                            if callback:
                                wx.CallAfter(callback, False, f"Network error on retry: {e}", None)
                        except Exception as e:
                            print(f"[AuthManager] An unexpected error occurred on retry during API request: {e}")
                            if callback:
                                wx.CallAfter(callback, False, f"An unexpected error occurred on retry: {e}", None)
                    else:
                        # 刷新失败，通知UI需要重新登录 (已由 refresh_access_token 处理)
                        if callback:
                            wx.CallAfter(callback, False, message, None)

                self.refresh_access_token(callback=_on_refresh_complete)
            else:
                # Access Token 有效，直接请求
                try:
                    data = self._perform_http_request(method, endpoint, json_data)
                    if callback:
                        wx.CallAfter(callback, True, None, data)
                except requests.exceptions.HTTPError as e:
                    print(f"[AuthManager] HTTP Error: {e.response.status_code} - {e.response.text}")
                    if e.response.status_code in [401, 403]:
                        # Access Token 真正过期或无效，再次尝试刷新 (以防万一)
                        print("[AuthManager] Received 401/403, attempting refresh again...")

                        def _on_refresh_complete_after_401(success, message):
                            if success:
                                print("[AuthManager] Refresh successful after 401, retrying original request.")
                                try:
                                    data = self._perform_http_request(method, endpoint, json_data)
                                    if callback:
                                        wx.CallAfter(callback, True, None, data)
                                except requests.exceptions.RequestException as e:
                                    if callback:
                                        wx.CallAfter(callback, False, f"Network error on 401 retry: {e}", None)
                            else:
                                if callback:
                                    wx.CallAfter(callback, False, message, None)

                        self.refresh_access_token(callback=_on_refresh_complete_after_401)
                    else:
                        if callback:
                            wx.CallAfter(callback, False, f"API error: {e.response.status_code} - {e.response.text}",
                                         None)
                except requests.exceptions.RequestException as e:
                    print(f"[AuthManager] Network error: {e}")
                    if callback:
                        wx.CallAfter(callback, False, f"Network error: {e}", None)
                except Exception as e:
                    print(f"[AuthManager] An unexpected error occurred during API request: {e}")
                    if callback:
                        wx.CallAfter(callback, False, f"An unexpected error occurred: {e}", None)

        threading.Thread(target=_do_request_with_refresh_check).start()

    def make_api_request_sync(self, method, endpoint, json_data=None, data=None, files=None):
        """
        同步发起受保护的API请求，包含自动刷新逻辑。
        此方法会阻塞当前线程，直到请求完成。
        **警告：切勿在 wxPython 主 UI 线程中调用此方法！**

        Args:
            method (str): HTTP 方法 (GET, POST, PUT, DELETE, etc.)
            endpoint (str): API 端点 (例如 "data", "users/me")
            json_data (dict, optional): 要发送的 JSON 数据。Defaults to None.

        Returns:
            dict: API 响应的 JSON 数据。

        Raises:
            requests.exceptions.RequestException: 如果请求失败（网络错误、HTTP 错误等）。
            Exception: 如果认证失败或刷新令牌无效。
        """
        max_retries = 2  # 第一次尝试 + 一次刷新重试

        for attempt in range(max_retries):
            # 1. 检查 Access Token 是否过期，并尝试刷新
            if self.is_access_token_expired():
                print(f"[AuthManager Sync] Access Token expired, attempting to refresh (Attempt {attempt + 1})...")
                refresh_event = threading.Event()

                # 启动刷新线程，并等待其完成
                # 注意：refresh_access_token 内部会启动一个线程
                # 我们在这里等待这个线程通过 completion_event.set() 来通知我们完成
                self.refresh_access_token(completion_event=refresh_event)
                refresh_event.wait()  # 阻塞当前线程，直到刷新操作完成

                # 检查刷新是否成功
                if self.access_token is None:
                    # 如果刷新失败（例如 refresh token 过期或被吊销），access_token 会被清空
                    raise Exception("Failed to refresh token. Please re-login.")
                print("[AuthManager Sync] Token refreshed successfully.")

            # 2. 执行实际的 HTTP 请求
            try:
                data = self._perform_http_request(method, endpoint, json_data, data, files)
                return data  # 成功，返回数据
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [401, 403] and attempt < max_retries - 1:
                    print(
                        f"[AuthManager Sync] Received 401/403 on attempt {attempt + 1}, attempting refresh and retry...")
                    self.access_token = None  # 清空 Access Token，强制下一次循环进行刷新
                    continue  # 进入下一次循环进行刷新和重试
                else:
                    raise e  # 抛出其他 HTTP 错误或最终的 401/403
            except requests.exceptions.RequestException as e:
                raise e  # 抛出网络错误

        # 理论上不应该到达这里，除非 max_retries 设置不当或逻辑有误
        raise Exception("Unexpected error during synchronous API request.")

    def logout(self):
        def _do_logout():
            try:
                requests.post(self.logout_url, json={"refresh_token": self.refresh_token})
            except requests.exceptions.RequestException as e:
                pass
            except Exception as e:
                pass
        threading.Thread(target=_do_logout).start()
        self._clear_tokens()
        print("[AuthManager] Logged out.")


# 全局客户端实例
api_client = AuthManager()

