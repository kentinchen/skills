import subprocess
import sys
import re

def create_ssh_proxy(tcp_address, local_port=20808):
    # 解析公网地址，提取主机和端口
    pattern = r'tcp://([^:]+):(\d+)'
    match = re.match(pattern, tcp_address)
    if not match:
        print("无效的公网地址格式，请使用 tcp://host:port 格式")
        return False
    
    host = match.group(1)
    port = match.group(2)
    
    # 构建SSH命令
    ssh_command = f'ssh -o StrictHostKeyChecking=no -D {local_port} -p {port} root@{host}'
    
    print(f"正在创建SSH动态代理: {ssh_command}")
    
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
        return True
    except Exception as e:
        print(f"创建代理失败: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("用法: python dynamic_proxy_script.py tcp://host:port [local_port]")
        print("参数说明:")
        print("  tcp://host:port    公网地址，必填")
        print("  local_port         本地监听端口，可选，默认20808")
        sys.exit(1)
    
    tcp_address = sys.argv[1]
    local_port = int(sys.argv[2]) if len(sys.argv) == 3 else 20808
    create_ssh_proxy(tcp_address, local_port)
