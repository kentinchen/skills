---
name: cpolar-tunnel
version: 1.0.0
author: local
homepage: https://github.com/
skills: []
description: 通过cpolar隧道创建SSH代理，支持单层和双层代理链。通过登录cpolar仪表盘获取SSH隧道公网地址，创建动态代理实现网络穿透。
  触发条件：当用户需要查看隧道状态、获取SSH隧道URL、创建单层或双层代理连接、或把远端端口转发到本机（如 RDP 3389）时调用。
---

# cpolar-tunnel Skill

## 前置条件

- Python 3 已安装
- 安装所需依赖：
  ```bash
  pip install requests beautifulsoup4 pyyaml
  ```
- 用户已注册cpolar账号（用户名和密码）
- cpolar客户端已配置authtoken并运行
- 如需使用双层代理功能（twin_dynamic_proxy_script.py），需安装 Git Bash（路径：C:\Program Files\Git\git-bash.exe）

## 脚本说明

### 1. cpolar_ssh_public_url.py

登录cpolar官网仪表盘，提取SSH隧道的公网URL。支持自动保存和读取凭据到 `~/.cpolar/auth.yaml`。

### 2. dynamic_proxy_script.py

根据TCP公网地址创建SSH动态SOCKS代理。支持自定义本地监听端口（默认20808）。

### 3. twin_dynamic_proxy_script.py

创建双层SSH代理链，支持自定义参数配置。第一个代理连接cpolar隧道，第二个代理连接指定的目标主机，通过第一个代理转发流量。

### 4. port_forward_script.py

创建SSH本地端口转发（如把远端 3389 映射到本地 33895）。启动后会等待本地端口真正进入监听状态才判定成功，失败时输出 ssh 日志与诊断原因。

## 工作流程

### Phase 0: 检查依赖

检查Python和依赖是否已安装：

```bash
python --version
pip show requests beautifulsoup4 pyyaml
```

### Phase 1: 登录cpolar获取SSH隧道URL

**强制要求：必须且只能通过以下命令执行，禁止用任何其他方式替代。**

```bash
python scripts/cpolar_ssh_public_url.py [username] [password]
```

**执行要求：**

- 使用 Python 工具执行上述命令
- 用户名和密码为可选参数
- 如果未提供参数，脚本会自动从 `~/.cpolar/auth.yaml` 读取已保存的凭据
- 如果配置文件不存在，会提示用户输入凭据并自动保存
- 不得修改脚本、不得跳过脚本、不得在脚本执行前后自行补充任何 API 调用
- 如果脚本输出错误并退出，直接将错误信息返回给用户，不得尝试修复或绕过

**输出：**
脚本直接输出SSH隧道的公网URL（如 `tcp://xxx.cpolar.io:12345`）

### Phase 2: 建立代理或端口转发

**方式一：使用 dynamic_proxy_script.py（单层代理）**

```bash
python scripts/dynamic_proxy_script.py tcp://host:port [local_port]
```

**参数说明：**

- `tcp://host:port` - 公网地址，必填
- `local_port` - 本地监听端口，可选，默认20808

**方式三：使用 port_forward_script.py（本地端口转发）**

适用于把远端某个 TCP 服务（如 RDP 3389、数据库端口）映射到本机。

```bash
python scripts/port_forward_script.py tcp://host:port local_port:target_host:target_port
```

**参数说明：**

- `tcp://host:port` - 公网地址，必填（Phase 1 获取）
- `local_port:target_host:target_port` - 转发规则，必填，例如 `33895:172.63.132.33:3389`
- `-i/--identity` - SSH 私钥路径，可选
- `--timeout` - 等待端口监听的秒数，可选，默认 12
- `--stop local_port` - 结束指定端口的转发进程
- `--use-schtasks` - Windows 下改用计划任务托管 ssh（默认不用，见下方注意事项）

**执行要求：**

- 成功后输出 `127.0.0.1:<local_port> -> <target_host>:<target_port>`
- 脚本会等端口真正监听才算成功，失败时打印 ssh 日志与诊断原因
- 该脚本仅做本地端口转发，不做 SOCKS 代理

**验证转发是否真的通到目标服务（以 RDP 为例）：**

