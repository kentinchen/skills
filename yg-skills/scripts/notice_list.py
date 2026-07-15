import requests
import json
import base64
import os
import sys
from datetime import datetime

try:
    import socks
except ImportError:
    pass

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

DEFAULT_SSO_URL = "https://zwwsfrz.cdmbc.cn"
DEFAULT_APP_URL = "https://10.190.227.110"
DEFAULT_APP_CODE = "2a06bab333f5257deb664b8b16a30f23"
DEFAULT_LOGIN_DEVICE_INFO = "a8799d06d5e4b4bf4b8efe54b5086f7c"

_global_token = None
_global_config = None

def get_config_path():
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".yg-skills", "config.yml")

def get_ocr_config_path():
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".dddd-ocr", "config.yml")

def read_ocr_config():
    config_path = get_ocr_config_path()
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and isinstance(config, dict):
                    return config.get('base_url'), config.get('proxy')
        except Exception as e:
            print(f"读取OCR配置文件失败: {e}")
    return None, None

def read_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    import yaml
                    config = yaml.safe_load(content)
                    if config and isinstance(config, dict):
                        return {
                            'username': config.get('username'),
                            'password': config.get('password'),
                            'app_username': config.get('app_username'),
                            'sso_url': config.get('sso_url') or config.get('base_url'),
                            'app_url': config.get('app_url'),
                            'proxy': config.get('proxy'),
                            'app_code': config.get('app_code'),
                            'login_device_info': config.get('login_device_info')
                        }
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    return {
        'username': None,
        'password': None,
        'app_username': None,
        'sso_url': None,
        'app_url': None,
        'proxy': None,
        'app_code': None,
        'login_device_info': None
    }

def get_timestamp():
    return str(int(datetime.now().timestamp() * 1000))

def get_common_headers():
    return {
        'Authentication': '',
        'Content-Type': 'application/json',
        'Sec-Fetch-Storage-Access': 'active',
        'X-Request-With': 'XMLHttpRequest'
    }

def get_public_key(sso_url, proxy=None):
    url = f"{sso_url}/sso-server/getPublicKey"
    params = {'_t': get_timestamp()}
    headers = get_common_headers()
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.get(url, params=params, headers=headers, proxies=proxies, verify=False)
        result = response.json()
        if result.get('resp_code') == 200:
            return result.get('datas')
        else:
            print(f"获取公钥失败: {result.get('resp_msg')}")
            return None
    except Exception as e:
        print(f"获取公钥异常: {e}")
        return None

def get_captcha(sso_url, proxy=None):
    url = f"{sso_url}/verify-server/kaptcha/generate"
    params = {'_t': get_timestamp()}
    headers = get_common_headers()
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.get(url, params=params, headers=headers, proxies=proxies, verify=False)
        result = response.json()
        if result.get('resp_code') == 200:
            datas = result.get('datas')
            return datas.get('image'), datas.get('picCodeId')
        else:
            print(f"获取验证码失败: {result.get('resp_msg')}")
            return None, None
    except Exception as e:
        print(f"获取验证码异常: {e}")
        return None, None

def rsa_encrypt(text, public_key):
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
    
    key = RSA.import_key(base64.b64decode(public_key))
    cipher = PKCS1_v1_5.new(key)
    
    text_bytes = text.encode('utf-8')
    max_chunk_size = key.size_in_bytes() - 11
    
    encrypted_chunks = []
    for i in range(0, len(text_bytes), max_chunk_size):
        chunk = text_bytes[i:i+max_chunk_size]
        encrypted = cipher.encrypt(chunk)
        encrypted_chunks.append(encrypted)
    
    encrypted_data = b''.join(encrypted_chunks)
    return base64.b64encode(encrypted_data).decode('utf-8')

def recognize_captcha(image_base64, ocr_server="http://localhost:8000", proxy=None):
    if image_base64.startswith('data:image/png;base64,'):
        image_base64 = image_base64.split(',')[1]
    
    url = f"{ocr_server}/ocr"
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        import io
        image_bytes = base64.b64decode(image_base64)
        files = {"file": ("captcha.png", io.BytesIO(image_bytes), "image/png")}
        response = requests.post(url, files=files, proxies=proxies, verify=False)
        result = response.json()
        if result.get('code') == 200:
            return result.get('data')
        else:
            print(f"验证码识别失败: {result.get('message')}")
            return None
    except Exception as e:
        print(f"调用OCR服务异常: {e}")
        return None

