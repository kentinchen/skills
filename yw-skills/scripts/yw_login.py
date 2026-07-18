import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yw_base import YwBase
from sso_utils import (
    read_config, save_config, read_ocr_config, save_ocr_config,
    get_ocr_server_and_proxy, DEFAULT_SSO_URL, DEFAULT_APP_URL,
    DEFAULT_APP_CODE, DEFAULT_LOGIN_DEVICE_INFO
)


def main():
    parser = None
    import argparse
    parser = argparse.ArgumentParser(description="yw-skills SSO登录脚本")
    parser.add_argument('--proxy', help='代理地址')
    parser.add_argument('--sso-url', '--sso_url', help='SSO服务地址')
    parser.add_argument('--username', help='用户名')
    parser.add_argument('--password', help='密码')
    parser.add_argument('--app-url', '--app_url', help='APP服务地址')
    parser.add_argument('--app-code', '--app_code', help='APP_CODE')
    parser.add_argument('--login-device-info', '--login_device_info', help='LOGIN_DEVICE_INFO')
    parser.add_argument('--ocr-server', '--ocr_server', help='OCR服务地址')
    parser.add_argument('--ocr-proxy', '--ocr_proxy', help='OCR代理地址')
    parser.add_argument('--force-login', '--force_login', action='store_true', help='强制重新登录')
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

    yw = YwBase()
    yw._config = {**yw._config, **current_config}

    print("\n=== 开始yw系统登录流程 ===")

    token = yw.get_token(force_login=args.force_login if args else False)

    if token:
        print(f"\n✅ 登录成功！")
        print(f"   Token: {token}...")
        
        result = {
            'success': True,
            'token': token,
            'sso_token': yw.sso_token,
            'message': '登录成功'
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n❌ 登录失败")
        result = {
            'success': False,
            'message': '登录失败'
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()