```python
import socket
s = socket.socket(); s.settimeout(8)
s.connect(('127.0.0.1', 33895))
# X.224 Connection Request，RDP 服务应回 03 00 00 13 ...
s.sendall(bytes([0x03,0x00,0x00,0x13,0x0e,0xe0,0x00,0x00,0x00,0x00,0x00,
                 0x01,0x00,0x08,0x00,0x03,0x00,0x00,0x00]))
print(s.recv(64).hex())
```

**方式二：使用 twin_dynamic_proxy_script.py（双层代理链）**

```bash
python scripts/twin_dynamic_proxy_script.py tcp://host:port host1 [--port1 port1] [--dp1 dp1] [--dp2 dp2]
```

**参数说明：**

- `tcp://host:port` - 公网地址，必填
- `host1` - 第二个代理的目标主机地址，必填
- `--port1` - 第二个代理的目标端口，可选，默认22
- `--dp1` - 第一个代理的本地监听端口，可选，默认20808
- `--dp2` - 第二个代理的本地监听端口，可选，默认20809

**执行要求：**

- 将 `tcp://host:port` 替换为Phase 1获取的SSH隧道地址
- `host1` 为必填参数，指定第二个代理要连接的目标主机
- 需要 Git Bash 支持
- 双层代理结构：应用 → 127.0.0.1:dp2 → 127.0.0.1:dp1 → cpolar隧道 → 目标网络

### Phase 3: 解析输出

脚本返回以下信息：

| 脚本                           | 输出信息                           |
|------------------------------|--------------------------------|
| cpolar_ssh_public_url.py     | SSH隧道公网URL（tcp://格式），首次使用会保存凭据 |
| dynamic_proxy_script.py      | 代理创建状态，监听端口（默认20808或自定义）       |
| twin_dynamic_proxy_script.py | 双层代理信息，自定义端口和目标主机              |
| port_forward_script.py       | 本地转发端口、进程ID、日志路径；失败时附 ssh 日志与诊断 |

### Phase 4: 展示结果

将解析后的隧道信息和代理状态以友好的格式展示给用户

## 示例

**获取SSH隧道URL（首次使用）：**

```bash
python scripts/cpolar_ssh_public_url.py user@example.com password123
```

**输出示例：**

```
tcp://abc123.cpolar.io:12345
凭据已保存到: C:\Users\用户名\.cpolar\auth.yaml
```

**获取SSH隧道URL（后续使用，自动读取凭据）：**

```bash
python scripts/cpolar_ssh_public_url.py
```

**输出示例：**

```
使用保存的用户名: user@example.com
使用保存的密码
tcp://abc123.cpolar.io:12345
```

**创建SSH代理（使用默认端口20808）：**

```bash
python scripts/dynamic_proxy_script.py tcp://abc123.cpolar.io:12345
```

**输出示例：**

```
正在创建SSH动态代理: ssh -o StrictHostKeyChecking=no -D 20808 -p 12345 root@abc123.cpolar.io
SSH动态代理已在后台启动
```

**创建SSH代理（使用自定义端口8888）：**

```bash
python scripts/dynamic_proxy_script.py tcp://abc123.cpolar.io:12345 8888
```

**输出示例：**

```
正在创建SSH动态代理: ssh -o StrictHostKeyChecking=no -D 8888 -p 12345 root@abc123.cpolar.io
SSH动态代理已在后台启动
```

**创建双层SSH代理链：**

```bash
python scripts/twin_dynamic_proxy_script.py tcp://abc123.cpolar.io:12345 192.168.1.100
```

**输出示例：**

```
正在启动第一个代理...
已启动代理: "C:\Program Files\Git\git-bash.exe" -c "ssh -o StrictHostKeyChecking=no -N -D 20808 -p 12345 root@abc123.cpolar.io"
进程ID: 2764
第一个代理端口 20808 正在监听

等待第一个代理完全连接...

正在启动第二个代理...
已启动第二个代理: "C:\Program Files\Git\git-bash.exe" temp_script.sh
进程ID: 37044
第二个代理端口 20809 正在监听

所有代理已成功启动!

代理信息:
1. 第一个代理 (本地端口 20808): ssh -o StrictHostKeyChecking=no -N -D 20808 -p 12345 root@abc123.cpolar.io
2. 第二个代理 (本地端口 20809): ssh -o "ProxyCommand connect -S 127.0.0.1:20808 %h %p" -D 20809 -p 22 root@172.61.143.237
```

**创建双层SSH代理链（自定义参数）：**

