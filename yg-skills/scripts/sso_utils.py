import base64
import json
import os
import sys
from datetime import datetime

import requests

DEFAULT_SSO_URL = "https://zwwsfrz.cdmbc.cn"
DEFAULT_APP_URL = "https://10.190.227.110"
DEFAULT_APP_CODE = "2a06bab333f5257deb664b8b16a30f23"
DEFAULT_LOGIN_DEVICE_INFO = "a8799d06d5e4b4bf4b8efe54b5086f7c"


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


def save_ocr_config(base_url, proxy=None):
    config_path = get_ocr_config_path()
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    import yaml
    config = {
        'base_url': base_url,
        'proxy': proxy
    }

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"OCR配置已保存到: {config_path}")
    except Exception as e:
        print(f"保存OCR配置文件失败: {e}")


def get_ocr_server_and_proxy():
    ocr_server, ocr_proxy = read_ocr_config()
    if ocr_server:
        print(f"使用保存的OCR服务地址: {ocr_server}")
        return ocr_server, ocr_proxy
    else:
        try:
            ocr_server = input("请输入ddddocr服务地址: ")
            if not ocr_server.strip():
                ocr_server = "http://localhost:8000"
                print(f"使用默认地址: {ocr_server}")
            proxy_input = input("请输入代理地址（可选，按回车跳过）: ")
            ocr_proxy = proxy_input.strip() if proxy_input.strip() else None
            save_ocr_config(ocr_server, ocr_proxy)
            return ocr_server, ocr_proxy
        except EOFError:
            return "http://localhost:8000", None


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


def save_config(config):
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    import yaml
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"配置已保存到: {config_path}")
    except Exception as e:
        print(f"保存配置文件失败: {e}")


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
        response = requests.get(url, params=params, headers=headers, proxies=proxies)
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
        response = requests.get(url, params=params, headers=headers, proxies=proxies)
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
        chunk = text_bytes[i:i + max_chunk_size]
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
        response = requests.post(url, files=files, proxies=proxies)
        result = response.json()
        if result.get('code') == 200:
            return result.get('data')
        else:
            print(f"验证码识别失败: {result.get('message')}")
            return None
    except Exception as e:
        print(f"调用OCR服务异常: {e}")
        return None


