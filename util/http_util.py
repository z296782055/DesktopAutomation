import keyring
import wx

SERVICE_ID = "YourWxPythonAppService" # 你的应用的服务ID

def save_token_to_keyring(username, token):
    try:
        keyring.set_password(SERVICE_ID, username, token)
        print(f"Token 已安全保存到系统密钥链，用户: {username}")
        return True
    except keyring.errors.NoKeyringError:
        print("未找到可用的系统密钥链后端。")
        return False
    except Exception as e:
        print(f"保存 Token 到密钥链失败: {e}")
        return False

def load_token_from_keyring(username):
    try:
        token = keyring.get_password(SERVICE_ID, username)
        if token:
            print(f"Token 已从系统密钥链加载，用户: {username}")
        else:
            print(f"系统密钥链中未找到用户 {username} 的 Token。")
        return token
    except keyring.errors.NoKeyringError:
        print("未找到可用的系统密钥链后端。")
        return None
    except Exception as e:
        print(f"从密钥链加载 Token 失败: {e}")
        return None

def delete_token_from_keyring(username):
    try:
        keyring.delete_password(SERVICE_ID, username)
        print(f"用户 {username} 的 Token 已从系统密钥链删除。")
        return True
    except keyring.errors.NoKeyringError:
        print("未找到可用的系统密钥链后端。")
        return False
    except Exception as e:
        print(f"从密钥链删除 Token 失败: {e}")
        return False

# 在登录成功后
# save_token_to_keyring(username, token)

# 在应用启动时或需要 Token 时
# loaded_token = load_token_from_keyring(username)

# 登出时
# delete_token_from_keyring(username)
