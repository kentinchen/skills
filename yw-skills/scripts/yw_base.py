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
from sso_utils import (
    DEFAULT_SSO_URL, DEFAULT_APP_URL, DEFAULT_APP_CODE, DEFAULT_LOGIN_DEVICE_INFO,
    read_config, read_ocr_config, save_config, get_timestamp, get_common_headers,
    get_public_key, get_captcha, rsa_encrypt, recognize_captcha, login
)


class YwBase:
    def __init__(self):
        self._token = None
        self._sso_token = None
        self._auth_token_key = None
        self._jsessionid = None
        self._user_id = None
        self._tenant_code = None
        self._config = read_config()
        self._session = requests.Session()

    @property
    def config(self):
        return self._config

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def sso_token(self):
        return self._sso_token

    @sso_token.setter
    def sso_token(self, value):
        self._sso_token = value

    def get_proxy(self):
        return self._config.get('proxy')

    def get_sso_url(self):
        return self._config.get('sso_url') or DEFAULT_SSO_URL

    def get_app_url(self):
        return self._config.get('app_url') or DEFAULT_APP_URL
    
    def get_cookie_header(self):
        cookie_parts = []
        if self._auth_token_key:
            cookie_parts.append(f"auth_token_key={self._auth_token_key}")
        if self._sso_token:
            cookie_parts.append(f"sso_token={self._sso_token}")
        if self._token:
            cookie_parts.append(f"YH-TOKEN={self._token}")
        if self._jsessionid:
            cookie_parts.append(f"JSESSIONID={self._jsessionid}")
        return "; ".join(cookie_parts) if cookie_parts else None

    def get_auth_headers(self):
        headers = {
            'language': 'zh',
            'noviceGuidance': 'false',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._token}'
        }
        cookie = self.get_cookie_header()
        if cookie:
            headers['Cookie'] = cookie
        if self._sso_token:
            headers['Authentication'] = f'Bearer {self._sso_token}'
        if self._tenant_code:
            headers['tenant-code'] = self._tenant_code
        return headers


    def exchange_app_token(self, art, sso_token, app_code=DEFAULT_APP_CODE):
        app_url = self.get_app_url()
        proxy = self.get_proxy()

        url = f"{app_url}/api-auth/oauth/user/doLogin"
        params = {
            'sp': app_code,
            'art': art,
            'type': 1,
            '_t': get_timestamp()
        }

        headers = {
            'Content-Type': 'application/json',
            'Authentication': f'{sso_token}'
        }

        proxies = {"http": proxy, "https": proxy} if proxy else None

        try:
            response = self._session.post(url, params=params, headers=headers, proxies=proxies, verify=False)
            result = response.json()
            print(f"APP登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

            if result.get('code') == 200:
                data = result.get('datas') or result.get('data')
                if data:
                    app_token = data.get('token')
                    user_id = data.get('id') or data.get('userId')
                    if app_token:
                        print(f"获取到APP token: {app_token[:20]}...")
                        self._token = app_token
                        self._sso_token = app_token
                        if user_id:
                            self._user_id = user_id

                        for cookie in response.cookies:
                            if cookie.name == 'JSESSIONID':
                                self._jsessionid = cookie.value
                                self._config['jsessionid'] = cookie.value
                            elif cookie.name == 'auth_token_key':
                                self._auth_token_key = cookie.value
                                self._config['auth_token_key'] = cookie.value

                        return app_token
                    print("APP登录成功，但未获取到token")
                else:
                    print("APP登录成功，但未获取到数据")
            else:
                print(f"APP登录失败: {result.get('msg')}")
        except Exception as e:
            print(f"APP登录异常: {e}")

        return None

    def sso_login(self, sso_url, username, password, proxy=None, app_code=DEFAULT_APP_CODE,
                  login_device_info=DEFAULT_LOGIN_DEVICE_INFO):
        ocr_server, ocr_proxy = read_ocr_config()
        if not ocr_server:
            ocr_server = "http://localhost:8000"

        print("1. 获取验证码...")
        image_base64, pic_code_id = get_captcha(sso_url, proxy)
        if not image_base64 or not pic_code_id:
            print("验证码获取失败")
            return None

        print("2. 识别验证码...")
        img_code = recognize_captcha(image_base64, ocr_server, ocr_proxy)
        if not img_code:
            print("验证码识别失败")
            return None

        print("3. SSO登录...")
        result = login(sso_url, username, password, img_code, pic_code_id, proxy, app_code, login_device_info)
        if result and result.get('resp_code') == 200:
            datas = result.get('datas')
            print(f"SSO登录成功，完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            if datas:
                sso_token = datas.get('token')
                art = datas.get('art')
                self._user_id = datas.get('userId')
                
                if sso_token:
                    print(f"获取到SSO token: {sso_token}...")
                    
                    print("4. 换取APP token...")
                    app_token = self.exchange_app_token(art, sso_token, app_code)
                    if app_token:
                        current_config = self._config.copy()
                        current_config['token'] = self._token
                        current_config['sso_token'] = self._sso_token
                        current_config['user_id'] = self._user_id
                        save_config(current_config)
                        self._config = current_config
                        
                        print(f"获取到userId: {self._user_id}")
                        return self._token
                    else:
                        print("无法获取APP token，使用SSO token")
                        self._token = sso_token
                        current_config = self._config.copy()
                        current_config['token'] = self._token
                        current_config['sso_token'] = self._sso_token
                        current_config['user_id'] = self._user_id
                        save_config(current_config)
                        self._config = current_config
                        return self._token
                else:
                    print("SSO登录成功，但未获取到token")
        else:
            print(f"SSO登录失败: {result.get('resp_msg') if result else '未知错误'}")

        return None

    def get_token(self, force_login=False):
        if not force_login and self._token:
            return self._token

        if not force_login:
            self._token = self._config.get('token')
            self._sso_token = self._config.get('sso_token')
            self._auth_token_key = self._config.get('auth_token_key')
            self._jsessionid = self._config.get('jsessionid')
            self._user_id = self._config.get('user_id')
            self._tenant_code = self._config.get('tenant_code')
            if self._token:
                print(f"使用保存的token: {self._token[:20]}...")
                return self._token

        username = self._config.get('username')
        password = self._config.get('password')
        sso_url = self.get_sso_url()
        proxy = self.get_proxy()
        app_code = self._config.get('app_code') or DEFAULT_APP_CODE
        login_device_info = self._config.get('login_device_info') or DEFAULT_LOGIN_DEVICE_INFO

        if not username or not password:
            print("错误: 配置文件中缺少用户名或密码")
            sys.exit(1)

        token = self.sso_login(sso_url, username, password, proxy, app_code, login_device_info)
        if token:
            self._token = token

        return self._token

    def call_api(self, url, method='get', headers=None, params=None, json_data=None, proxy=None):
        if proxy is None:
            proxy = self.get_proxy()

        proxies = {"http": proxy, "https": proxy} if proxy else None

        auth_headers = self.get_auth_headers()
        if headers:
            auth_headers.update(headers)

        try:
            if method.lower() == 'get':
                response = self._session.get(url, headers=auth_headers, params=params, proxies=proxies, verify=False)
            elif method.lower() == 'post':
                response = self._session.post(url, headers=auth_headers, params=params, json=json_data, proxies=proxies, verify=False)
            else:
                print(f"不支持的HTTP方法: {method}")
                return None

            for cookie in response.cookies:
                if cookie.name == 'JSESSIONID':
                    self._jsessionid = cookie.value
                    self._config['jsessionid'] = cookie.value
                elif cookie.name == 'auth_token_key':
                    self._auth_token_key = cookie.value
                    self._config['auth_token_key'] = cookie.value

            save_config(self._config)

            return response.json()
        except Exception as e:
            print(f"API调用异常: {e}")
            return None
