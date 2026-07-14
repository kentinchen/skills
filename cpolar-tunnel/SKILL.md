---
name: cpolar-status
version: 1.0.0
description: |
  查询cpolar隧道信息并创建SSH代理。通过登录cpolar仪表盘获取SSH隧道公网地址，并创建动态代理实现网络穿透。
  触发条件：当用户需要查看隧道状态、获取SSH隧道URL、创建代理连接时调用。
---

# cpolar-status Skill

## 前置条件

- Python 3 已安装
- 安装所需依赖：
  ```bash
  pip install requests beautifulsoup4 pyyaml
  ```
- 用户已注册cpolar账号（用户名和密码）
- cpolar客户端已配置authtoken并运行
- 如需使用双层代理功能（proxy_manager.py），需安装 Git Bash

## 脚本说明

### 1. cpolar_ssh_public_url.py
登录cpolar官网仪表盘，提取SSH隧道的公网URL。支持自动保存和读取凭据到 `~/.cpolar/auth.yaml`。

### 2. dynamic_proxy_script.py
根据TCP公网地址创建SSH动态SOCKS代理。支持自定义本地监听端口。

### 3. proxy_manager.py
高级代理管理，创建双层SSH代理链（需Git Bash）。

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

### Phase 2: 创建SSH动态代理

**方式一：使用 dynamic_proxy_script.py**

```bash
python scripts/dynamic_proxy_script.py tcp://host:port [local_port]
```

**参数说明：**
- `tcp://host:port` - 公网地址，必填
- `local_port` - 本地监听端口，可选，默认20808

**方式二：使用 proxy_manager.py（双层代理）**

```bash
python scripts/proxy_manager.py tcp://host:port
```

**执行要求：**
- 将 `tcp://host:port` 替换为Phase 1获取的SSH隧道地址
- proxy_manager.py 需要 Git Bash 支持

### Phase 3: 解析输出

脚本返回以下信息：

| 脚本 | 输出信息 |
|------|----------|
| cpolar_ssh_public_url.py | SSH隧道公网URL（tcp://格式），首次使用会保存凭据 |
| dynamic_proxy_script.py | 代理创建状态，监听端口（默认20808或自定义） |
| proxy_manager.py | 双层代理信息，端口20808和20809 |

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

## 注意事项

- 用户名和密码是敏感信息，请勿泄露
- 凭据自动保存到 `~/.cpolar/auth.yaml`，后续使用无需重新输入
- 登录失败可能原因：用户名密码错误、CSRF token获取失败、网络问题
- 如果未找到SSH隧道，需要先在cpolar仪表盘创建SSH隧道
- proxy_manager.py 需要安装 Git Bash（路径：C:\Program Files\Git\git-bash.exe）
- 默认代理端口：20808（单层），20808/20809（双层）
- 可使用 `-d` 参数启用debug模式查看详细日志

## 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 依赖未安装 | 提示用户执行 `pip install requests beautifulsoup4 pyyaml` |
| 登录失败 | 提示用户检查用户名密码是否正确 |
| 无法获取CSRF token | 提示用户网络问题或cpolar页面结构变更 |
| 未找到SSH隧道 | 提示用户先在cpolar仪表盘创建SSH隧道 |
| SSH连接失败 | 提示用户检查网络连接或隧道状态 |
| Git Bash未安装 | 提示用户安装Git或使用dynamic_proxy_script.py |