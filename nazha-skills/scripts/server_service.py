#!/usr/bin/env python3
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nazha_base import NazhaBase


def print_server_list(servers):
    if not servers:
        print('未找到服务器')
        return

    if isinstance(servers, dict):
        value = servers.get('value', [])
    else:
        value = servers

    total = len(value)
    print(f'服务器列表（共 {total} 台）:')
    print('-' * 110)
    print(f'{"ID":<8} {"名称":<20} {"IP":<20} {"状态":<10} {"CPU":<8} {"内存":<10} {"磁盘":<10}')
    print('-' * 110)

    for server in value:
        server_id = server.get('id', '')
        name = server.get('name', '')
        
        geoip = server.get('geoip', {})
        ip_info = geoip.get('ip', {})
        ip = ip_info.get('ipv4_addr', '')
        
        state = server.get('state', {})
        cpu = state.get('cpu', 0) * 100
        
        host = server.get('host', {})
        mem_total = host.get('mem_total', 1)
        mem_used = state.get('mem_used', 0)
        memory = (mem_used / mem_total) * 100 if mem_total > 0 else 0
        
        disk_total = host.get('disk_total', 1)
        disk_used = state.get('disk_used', 0)
        disk = (disk_used / disk_total) * 100 if disk_total > 0 else 0
        
        last_active = server.get('last_active')
        status = '在线' if state and last_active else '离线'

        print(f'{server_id:<8} {name:<20} {ip:<20} {status:<10} {cpu:>6.1f}% {memory:>7.1f}% {disk:>7.1f}%')

    print('-' * 110)


def main():
    client = NazhaBase.load_config()

    if not client:
        print('未找到配置，请先运行登录脚本')
        print('用法: python nazha_login.py <base_url> <username> <password>')
        sys.exit(1)

    if not client.get_token():
        print('配置中没有Token，请先运行登录脚本')
        sys.exit(1)

    servers = client.get_server_list()

    if servers:
        print_server_list(servers)
    else:
        print('获取服务器列表失败')
        sys.exit(1)


if __name__ == '__main__':
    main()