import argparse
import subprocess
import re
import sys
import socket
import threading
import yaml
import os

def get_servers_config_path():
    home_dir = os.path.expanduser("~")
    cpolar_dir = os.path.join(home_dir, ".cpolar")
    return os.path.join(cpolar_dir, "servers.yaml")

def read_servers_config():
    config_path = get_servers_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and isinstance(config, dict):
                    return config.get('host1'), config.get('port1', 22)
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    return None, None

def save_servers_config(host1, port1):
    config_path = get_servers_config_path()
    cpolar_dir = os.path.dirname(config_path)
    if not os.path.exists(cpolar_dir):
        os.makedirs(cpolar_dir)
    
    config = {
        'host1': host1,
        'port1': port1
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"配置已保存到: {config_path}")
    except Exception as e:
        print(f"保存配置文件失败: {e}")

# 解析公网地址，提取主机和端口
def parse_tcp_url(url):
    # 匹配 tcp://host:port 格式
    pattern = r'^tcp://([^:]+):(\d+)$'
    match = re.match(pattern, url)
    if not match:
        print(f"无效的公网地址格式: {url}")
        print("正确格式应为: tcp://host:port")
        sys.exit(1)
    host = match.group(1)
    port = match.group(2)
    return host, port

# SOCKS5代理连接器
def socks5_proxy_connect(host, port, proxy_host='127.0.0.1', proxy_port=20808):
    """通过SOCKS5代理连接到目标主机"""
    # 创建到SOCKS5代理的连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((proxy_host, proxy_port))
    
    # SOCKS5握手
    # 版本标识符(5) + 认证方法数量(1) + 认证方法(0=无认证)
    sock.sendall(b'\x05\x01\x00')
    # 接收服务器响应
    response = sock.recv(2)
    if response[0] != 5:  # 版本不匹配
        sock.close()
        return None
    if response[1] != 0:  # 认证方法不支持
        sock.close()
        return None
    
    # 构建请求: 版本(5) + 命令(1=连接) + 保留(0) + 地址类型(3=域名)
    # 地址长度 + 域名 + 端口
    host_bytes = host.encode('utf-8')
    request = b'\x05\x01\x00\x03' + bytes([len(host_bytes)]) + host_bytes
    request += port.to_bytes(2, byteorder='big')
    sock.sendall(request)
    
    # 接收响应
    response = sock.recv(4)
    if response[0] != 5:  # 版本不匹配
        sock.close()
        return None
    if response[1] != 0:  # 连接失败
        sock.close()
        return None
    
    # 跳过剩余的响应数据
    addr_type = response[3]
    if addr_type == 1:  # IPv4
        sock.recv(4)
    elif addr_type == 3:  # 域名
        length = ord(sock.recv(1))
        sock.recv(length)
    elif addr_type == 4:  # IPv6
        sock.recv(16)
    # 接收端口
    sock.recv(2)
    
    return sock

# 简单的代理服务器，用于SSH的ProxyCommand
def proxy_server(port, target_host, target_port):
    """启动一个简单的代理服务器，将流量通过SOCKS5代理转发到目标主机"""
    def handle_client(client_socket):
        try:
            # 通过SOCKS5代理连接到目标主机
            proxy_sock = socks5_proxy_connect(target_host, target_port)
            if not proxy_sock:
                client_socket.close()
                return
            
            # 双向转发数据
            def forward(src, dst):
                try:
                    while True:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.sendall(data)
                except:
                    pass
            
            # 启动两个线程进行双向转发
            thread1 = threading.Thread(target=forward, args=(client_socket, proxy_sock))
            thread2 = threading.Thread(target=forward, args=(proxy_sock, client_socket))
            thread1.start()
            thread2.start()
            thread1.join()
            thread2.join()
        finally:
            client_socket.close()
            if 'proxy_sock' in locals():
                proxy_sock.close()
    
    # 启动服务器
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', port))
    server.listen(1)
    print(f"代理服务器启动在 127.0.0.1:{port}")
    
    # 只处理一个连接，然后退出
    client_socket, addr = server.accept()
    handle_client(client_socket)
    server.close()

def start_ssh_proxy(command, is_first_proxy=False, dp1=20808):
    try:
        git_bash_path = r"C:\Program Files\Git\git-bash.exe"
        full_command = f'"{git_bash_path}" -c "ssh -o StrictHostKeyChecking=no -N {command}"'
        process = subprocess.Popen(
            full_command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"已启动代理: {full_command}")
        print(f"进程ID: {process.pid}")
        
        import time
        time.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"代理进程已退出，退出码: {process.returncode}")
            if stdout:
                print(f"标准输出: {stdout}")
            if stderr:
                print(f"错误输出: {stderr}")
            return None
        
        if is_first_proxy:
            time.sleep(2)
            import subprocess as sp
            result = sp.run(f'netstat -ano|findstr {dp1}', shell=True, capture_output=True, text=True)
            if 'LISTENING' in result.stdout:
                print(f"第一个代理端口 {dp1} 正在监听")
            else:
                print(f"警告: 第一个代理端口 {dp1} 未监听")
                stdout, stderr = process.communicate(timeout=5)
                if stdout:
                    print(f"标准输出: {stdout}")
                if stderr:
                    print(f"错误输出: {stderr}")
                return None
        
        return process
    except Exception as e:
        print(f"启动代理失败: {e}")
        return None

