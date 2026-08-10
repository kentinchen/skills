import argparse
import re
import subprocess
import sys


def parse_tcp_url(url):
    """解析公网地址，提取主机和端口"""
    pattern = r'^tcp://([^:]+):(\d+)$'
    match = re.match(pattern, url)
    if not match:
        print(f"无效的公网地址格式: {url}")
        print("正确格式应为: tcp://host:port")
        sys.exit(1)
    host = match.group(1)
    port = match.group(2)
    return host, port


def parse_forward_param(param):
    """解析本地转发参数，格式: local_port:target_host:target_port"""
    pattern = r'^(\d+):([^:]+):(\d+)$'
    match = re.match(pattern, param)
    if not match:
        print(f"无效的转发参数格式: {param}")
        print("正确格式应为: local_port:target_host:target_port")
        print("例如: 33895:172.63.132.33:3389")
        sys.exit(1)
    local_port = match.group(1)
    target_host = match.group(2)
    target_port = match.group(3)
    return local_port, target_host, target_port


def build_identity_option(identity_file):
    """构建 SSH 密钥参数"""
    if identity_file:
        # -i 指定私钥，-o IdentitiesOnly=yes 防止客户端尝试其他密钥
        return f'-i "{identity_file}" -o IdentitiesOnly=yes '
    return ''


def create_port_forward(tcp_address, forward_param, identity_file=None):
    """创建SSH本地端口转发"""
    # 解析参数
    tunnel_host, tunnel_port = parse_tcp_url(tcp_address)
    local_port, target_host, target_port = parse_forward_param(forward_param)

    identity_opt = build_identity_option(identity_file)

    # 构建SSH命令 - 使用-L参数进行本地端口转发
    ssh_command = (
        f'ssh -o StrictHostKeyChecking=no '
        f'{identity_opt}'
        f'-L {local_port}:{target_host}:{target_port} '
        f'-N '
        f'-p {tunnel_port} root@{tunnel_host}'
    )

    print(f"正在创建SSH本地端口转发: {ssh_command}")
    print(f"转发规则: 127.0.0.1:{local_port} -> {target_host}:{target_port} (通过 {tunnel_host}:{tunnel_port})")
    if identity_file:
        print(f"使用本地密钥: {identity_file}")

    # 在后台执行SSH命令
    try:
        if sys.platform == 'win32':
            # Windows平台
            subprocess.Popen(
                ['cmd.exe', '/c', ssh_command],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            # Linux/Mac平台
            subprocess.Popen(
                ssh_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        print("SSH本地端口转发已在后台启动")
        print(f"现在可以通过访问 127.0.0.1:{local_port} 来访问 {target_host}:{target_port}")
        return True
    except Exception as e:
        print(f"创建端口转发失败: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='通过cpolar隧道创建SSH本地端口转发',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python port_forward_script.py tcp://12.tcp.vip.cpolar.cn:10328 33895:172.63.132.33:3389\n'
            '  python port_forward_script.py tcp://12.tcp.vip.cpolar.cn:10328 33895:172.63.132.33:3389 -i ~/.ssh/id_rsa\n'
        )
    )
    parser.add_argument('public_url', help='公网地址，格式: tcp://host:port')
    parser.add_argument('forward_param', help='转发参数，格式: local_port:target_host:target_port')
    parser.add_argument('-i', '--identity', help='SSH私钥路径，使用本地密钥登录（如 C:\\Users\\xxx\\.ssh\\id_rsa 或 ~/.ssh/id_rsa）')
    args = parser.parse_args()

    create_port_forward(args.public_url, args.forward_param, args.identity)
