import json
import os
import requests
import sys

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'nazha_config.json')


class NazhaBase:
    def __init__(self, base_url=None, username=None, password=None, token=None, pat_token=None):
        self._base_url = base_url
        self._username = username
        self._password = password
        self._token = token
        self._pat_token = pat_token
        self._session = requests.Session()
        self._session.verify = False
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    def get_base_url(self):
        return self._base_url

    def get_token(self):
        return self._token

    def _get_headers(self):
        headers = {
            'Content-Type': 'application/json',
        }
        if self._pat_token:
            headers['Authorization'] = f'Bearer {self._pat_token}'
        elif self._token:
            headers['Authorization'] = f'Bearer {self._token}'
        return headers

    def _request(self, method, path, params=None, data=None, json_data=None, retry=True):
        url = f'{self._base_url}{path}'
        headers = self._get_headers()

        try:
            if method == 'GET':
                response = self._session.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = self._session.post(url, headers=headers, params=params, data=data, json=json_data)
            elif method == 'PUT':
                response = self._session.put(url, headers=headers, params=params, data=data, json=json_data)
            elif method == 'PATCH':
                response = self._session.patch(url, headers=headers, params=params, data=data, json=json_data)
            elif method == 'DELETE':
                response = self._session.delete(url, headers=headers, params=params)
            else:
                print(f'不支持的请求方法: {method}')
                return None

            if response.status_code == 401 and retry and not self._pat_token:
                print('Token已过期，尝试重新登录...')
                if self._username and self._password:
                    if self.login():
                        self.save_config()
                        return self._request(method, path, params, data, json_data, retry=False)
                    else:
                        print('重新登录失败')
                else:
                    print('没有保存用户名密码，无法自动重新登录')
                return None

            try:
                result = response.json()
            except Exception:
                print(f'响应不是JSON格式: {response.text}')
                return None

            return result
        except Exception as e:
            print(f'请求异常: {e}')
            return None

    def login(self):
        url = f'{self._base_url}/api/v1/login'
        payload = {
            'username': self._username,
            'password': self._password
        }

        try:
            response = self._session.post(url, json=payload, headers={'Content-Type': 'application/json'})
            result = response.json()

            if result.get('success'):
                data = result.get('data')
                if data:
                    self._token = data.get('token')
                    print(f'登录成功，Token已获取')
                    return True
                print('登录响应中无data字段')
            else:
                print(f'登录失败: {result.get("error", "未知错误")}')
        except Exception as e:
            print(f'登录请求异常: {e}')

        return False

    def save_config(self):
        config_dir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config = {
            'base_url': self._base_url,
            'username': self._username,
            'password': self._password,
            'token': self._token,
            'pat_token': self._pat_token
        }

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f'配置已保存到: {CONFIG_FILE}')

    @classmethod
    def load_config(cls):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return cls(
                base_url=config.get('base_url'),
                username=config.get('username'),
                password=config.get('password'),
                token=config.get('token'),
                pat_token=config.get('pat_token')
            )
        return None

    def get_server_list(self, offset=0, limit=100):
        params = {
            'offset': offset,
            'limit': limit
        }
        result = self._request('GET', '/api/v1/server', params=params)
        if result and result.get('success'):
            return result.get('data')
        return None

    def get_setting(self):
        result = self._request('GET', '/api/v1/setting')
        if result and result.get('success'):
            return result.get('data')
        return None