def login(sso_url, username, password, img_code, pic_code_id, proxy=None, app_code=DEFAULT_APP_CODE,
          login_device_info=DEFAULT_LOGIN_DEVICE_INFO):
    public_key = get_public_key(sso_url, proxy)
    if not public_key:
        print("无法获取公钥，登录失败")
        return None

    encrypted_username = rsa_encrypt(username, public_key)
    encrypted_password = rsa_encrypt(password, public_key)

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
        response = requests.post(url, params=params, headers=headers, json=payload, proxies=proxies)
        return response.json()
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SSO登录脚本")
    parser.add_argument('--proxy', help='代理地址')
    parser.add_argument('--sso-url', '--sso_url', help='SSO服务地址')
    parser.add_argument('--username', help='用户名')
    parser.add_argument('--password', help='密码')
    parser.add_argument('--app-url', '--app_url', help='APP服务地址')
    parser.add_argument('--app-code', '--app_code', help='APP_CODE')
    parser.add_argument('--login-device-info', '--login_device_info', help='LOGIN_DEVICE_INFO')
    parser.add_argument('--ocr-server', '--ocr_server', help='OCR服务地址')
    parser.add_argument('--ocr-proxy', '--ocr_proxy', help='OCR代理地址')
    args = parser.parse_args()

    saved_config = read_config()

    sso_url = args.sso_url if args and args.sso_url else saved_config['sso_url']
    app_url = args.app_url if args and args.app_url else saved_config['app_url']
    proxy = args.proxy if args and args.proxy else saved_config['proxy']
    app_code = args.app_code if args and args.app_code else saved_config['app_code']
    login_device_info = args.login_device_info if args and args.login_device_info else saved_config['login_device_info']

    if args and args.ocr_server:
        ocr_server = args.ocr_server
        _, saved_ocr_proxy = read_ocr_config()
        ocr_proxy = args.ocr_proxy if args.ocr_proxy else saved_ocr_proxy
        save_ocr_config(ocr_server, ocr_proxy)
    else:
        ocr_server, ocr_proxy = get_ocr_server_and_proxy()

    if args and args.username:
        username = args.username
    elif saved_config['username']:
        username = saved_config['username']
        print(f"使用保存的用户名: {username}")
    else:
        try:
            username = input("请输入用户名: ")
        except EOFError:
            print("错误: 非交互式环境下必须提供用户名")
            sys.exit(1)

    if args and args.password:
        password = args.password
    elif saved_config['password']:
        password = saved_config['password']
        print("使用保存的密码")
    else:
        try:
            from getpass import getpass
            password = getpass("请输入密码: ")
        except EOFError:
            print("错误: 非交互式环境下必须提供密码")
            sys.exit(1)

    if sso_url is None:
        try:
            sso_url_input = input(f"请输入SSO服务地址（默认: {DEFAULT_SSO_URL}）: ")
            if sso_url_input.strip():
                sso_url = sso_url_input.strip()
            else:
                sso_url = DEFAULT_SSO_URL
            print(f"使用SSO服务地址: {sso_url}")
        except EOFError:
            sso_url = DEFAULT_SSO_URL

    if app_url is None:
        try:
            app_url_input = input(f"请输入APP服务地址（默认: {DEFAULT_APP_URL}）: ")
            if app_url_input.strip():
                app_url = app_url_input.strip()
            else:
                app_url = DEFAULT_APP_URL
            print(f"使用APP服务地址: {app_url}")
        except EOFError:
            app_url = DEFAULT_APP_URL

    if app_code is None:
        try:
            app_code_input = input(f"请输入APP_CODE（默认: {DEFAULT_APP_CODE}）: ")
            if app_code_input.strip():
                app_code = app_code_input.strip()
            else:
                app_code = DEFAULT_APP_CODE
            print(f"使用APP_CODE: {app_code}")
        except EOFError:
            app_code = DEFAULT_APP_CODE

    if login_device_info is None:
        try:
            login_device_info_input = input(f"请输入LOGIN_DEVICE_INFO（默认: {DEFAULT_LOGIN_DEVICE_INFO}）: ")
            if login_device_info_input.strip():
                login_device_info = login_device_info_input.strip()
            else:
                login_device_info = DEFAULT_LOGIN_DEVICE_INFO
            print(f"使用LOGIN_DEVICE_INFO: {login_device_info}")
        except EOFError:
            login_device_info = DEFAULT_LOGIN_DEVICE_INFO

    current_config = {
        'username': username,
        'password': password,
        'sso_url': sso_url,
        'app_url': app_url,
        'proxy': proxy,
        'app_code': app_code,
        'login_device_info': login_device_info
    }

    needs_save = False
    if (saved_config['username'] is None and username) or \
            (saved_config['password'] is None and password) or \
            (saved_config['sso_url'] is None and sso_url) or \
            (saved_config['app_url'] is None and app_url) or \
            (saved_config['app_code'] is None and app_code) or \
            (saved_config['login_device_info'] is None and login_device_info):
        needs_save = True
    else:
        for key in ['username', 'password', 'sso_url', 'app_url', 'proxy', 'app_code', 'login_device_info']:
            if saved_config.get(key) != current_config.get(key):
                needs_save = True
                break

    if needs_save:
        save_config(current_config)

    print("\n=== 开始登录流程 ===")

    print("1. 获取验证码...")
    image_base64, pic_code_id = get_captcha(sso_url, proxy)
    if not image_base64 or not pic_code_id:
        print("获取验证码失败")
        sys.exit(1)
    print(f"   获取成功，picCodeId: {pic_code_id}")

    print("2. 识别验证码...")
    img_code = recognize_captcha(image_base64, ocr_server, ocr_proxy)
    if not img_code:
        print("验证码识别失败")
        sys.exit(1)
    print(f"   识别结果: {img_code}")

    print("3. 登录...")
    result = login(sso_url, username, password, img_code, pic_code_id, proxy, app_code, login_device_info)
    if result:
        print(f"\n登录结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        resp_code = result.get('resp_code')
        if resp_code == 200:
            print("\n✅ 登录成功！")
        else:
            print(f"\n❌ 登录失败: {result.get('resp_msg')}")
    else:
        print("\n登录请求失败")


if __name__ == "__main__":
    main()
