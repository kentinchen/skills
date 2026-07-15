import requests
import json
import os
import sys

try:
    import socks
except ImportError:
    pass

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sso_login import (
    DEFAULT_SSO_URL, DEFAULT_APP_URL, DEFAULT_APP_CODE, DEFAULT_LOGIN_DEVICE_INFO,
    read_config, read_ocr_config, get_timestamp, get_common_headers,
    get_public_key, get_captcha, rsa_encrypt, recognize_captcha, login
)

_global_token = None
_global_config = None

def get_user_info_by_art(art):
    global _global_config
    
    if _global_config is None:
        _global_config = read_config()
    
    app_url = _global_config.get('app_url') or DEFAULT_APP_URL
    proxy = _global_config.get('proxy')
    
    url = f"{app_url}/prod-api/loginByArt"
    params = {'art': art}
    
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

def sso_login(sso_url, username, password, proxy=None, app_code=DEFAULT_APP_CODE, login_device_info=DEFAULT_LOGIN_DEVICE_INFO, app_username=None):
    ocr_server, ocr_proxy = read_ocr_config()
    if not ocr_server:
        ocr_server = "http://localhost:8000"
    
    image_base64, pic_code_id = get_captcha(sso_url, proxy)
    if not image_base64 or not pic_code_id:
        print("获取验证码失败")
        return None
    
    img_code = recognize_captcha(image_base64, ocr_server, ocr_proxy)
    if not img_code:
        print("验证码识别失败")
        return None
    
    result = login(sso_url, username, password, img_code, pic_code_id, proxy, app_code, login_device_info)
    
    if result and result.get('resp_code') == 200:
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
                print("无法获取APP token")
                return art
            elif token:
                print(f"获取到SSO token: {token[:20]}...")
                app_token = exchange_app_token(token, app_username)
                if app_token:
                    return app_token
                print("无法获取APP token，使用SSO token")
                return token
        print(f"登录成功，但未获取到token")
    else:
        print(f"登录失败: {result.get('resp_msg') if result else '未知错误'}")
    
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
    
    token = sso_login(sso_url, username, password, proxy, app_code, login_device_info, app_username)
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
    result = get_notice_list(args.page_num, args.page_size, args.notice_type, True, args.app_username)
    
    if result:
        print("\n通知清单查询结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n查询失败")

if __name__ == "__main__":
    _global_config = read_config()
    main()
