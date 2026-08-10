import argparse
import re
import subprocess
import sys


def build_identity_option(identity_file):
    """构建 SSH 密钥参数"""
    if identity_file:
        return f'-i "{identity_file}" -o IdentitiesOnly=yes '
    return ''


def create_ssh_proxy(tcp_address, local_port=20808, identity_file=None):
    # 解析公网地址，提取主机和端口
    pattern = r'tcp://([^:]+):(\d+)'
    match = re.match(pattern, tcp_address)
    if not match:
        print("无效的公网地址格式，请使用 tcp://host:port 格式")
        return False

    host = match.group(1)
    port = match.group(2)

    identity_opt = build_identity_option(identity_file)

    # 构建SSH命令
    ssh_command = (
        f'ssh -o StrictHostKeyChecking=no '
        f'{identity_opt}'
        f'-N -D {local_port} '
        f'-p {port} root@{host}'
    )

    print(f"正在创建SSH动态代理: {ssh_command}")
    if identity_file:
        print(f"使用本地密钥: {identity_file}")

    # 在后台执行SSH命令
    try:
        # 使用subprocess在后台执行命令
        if sys.platform == 'win32':
            # Windows平台
            subprocess.Popen(['cmd.exe', '/c', ssh_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            # Linux/Mac平台
            subprocess.Popen(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("SSH动态代理已在后台启动")
        print(f"本地SOCKS5代理: 127.0.0.1:{local_port}")
        return True
    except Exception as e:
        print(f"创建代理失败: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='通过cpolar隧道创建SSH动态SOCKS5代理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python dynamic_proxy_script.py tcp://host:port\n'
            '  python dynamic_proxy_script.py tcp://host:port 8888\n'
            '  python dynamic_proxy_script.py tcp://host:port 8888 -i ~/.ssh/id_rsa\n'
        )
    )
    parser.add_argument('public_url', help='公网地址，格式: tcp://host:port')
    parser.add_argument('local_port', nargs='?', type=int, default=20808, help='本地监听端口，默认20808')
    parser.add_argument('-i', '--identity', help='SSH私钥路径，使用本地密钥登录（如 C:\\Users\\xxx\\.ssh\\id_rsa 或 ~/.ssh/id_rsa）')
    args = parser.parse_args()

    create_ssh_proxy(args.public_url, args.local_port, args.identity)
