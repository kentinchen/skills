import argparse
import getpass
import os

import requests
import yaml
from bs4 import BeautifulSoup


def get_auth_config_path():
    home_dir = os.path.expanduser("~")
    cpolar_dir = os.path.join(home_dir, ".cpolar")
    return os.path.join(cpolar_dir, "auth.yaml")


def read_auth_config():
    config_path = get_auth_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and 'username' in config and 'password' in config:
                    return config['username'], config['password']
        except Exception:
            pass
    return None, None


def save_auth_config(username, password):
    config_path = get_auth_config_path()
    cpolar_dir = os.path.dirname(config_path)

    if not os.path.exists(cpolar_dir):
        os.makedirs(cpolar_dir)

    config = {
        'username': username,
        'password': password
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    return config_path


# 登录cpolar dashboard
def login_cpolar(username, password, debug=False):
    login_url = "https://dashboard.cpolar.com/login"
    session = requests.Session()

    # 添加请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 获取登录页面，获取csrf token
    response = session.get(login_url, headers=headers)
    if debug:
        print(f"获取登录页面状态码: {response.status_code}")
        print(f"登录页面URL: {response.url}")

    # 保存页面内容到文件以便分析
    if debug:
        with open('login_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("登录页面内容已保存到login_page.html")

    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找csrf token
    csrf_token = None

    # 方法1: 查找name为csrf_token的input
    for input_tag in soup.find_all('input'):
        if input_tag.get('name') == 'csrf_token':
            csrf_token = input_tag.get('value')
            break

    # 方法2: 如果方法1失败，尝试查找meta标签中的csrf token
    if not csrf_token:
        meta_tag = soup.find('meta', {'name': 'csrf-token'})
        if meta_tag:
            csrf_token = meta_tag.get('content')

    # 方法3: 如果方法2失败，尝试从脚本中提取
    if not csrf_token:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'csrf_token' in script.string:
                # 尝试从脚本中提取token
                import re
                match = re.search(r'csrf_token"\s*value="([^"]+)"', str(script))
                if match:
                    csrf_token = match.group(1)
                    break

    if debug:
        print(f"获取到的csrf token: {csrf_token}")

    if not csrf_token:
        if debug:
            print("无法获取csrf token")
        return None

    # 构造登录数据
    login_data = {
        'csrf_token': csrf_token,
        'login': username,
        'password': password
    }

    # 提交登录请求
    response = session.post(login_url, data=login_data, headers=headers)

    if debug:
        print(f"登录请求状态码: {response.status_code}")
        print(f"登录请求URL: {response.url}")
        print(f"登录请求响应内容长度: {len(response.text)}")

    # 保存响应内容到文件以便分析
    if debug:
        with open('login_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("登录响应内容已保存到login_response.html")

    # 检查登录是否成功
    if response.status_code == 200 and "dashboard" in response.url:
        if debug:
            print("登录成功")
        return session
    elif response.status_code == 302:
        # 处理重定向
        redirect_url = response.headers.get('Location')
        if debug:
            print(f"重定向到: {redirect_url}")
        if redirect_url and "dashboard" in redirect_url:
            if debug:
                print("登录成功")
            return session
        else:
            if debug:
                print("登录失败: 重定向到非dashboard页面")
            return None
    else:
        if debug:
            print(f"登录失败: 状态码 {response.status_code}")
        return None


# 获取状态页面并提取ssh隧道的URL
def get_ssh_tunnel_url(session, debug=False):
    status_url = "https://dashboard.cpolar.com/status"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = session.get(status_url, headers=headers)

    if debug:
        print(f"获取状态页面状态码: {response.status_code}")
        print(f"状态页面URL: {response.url}")

    # 保存页面内容到文件以便分析
    if debug:
        with open('status_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("状态页面内容已保存到status_page.html")

    if response.status_code != 200:
        if debug:
            print("无法访问状态页面")
        return None

    # 解析页面内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找隧道列表
    tunnel_table = soup.find('table', class_='table table-sm')
    if not tunnel_table:
        # 尝试查找其他可能的隧道列表
        if debug:
            print("无法找到class为table table-sm的隧道列表，尝试查找其他可能的元素")
            # 查找所有table元素
            tables = soup.find_all('table')
            print(f"找到 {len(tables)} 个table元素")
            for i, table in enumerate(tables):
                print(f"Table {i} class: {table.get('class')}")
        return None

    # 遍历隧道行
    for row in tunnel_table.find_all('tr')[1:]:  # 跳过表头
        columns = row.find_all(['td', 'th'])
        if len(columns) >= 4:
            tunnel_name = columns[0].text.strip()
            if tunnel_name == 'ssh':
                # 公网URL在第2列（索引1）
                url_element = columns[1].find('a')
                if url_element:
                    url = url_element.text.strip()
                    if debug:
                        print(f"找到ssh隧道公网URL: {url}")
                    return url
                else:
                    # 如果没有a标签，直接获取文本
                    url = columns[1].text.strip()
                    if debug:
                        print(f"找到ssh隧道URL: {url}")
                    return url

    if debug:
        print("未找到ssh隧道")
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='登录cpolar dashboard并获取ssh隧道URL')
    parser.add_argument('username', nargs='?', help='cpolar用户名')
    parser.add_argument('password', nargs='?', help='cpolar密码')
    parser.add_argument('-d', '--debug', action='store_true', help='打印详细信息')
    args = parser.parse_args()

    debug = args.debug

    saved_username, saved_password = read_auth_config()

    if args.username:
        username = args.username
    elif saved_username:
        username = saved_username
        print(f"使用保存的用户名: {username}")
    else:
        username = input("请输入cpolar用户名: ")

    if args.password:
        password = args.password
    elif saved_password:
        password = saved_password
        print("使用保存的密码")
    else:
        password = getpass.getpass("请输入cpolar密码: ")

    session = login_cpolar(username, password, debug)

    if session:
        ssh_url = get_ssh_tunnel_url(session, debug)
        if ssh_url:
            print(ssh_url)
            if not saved_username:
                config_path = save_auth_config(username, password)
                print(f"凭据已保存到: {config_path}")
        else:
            if debug:
                print("无法获取ssh隧道URL")
    else:
        if debug:
            print("登录失败，无法继续")
