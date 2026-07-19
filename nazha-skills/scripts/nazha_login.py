#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nazha_base import NazhaBase


def main():
    if len(sys.argv) < 4:
        print('用法: python nazha_login.py <base_url> <username> <password>')
        print('示例: python nazha_login.py http://localhost:8008 admin admin')
        sys.exit(1)

    base_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    client = NazhaBase(base_url=base_url, username=username, password=password)

    if client.login():
        client.save_config()
        print('登录成功！')
    else:
        print('登录失败！')
        sys.exit(1)


if __name__ == '__main__':
    main()