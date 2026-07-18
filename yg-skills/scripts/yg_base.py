import json
import os
import sys

import requests

try:
    import socks
except ImportError:
    pass

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sso_utils import (
    DEFAULT_SSO_URL, DEFAULT_APP_URL, DEFAULT_APP_CODE, DEFAULT_LOGIN_DEVICE_INFO,
    read_config, read_ocr_config, get_captcha, recognize_captcha, login
)


class YgBase:
    def __init__(self):
        self._token = None
        self._config = read_config()

    @property
    def config(self):
        return self._config

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    def get_proxy(self):
        return self._config.get('proxy')

    def get_sso_url(self):
        return self._config.get('sso_url') or DEFAULT_SSO_URL

    def get_app_url(self):
        return self._config.get('app_url') or DEFAULT_APP_URL

    def get_user_info_by_art(self, art):
        app_url = self.get_app_url()
        proxy = self.get_proxy()

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

    def exchange_app_token(self, sso_token, username=None):
        art = sso_token
        app_username = self.get_user_info_by_art(art)

        if not app_username:
            print(f"无法通过loginByArt获取userName，使用传入的username: {username}")
            app_username = username
        if not app_username:
            print("错误: 缺少APP用户名")
            return None

        app_url = self.get_app_url()
        proxy = self.get_proxy()

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
                    self._token = app_token
                    return app_token
                print(f"APP登录成功，但未获取到token")
            else:
                print(f"APP登录失败: {result.get('msg')}")
        except Exception as e:
            print(f"APP登录异常: {e}")
        return None

    def sso_login(self, sso_url, username, password, proxy=None, app_code=DEFAULT_APP_CODE,
                  login_device_info=DEFAULT_LOGIN_DEVICE_INFO, app_username=None):
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
                    app_token = self.exchange_app_token(art, app_username)
                    if app_token:
                        return app_token
                    print("无法获取APP token")
                    return art
                elif token:
                    print(f"获取到SSO token: {token}...")
                    app_token = self.exchange_app_token(token, app_username)
                    if app_token:
                        return app_token
                    print("无法获取APP token，使用SSO token")
                    return token
            print(f"登录成功，但未获取到token")
        else:
            print(f"登录失败: {result.get('resp_msg') if result else '未知错误'}")

        return None

    def get_token(self, force_login=False, app_username=None):
        if not force_login and self._token:
            return self._token

        username = self._config.get('username')
        password = self._config.get('password')
        if app_username is None:
            app_username = self._config.get('app_username') or username
        sso_url = self.get_sso_url()
        proxy = self.get_proxy()
        app_code = self._config.get('app_code') or DEFAULT_APP_CODE
        login_device_info = self._config.get('login_device_info') or DEFAULT_LOGIN_DEVICE_INFO

        if not username or not password:
            print("错误: 配置文件中缺少用户名或密码")
            sys.exit(1)
        if not app_username:
            print("错误: 配置文件中缺少app_username")
            sys.exit(1)

        token = self.sso_login(sso_url, username, password, proxy, app_code, login_device_info, app_username)
        if token:
            self._token = token

        return self._token

    def call_api(self, url, method='get', headers=None, params=None, json_data=None, proxy=None):
        if proxy is None:
            proxy = self.get_proxy()

        proxies = {"http": proxy, "https": proxy} if proxy else None

        try:
            if method.lower() == 'get':
                response = requests.get(url, headers=headers, params=params, proxies=proxies, verify=False)
            elif method.lower() == 'post':
                response = requests.post(url, headers=headers, params=params, json=json_data, proxies=proxies, verify=False)
            else:
                print(f"不支持的HTTP方法: {method}")
                return None

            return response.json()
        except Exception as e:
            print(f"API调用异常: {e}")
            return None