# Python实现的简单nc命令替代方案
def python_nc(host, port):
    """简单的nc命令替代，从标准输入读取数据并发送到指定主机和端口"""
    import sys
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # 双向传输数据
        def receive_from_socket():
            try:
                while True:
                    data = sock.recv(4096)
                    if not data:
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.flush()
            except:
                pass
        
        # 启动接收线程
        import threading
        recv_thread = threading.Thread(target=receive_from_socket)
        recv_thread.daemon = True
        recv_thread.start()
        
        # 从标准输入读取数据并发送
        while True:
            data = sys.stdin.buffer.read(4096)
            if not data:
                break
            sock.sendall(data)
    except Exception as e:
        print(f"python_nc error: {e}")
    finally:
        if 'sock' in locals():
            sock.close()

def start_second_proxy(host1, port1, dp1=20808, dp2=20809):
    try:
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(f'ssh -o "ProxyCommand connect -S 127.0.0.1:{dp1} %h %p" -D {dp2} -p {port1} root@{host1}\n')
            script_path = f.name
        
        git_bash_path = r"C:\Program Files\Git\git-bash.exe"
        full_proxy2_command = f'"{git_bash_path}" {script_path}'
        proxy2_command = f'ssh -o "ProxyCommand connect -S 127.0.0.1:{dp1} %h %p" -D {dp2} -p {port1} root@{host1}'
        
        print(f"已启动第二个代理: {full_proxy2_command}")
        
        process = subprocess.Popen(
            full_proxy2_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"进程ID: {process.pid}")
        
        import time
        time.sleep(10)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"代理进程已退出，退出码: {process.returncode}")
            if stdout:
                print(f"标准输出: {stdout}")
            if stderr:
                print(f"错误输出: {stderr}")
            return None, full_proxy2_command
        
        import subprocess as sp
        result = sp.run(f'netstat -ano|findstr {dp2}', shell=True, capture_output=True, text=True)
        if 'LISTENING' in result.stdout:
            print(f"第二个代理端口 {dp2} 正在监听")
        else:
            print(f"警告: 第二个代理端口 {dp2} 未监听")
            try:
                stdout, stderr = process.communicate(timeout=5)
                if stdout:
                    print(f"标准输出: {stdout}")
                if stderr:
                    print(f"错误输出: {stderr}")
            except subprocess.TimeoutExpired:
                pass
        
        return process, full_proxy2_command
    except Exception as e:
        print(f"启动第二个代理失败: {e}")
        return None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='创建双层SSH动态代理')
    parser.add_argument('public_url', help='公网地址，格式: tcp://host:port')
    parser.add_argument('host1', nargs='?', help='第二个代理的目标主机地址（可选，未提供时从配置文件读取或提示输入）')
    parser.add_argument('--port1', type=int, help='第二个代理的目标端口（可选，未提供时从配置文件读取或使用默认值22）', default=None)
    parser.add_argument('--dp1', type=int, help='第一个代理的本地监听端口，默认20808', default=20808)
    parser.add_argument('--dp2', type=int, help='第二个代理的本地监听端口，默认20809', default=20809)
    args = parser.parse_args()
    
    host, port = parse_tcp_url(args.public_url)
    
    saved_host1, saved_port1 = read_servers_config()
    
    if args.host1:
        host1 = args.host1
    elif saved_host1:
        host1 = saved_host1
        print(f"使用保存的目标主机: {host1}")
    else:
        try:
            host1 = input("请输入第二个代理的目标主机地址: ")
            if not host1.strip():
                print("错误: 目标主机地址不能为空")
                sys.exit(1)
        except EOFError:
            print("错误: 非交互式环境下必须提供host1参数")
            sys.exit(1)
    
    if args.port1 is not None:
        port1 = args.port1
    elif saved_port1:
        port1 = saved_port1
        print(f"使用保存的目标端口: {port1}")
    else:
        try:
            port_input = input("请输入第二个代理的目标端口（默认22）: ")
            port1 = int(port_input) if port_input.strip() else 22
        except EOFError:
            port1 = 22
            print(f"使用默认端口: {port1}")
    
    if not args.host1 or args.port1 is None:
        save_servers_config(host1, port1)
    
    dp1 = args.dp1
    dp2 = args.dp2
    
    proxy1_command = f'-D {dp1} -p {port} root@{host}'
    full_proxy1_command = f'ssh -o StrictHostKeyChecking=no -N -D {dp1} -p {port} root@{host}'
    
    print("正在启动第一个代理...")
    proxy1 = start_ssh_proxy(proxy1_command, is_first_proxy=True, dp1=dp1)
    
    if proxy1:
        import time
        print("\n等待第一个代理完全连接...")
        time.sleep(5)
        
        print("\n正在启动第二个代理...")
        proxy2, full_proxy2_command = start_second_proxy(host1, port1, dp1=dp1, dp2=dp2)
        
        if proxy2:
            print("\n所有代理已成功启动!")
            print("\n代理信息:")
            print(f"1. 第一个代理 (本地端口 {dp1}): {full_proxy1_command}")
            print(f"2. 第二个代理 (本地端口 {dp2}): {full_proxy2_command}")
            print("\n提示: 使用 Ctrl+C 停止脚本，代理进程将继续在后台运行")
            
            # 等待用户输入以保持脚本运行
            try:
                input("\n按 Enter 键退出...")
            except KeyboardInterrupt:
                pass
        else:
            print("启动第二个代理失败")
    else:
        print("启动第一个代理失败")