```bash
python scripts/twin_dynamic_proxy_script.py tcp://abc123.cpolar.io:12345 172.61.143.237 --port1 22 --dp1 8888 --dp2 8889
```

**创建本地端口转发（远端 RDP 映射到本地 33895）：**

```bash
python scripts/port_forward_script.py tcp://abc123.cpolar.io:12345 33895:172.63.132.33:3389
```

**输出示例：**

```
正在创建SSH本地端口转发: C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -L 33895:172.63.132.33:3389 -N -p 12345 root@abc123.cpolar.io
转发规则: 127.0.0.1:33895 -> 172.63.132.33:3389 (通过 abc123.cpolar.io:12345)
SSH本地端口转发已在后台启动
进程ID: 17120
现在可以通过访问 127.0.0.1:33895 来访问 172.63.132.33:3389
日志: C:\Users\用户名\.cpolar\forward_33895.log
停止转发: python port_forward_script.py --stop 33895
```

**结束转发：**

```bash
python scripts/port_forward_script.py --stop 33895
```

## 注意事项

- 用户名和密码是敏感信息，请勿泄露
- 凭据自动保存到 `~/.cpolar/auth.yaml`，后续使用无需重新输入
- 登录失败可能原因：用户名密码错误、CSRF token获取失败、网络问题
- 如果未找到SSH隧道，需要先在cpolar仪表盘创建SSH隧道
- twin_dynamic_proxy_script.py 需要安装 Git Bash（路径：C:\Program Files\Git\git-bash.exe）
- 默认代理端口：20808（单层），20808/20809（双层）
- 可使用 `-d` 参数启用debug模式查看详细日志
- 双层代理链使用方法：将SOCKS5代理设置为第二个代理的端口（默认20809）
- twin_dynamic_proxy_script.py 需要提供第二个代理的目标主机地址（host1参数）

### 运行环境注意（Windows / 受限沙箱）

1. **Python 依赖**：需要 `requests`、`beautifulsoup4`、`pyyaml`。如果当前解释器缺包，先检查是否有其他已装好依赖的 Python 可用，避免重复安装。
2. **`schtasks` 可能被安全策略拦截**：`port_forward_script.py` 默认不再使用计划任务托管 ssh，改用 `DETACHED_PROCESS` 让进程脱离父进程树。若环境禁止创建脱离进程，转发会在会话结束后失效——此时需要用户手工在终端执行 ssh 命令保持前台运行。
3. **沙箱禁止读取 `~/.ssh`**：表现为 `Load key "...id_rsa": Permission denied` + `Permission denied (publickey...)`。这不是密钥本身的问题，而是文件读取被拦。需要在允许访问 `~/.ssh` 的环境下执行。
4. **不要依赖“进程存活”判断成功**：ssh 卡在交互式密码提示时进程存活、TCP 已建连，但本地端口不监听。以 `port_forward_script.py` 的监听自检结果为准，或直接 `netstat -ano | findstr :<port>`。
5. **隧道地址会变**：cpolar 免费隧道重启后 `tcp://` 地址的端口可能变化，转发失效时先重新执行 `cpolar_ssh_public_url.py`。

## 错误处理

| 错误场景           | 处理方式                                                |
|----------------|-----------------------------------------------------|
| 依赖未安装          | 提示用户执行 `pip install requests beautifulsoup4 pyyaml` |
| 登录失败           | 提示用户检查用户名密码是否正确                                     |
| 无法获取CSRF token | 提示用户网络问题或cpolar页面结构变更                               |
| 未找到SSH隧道       | 提示用户先在cpolar仪表盘创建SSH隧道                              |
| SSH连接失败        | 提示用户检查网络连接或隧道状态                                     |
| Git Bash未安装    | 提示用户安装Git或使用dynamic_proxy_script.py                 |
| 双层代理启动失败       | 检查第一层代理是否正常运行，确保端口已监听                               |
| host1参数缺失      | 提示用户必须提供第二个代理的目标主机地址                                |
| 本地端口已被占用       | 换一个端口，或先 `--stop` 结束旧转发                             |
| `Load key ... Permission denied` | ssh 无法读取 `~/.ssh`，检查文件权限或沙箱是否放行该目录          |
| 进程存活但端口不监听     | 查看 `~/.cpolar/forward_<port>.log`，多为认证失败或卡在密码提示         |
| `schtasks` 被安全策略拦截 | 去掉 `--use-schtasks`（默认即不使用），改用 DETACHED_PROCESS 方式 |