def login(sso_url, username, password, proxy=None, app_code=DEFAULT_APP_CODE, login_device_info=DEFAULT_LOGIN_DEVICE_INFO, app_username=None):
    ocr_server, ocr_proxy = read_ocr_config()
    if not ocr_server:
        ocr_server = "http://localhost:8000"
    
    public_key = get_public_key(sso_url, proxy)
    if not public_key:
        print("无法获取公钥，登录失败")
        return None
    
    encrypted_username = rsa_encrypt(username, public_key)
    encrypted_password = rsa_encrypt(password, public_key)
    
    image_base64, pic_code_id = get_captcha(sso_url, proxy)
    if not image_base64 or not pic_code_id:
        print("获取验证码失败")
        return None
    
    img_code = recognize_captcha(image_base64, ocr_server, ocr_proxy)
    if not img_code:
        print("验证码识别失败")
        return None
    
    url = f"{sso_url}/sso-server/wmh/Internal/users"
    params = {'_t': get_timestamp()}
    headers = get_common_headers()
    
    payload = {
        'userName': encrypted_username,
        'passWord': encrypted_password,
        'imgCode': img_code,
        'picCodeId': pic_code_id,
        'appCode': app_code,
        'state': None,
        'loginDeviceInfo': login_device_info
    }
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.post(url, params=params, headers=headers, json=payload, proxies=proxies, verify=False)
        result = response.json()
        
        if result.get('resp_code') == 200:
            datas = result.get('datas')
            print(f"登录成功，完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            if datas:
                art = datas.get('art')
                token = datas.get('token')
                if art:
                    print(f"获取到SSO art: {art}...")
                    app_token = exchange_app_token(art, app_username)
                    if app_token:
                        return app_token
                    print("无法获取APP art token")
                    return art
            print(f"登录成功，但未获取到art")
            return None
        else:
            print(f"登录失败: {result.get('resp_msg')}")
            return None
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None

def get_user_info_by_art(art):
    global _global_config
    
    if _global_config is None:
        _global_config = read_config()
    
    app_url = _global_config.get('app_url') or DEFAULT_APP_URL
    proxy = _global_config.get('proxy')
    
    url = f"{app_url}/prod-api/loginByArt"
    params = {
        'art': art
    }
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.get(url, params=params, proxies=proxies, verify=False)
        result = response.json()
        print(f"loginByArt响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 200 and result.get('success') == True:
            data = result.get('data')
            if data and isinstance(data, list) and len(data) > 0:
                return data[0].get('userName')
            print("loginByArt成功，但未获取到userName")
        else:
            print(f"loginByArt失败: {result.get('msg')}")
    except Exception as e:
        print(f"loginByArt异常: {e}")
    
    return None

def exchange_app_token(sso_token, username=None):
    global _global_config
    
    if _global_config is None:
        _global_config = read_config()
    
    art = sso_token
    app_username = get_user_info_by_art(art)
    
    if not app_username:
        print(f"无法通过loginByArt获取userName，使用传入的username: {username}")
        app_username = username
    
    if not app_username:
        print("错误: 缺少APP用户名")
        return None
    
    app_url = _global_config.get('app_url') or DEFAULT_APP_URL
    proxy = _global_config.get('proxy')
    
    url = f"{app_url}/prod-api/loginByArtUserId"
    params = {
        'art': sso_token,
        'userName': app_username
    }
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.get(url, params=params, proxies=proxies, verify=False)
        result = response.json()
        print(f"APP登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 200 and result.get('success') == True:
            app_token = result.get('msg')
            if app_token:
                print(f"获取到APP token: {app_token}")
                global _global_token
                _global_token = app_token
                return app_token
            print(f"APP登录成功，但未获取到token")
        else:
            print(f"APP登录失败: {result.get('msg')}")
    except Exception as e:
        print(f"APP登录异常: {e}")
    
    return None

def get_token(force_login=False, app_username=None):
    global _global_token, _global_config   
    if not force_login and _global_token:
        return _global_token
    
    username = _global_config.get('username')
    password = _global_config.get('password')
    if app_username is None:
        app_username = _global_config.get('app_username') or username
    sso_url = _global_config.get('sso_url') or DEFAULT_SSO_URL
    proxy = _global_config.get('proxy')
    app_code = _global_config.get('app_code') or DEFAULT_APP_CODE
    login_device_info = _global_config.get('login_device_info') or DEFAULT_LOGIN_DEVICE_INFO
    
    if not username or not password:
        print("错误: 配置文件中缺少用户名或密码")
        sys.exit(1)    
    if not app_username:
        print("错误: 配置文件中缺少app_username")
        sys.exit(1)
    
    token = login(sso_url, username, password, proxy, app_code, login_device_info, app_username)
    if token:
        _global_token = token    
    return _global_token

def call_api(url, method='get', headers=None, params=None, json=None, proxy=None):
    global _global_config   
    if proxy is None:
        proxy = _global_config.get('proxy')    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, params=params, proxies=proxies, verify=False)
        elif method.lower() == 'post':
            response = requests.post(url, headers=headers, params=params, json=json, proxies=proxies, verify=False)
        else:
            print(f"不支持的HTTP方法: {method}")
            return None
        
        return response.json()
    except Exception as e:
        print(f"API调用异常: {e}")
        return None

def get_notice_list(page_num=1, page_size=5, notice_type=1, token_required=True, app_username=None):
    global _global_config
    app_url = _global_config.get('app_url') or DEFAULT_APP_URL
    
    url = f"{app_url}/prod-api/noToken/notice/mylist"
    params = {
        'pageNum': page_num,
        'pageSize': page_size,
        'noticeType': notice_type
    }    
    headers = {
        'Content-Type': 'application/json'
    }

    result = call_api(url, method='get', headers=headers, params=params)    
    if result:
        code = result.get('code')
        if code == 200:    
            return result.get('msg')
        else:
            print(f"查询通知清单失败: {result.get('msg')}")
    return None

def main():
    import argparse   
    parser = argparse.ArgumentParser(description="通知清单查询脚本")
    parser.add_argument('--page-num', '--pageNum', type=int, default=1, help='页码')
    parser.add_argument('--page-size', '--pageSize', type=int, default=5, help='每页大小')
    parser.add_argument('--notice-type', '--noticeType', type=int, default=1, help='通知类型: 普通公告1、安全情报2、资源变化')
    parser.add_argument('--app-username', '--app_username', help='APP用户名（用于获取APP token，可能与SSO用户名不同）')
    args = parser.parse_args()   
    
    print(f"查询通知清单: pageNum={args.page_num}, pageSize={args.page_size}, noticeType={args.notice_type}")    
    result = get_notice_list(args.page_num, args.page_size, args.notice_type, not args.no_token, args.app_username)
    
    if result:
        print("\n通知清单查询结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n查询失败")

if __name__ == "__main__":
    _global_config = read_config()    
    main()