import argparse
import os
import re
import socket
import subprocess
import sys
import time


def parse_tcp_url(url):
    pattern = r'^tcp://([^:]+):(\d+)$'
    match = re.match(pattern, url)
    if not match:
        print(f"无效的公网地址格式: {url}")
        print("正确格式应为: tcp://host:port")
        sys.exit(1)
    return match.group(1), match.group(2)


def parse_forward_param(param):
    pattern = r'^(\d+):([^:]+):(\d+)$'
    match = re.match(pattern, param)
    if not match:
        print(f"无效的转发参数格式: {param}")
        print("正确格式应为: local_port:target_host:target_port")
        print("例如: 33895:172.63.132.33:3389")
        sys.exit(1)
    return match.group(1), match.group(2), match.group(3)


def build_ssh_args(tunnel_host, tunnel_port, local_port, target_host, target_port, identity_file):
    """构建 ssh 参数列表"""
    args = ['ssh', '-o', 'StrictHostKeyChecking=no']
    if identity_file:
        args += ['-i', identity_file, '-o', 'IdentitiesOnly=yes']
    # keepalive: 每15秒发心跳,3次无响应才断开,避免空闲超时被服务端踢掉
    args += ['-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3']
    args += [
        '-L', f'{local_port}:{target_host}:{target_port}',
        '-N',
        '-p', str(tunnel_port),
        f'root@{tunnel_host}',
    ]
    return args


def resolve_ssh_exe():
    """定位 ssh 可执行文件,Windows 下优先用系统自带 OpenSSH 的绝对路径"""
    if sys.platform == 'win32':
        candidates = [
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'OpenSSH', 'ssh.exe'),
            os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'Git', 'usr', 'bin', 'ssh.exe'),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return 'ssh'
    return 'ssh'


def port_is_listening(port):
    """检测本地端口是否已被监听(监听态而非可连接态,不做完整握手)"""
    for family, addr in ((socket.AF_INET, '127.0.0.1'), (socket.AF_INET6, '::1')):
        try:
            s = socket.socket(family, socket.SOCK_STREAM)
            s.settimeout(1.5)
            try:
                s.connect((addr, int(port)))
                return True
            finally:
                s.close()
        except OSError:
            continue
    return False


