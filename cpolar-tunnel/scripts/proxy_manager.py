import argparse
import subprocess
import re
import sys
import socket
import threading

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

# 启动SSH动态代理（使用git-bash）
def start_ssh_proxy(command, is_first_proxy=False):
    try:
        # 使用git-bash启动SSH代理
        git_bash_path = r"C:\Program Files\Git\git-bash.exe"
        # 构建完整的git-bash命令，确保路径被正确引用
        full_command = f'"{git_bash_path}" -c "ssh -o StrictHostKeyChecking=no -N {command}"'
        # 在后台启动进程
        process = subprocess.Popen(
            full_command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"已启动代理: {full_command}")
        print(f"进程ID: {process.pid}")
        
        # 等待几秒钟，检查进程是否还在运行
        import time
        time.sleep(3)  # 增加等待时间
        
        # 检查进程状态
        if process.poll() is not None:
            # 进程已经退出，获取错误信息
            stdout, stderr = process.communicate()
            print(f"代理进程已退出，退出码: {process.returncode}")
            if stdout:
                print(f"标准输出: {stdout}")
            if stderr:
                print(f"错误输出: {stderr}")
            return None
        
        # 对于第一个代理，检查端口是否正在监听
        if is_first_proxy:
            time.sleep(2)  # 再等待一下确保端口已经开始监听
            import subprocess as sp
            result = sp.run('netstat -ano|findstr 20808', shell=True, capture_output=True, text=True)
            if 'LISTENING' in result.stdout:
                print("第一个代理端口 20808 正在监听")
            else:
                print("警告: 第一个代理端口 20808 未监听")
                # 尝试获取更多错误信息
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

# 启动第二个代理（使用git-bash和原始的ProxyCommand命令）
def start_second_proxy():
    try:
        # 使用git-bash启动第二个代理
        git_bash_path = r"C:\Program Files\Git\git-bash.exe"
        # 构建第二个代理命令，使用connect命令
        proxy2_command = f'ssh -o "ProxyCommand connect -S 127.0.0.1:20808 %h %p" -D 20809 root@172.61.143.237'
        full_proxy2_command = f'"{git_bash_path}" -c "{proxy2_command}"'
        
        print(f"已启动第二个代理: {full_proxy2_command}")
        
        # 启动SSH代理
        process = subprocess.Popen(
            full_proxy2_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"进程ID: {process.pid}")
        
        # 等待几秒钟，检查进程是否还在运行
        import time
        time.sleep(10)  # 增加等待时间，确保第一个代理完全连接好
        
        # 检查进程状态
        if process.poll() is not None:
            # 进程已经退出，获取错误信息
            stdout, stderr = process.communicate()
            print(f"代理进程已退出，退出码: {process.returncode}")
            if stdout:
                print(f"标准输出: {stdout}")
            if stderr:
                print(f"错误输出: {stderr}")
            return None, full_proxy2_command
        
        # 检查20809端口是否正在监听
        import subprocess as sp
        result = sp.run('netstat -ano|findstr 20809', shell=True, capture_output=True, text=True)
        if 'LISTENING' in result.stdout:
            print("第二个代理端口 20809 正在监听")
        else:
            print("警告: 第二个代理端口 20809 未监听")
            # 尝试获取更多错误信息
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
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='创建SSH动态代理')
    parser.add_argument('public_url', help='公网地址，格式: tcp://host:port')
    args = parser.parse_args()
    
    # 解析公网地址
    host, port = parse_tcp_url(args.public_url)
    
    # 构建第一个代理命令
    proxy1_command = f'-D 20808 -p {port} root@{host}'
    full_proxy1_command = f'ssh -o StrictHostKeyChecking=no -N -D 20808 -p {port} root@{host}'
    
    print("正在启动第一个代理...")
    proxy1 = start_ssh_proxy(proxy1_command, is_first_proxy=True)
    
    if proxy1:
        # 等待第一个代理完全连接好
        import time
        print("\n等待第一个代理完全连接...")
        time.sleep(5)
        
        print("\n正在启动第二个代理...")
        proxy2, full_proxy2_command = start_second_proxy()
        
        if proxy2:
            print("\n所有代理已成功启动!")
            print("\n代理信息:")
            print(f"1. 第一个代理 (本地端口 20808): {full_proxy1_command}")
            print(f"2. 第二个代理 (本地端口 20809): {full_proxy2_command}")
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