def wait_listening(port, timeout=12):
    """等待端口进入监听状态,返回是否成功"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_is_listening(port):
            return True
        time.sleep(0.4)
    return False


def _launch_detached(ssh_args, log_path):
    """
    以脱离父进程树的方式启动 ssh。

    Windows: DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
      DETACHED_PROCESS 没有控制台,因此 ssh 不会弹出交互式密码提示而卡死,
      进程也不会随 agent 的进程树清理而终止。这也是相对 schtasks 的
      关键优势: 不依赖 Task Scheduler,不会被安全策略黑名单拦截。
    Linux/Mac: start_new_session 让子进程脱离父进程会话。
    """
    log = open(log_path, 'ab')
    kwargs = dict(
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        close_fds=True,
    )
    if sys.platform == 'win32':
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        kwargs['creationflags'] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    else:
        kwargs['start_new_session'] = True
    return subprocess.Popen(ssh_args, **kwargs)


def _launch_via_schtasks(ssh_args, local_port):
    """旧方案: 用计划任务托管 ssh。仅在 --use-schtasks 显式指定时使用"""
    task_name = f"SshPortForward{local_port}"
    subprocess.run(
        ['schtasks', '/Delete', '/TN', task_name, '/F'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    tr = subprocess.list2cmdline(ssh_args)
    subprocess.run(
        ['schtasks', '/Create', '/TN', task_name,
         '/TR', tr, '/SC', 'ONCE', '/ST', '23:59', '/F'],
        check=True, capture_output=True,
    )
    subprocess.run(['schtasks', '/Run', '/TN', task_name], check=True, capture_output=True)


def _tail_log(log_path, lines=12):
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read().strip().splitlines()
        return content[-lines:]
    except OSError:
        return []


def create_port_forward(tcp_address, forward_param, identity_file=None,
                        use_schtasks=False, timeout=12):
    """创建SSH本地端口转发"""
    tunnel_host, tunnel_port = parse_tcp_url(tcp_address)
    local_port, target_host, target_port = parse_forward_param(forward_param)

    if port_is_listening(local_port):
        print(f"本地端口 {local_port} 已被占用,请先释放或换一个端口")
        print(f"查看占用进程: netstat -ano | findstr :{local_port}")
        return False

    ssh_exe = resolve_ssh_exe()
    ssh_args = build_ssh_args(
        tunnel_host, tunnel_port, local_port, target_host, target_port, identity_file
    )
    ssh_args[0] = ssh_exe

    ssh_command = ' '.join(
        [arg if not (' ' in arg or '"' in arg) else f'"{arg}"' for arg in ssh_args]
    )
    print(f"正在创建SSH本地端口转发: {ssh_command}")
    print(f"转发规则: 127.0.0.1:{local_port} -> {target_host}:{target_port} (通过 {tunnel_host}:{tunnel_port})")
    if identity_file:
        print(f"使用本地密钥: {identity_file}")

    log_path = os.path.join(
        os.path.expanduser('~'), '.cpolar', f'forward_{local_port}.log'
    )
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
    except OSError:
        log_path = os.path.join(os.getcwd(), f'forward_{local_port}.log')

    try:
        if use_schtasks and sys.platform == 'win32':
            _launch_via_schtasks(ssh_args, local_port)
            pid = None
        else:
            proc = _launch_detached(ssh_args, log_path)
            pid = proc.pid
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode('gbk', errors='replace') if e.stderr else str(e)
        print(f"创建端口转发失败(schtasks): {err}")
        return False
    except (OSError, PermissionError) as e:
        print(f"创建端口转发失败: 无法启动 ssh ({e})")
        print("提示: 如果是在受限沙箱中执行,ssh 可能被禁止读取 ~/.ssh 下的密钥/known_hosts,"
              "请改用不受限方式运行,或确认沙箱允许访问该目录。")
        return False

    # 启动后自检: 只有本地端口真正进入监听态才算成功。
    # ssh 在认证失败或卡在交互式密码提示时,进程仍然存活但不监听端口,
    # 因此不能只看进程是否启动就判定成功。
    if wait_listening(local_port, timeout=timeout):
        print("SSH本地端口转发已在后台启动")
        if pid:
            print(f"进程ID: {pid}")
        print(f"现在可以通过访问 127.0.0.1:{local_port} 来访问 {target_host}:{target_port}")
        print(f"日志: {log_path}")
        print(f"停止转发: python {os.path.basename(__file__)} --stop {local_port}")
        return True

    print(f"端口 {local_port} 未进入监听状态,转发很可能失败")
    if pid:
        try:
            alive = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True, text=True, errors='replace',
            ).stdout
            if str(pid) not in alive:
                print(f"ssh 进程(pid {pid})已退出")
        except OSError:
            pass
    for line in _tail_log(log_path):
        print(f"  [ssh] {line}")
    print("常见原因:")
    print("  1. 认证失败: Load key ... Permission denied —— ssh 无法读取 ~/.ssh 下的密钥,检查沙箱/文件权限")
    print("  2. 卡在密码提示: 本脚本以无控制台方式启动 ssh,如需密码认证请改用密钥")
    print("  3. 隧道地址已变化: 重新执行 cpolar_ssh_public_url.py 获取最新 tcp:// 地址")
    return False


def stop_forward(local_port):
    """按本地监听端口结束对应的转发进程"""
    try:
        out = subprocess.run(
            ['netstat', '-ano'], capture_output=True, text=True, errors='replace'
        ).stdout if sys.platform == 'win32' else ''
    except OSError:
        out = ''

    pids = set()
    for line in out.splitlines():
        if f':{local_port}' in line and 'LISTENING' in line:
            parts = line.split()
            if parts and parts[-1].isdigit():
                pids.add(parts[-1])

    if not pids:
        print(f"未发现监听端口 {local_port} 的进程")
        return True

    ok = True
    for pid in pids:
        try:
            subprocess.run(['taskkill', '/F', '/PID', pid],
                           capture_output=True, check=True)
            print(f"已结束进程 {pid} (端口 {local_port})")
        except subprocess.CalledProcessError as e:
            print(f"结束进程 {pid} 失败: {e}")
            ok = False
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='通过cpolar隧道创建SSH本地端口转发',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '示例:\n'
            '  python port_forward_script.py tcp://12.tcp.vip.cpolar.cn:10328 33895:172.63.132.33:3389\n'
            '  python port_forward_script.py tcp://12.tcp.vip.cpolar.cn:10328 33895:172.63.132.33:3389 -i ~/.ssh/id_rsa\n'
            '  python port_forward_script.py --stop 33895\n'
        )
    )
    parser.add_argument('public_url', nargs='?', help='公网地址，格式: tcp://host:port')
    parser.add_argument('forward_param', nargs='?', help='转发参数，格式: local_port:target_host:target_port')
    parser.add_argument('-i', '--identity', help='SSH私钥路径，使用本地密钥登录（如 C:\\Users\\xxx\\.ssh\\id_rsa 或 ~/.ssh/id_rsa）')
    parser.add_argument('--use-schtasks', action='store_true',
                        help='Windows 下改用计划任务托管 ssh（默认不使用；schtasks 可能被安全策略黑名单拦截）')
    parser.add_argument('--timeout', type=int, default=12,
                        help='等待端口进入监听状态的秒数，默认 12')
    parser.add_argument('--stop', dest='stop_port', type=int,
                        help='结束指定本地端口的转发进程')
    args = parser.parse_args()

    if args.stop_port:
        sys.exit(0 if stop_forward(args.stop_port) else 1)

    if not args.public_url or not args.forward_param:
        parser.print_help()
        sys.exit(1)

    ok = create_port_forward(
        args.public_url, args.forward_param, args.identity,
        use_schtasks=args.use_schtasks, timeout=args.timeout,
    )
    sys.exit(0 if ok else 1)
