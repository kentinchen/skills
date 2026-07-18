---
name: yw-services
version: 1.0.0
description: |
  yw系统综合服务，支持SSO登录、查询待办工单、系统清单等功能。
  触发条件：当用户需要登录yw系统或查询yw系统的工单、系统清单等信息时调用。
---

# yw系统服务 Skill

## 前置条件

- Python 3 已安装
- 安装所需依赖：
  ```bash
  pip install requests pycryptodome pyyaml
  ```
- 已配置 `~/.yw-skills/config.yml` 文件，包含用户名、密码等配置
- ddddocr-fastapi 服务已启动（用于验证码识别）

## 服务列表

| 服务 | 脚本 | 功能 |
|------|------|------|
| SSO登录 | yw_login.py | 执行SSO登录，获取token |
| 基础服务 | yw_base.py | yw系统基础类，封装API调用 |
| 工单服务 | task_service.py | 查询待办工单数量、已办工单、工单动作表、处理记录 |

## 配置文件

配置文件路径：`~/.yw-skills/config.yml`

```yaml
username: your_username
password: your_password
sso_url: http://172.60.142.10
app_url: http://172.60.142.10
proxy: socks5://127.0.0.1:20808
app_code: 2a06bab333f5257deb664b8b16a30f23
login_device_info: a8799d06d5e4b4bf4b8efe54b5086f7c
tenant_code: aipuxjgmbqhbprui.clouds-work
```

## SSO登录

### 执行登录

```bash
python scripts/yw_login.py [--proxy <代理地址>] [--sso-url <SSO地址>] [--username <用户名>] [--password <密码>] [--app-url <APP地址>] [--app-code <APP_CODE>] [--login-device-info <设备信息>] [--ocr-server <OCR地址>] [--force-login]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --proxy | 代理地址 | 从配置文件读取 |
| --sso-url, --sso_url | SSO服务地址 | http://172.60.142.10 |
| --username | 用户名 | 从配置文件读取 |
| --password | 密码 | 从配置文件读取 |
| --app-url, --app_url | APP服务地址 | http://172.60.142.10 |
| --app-code, --app_code | APP_CODE | 2a06bab333f5257deb664b8b16a30f23 |
| --login-device-info, --login_device_info | LOGIN_DEVICE_INFO | a8799d06d5e4b4bf4b8efe54b5086f7c |
| --ocr-server, --ocr_server | OCR服务地址 | http://localhost:8000 |
| --force-login, --force_login | 强制重新登录 | False |

**登录流程：**

1. 获取验证码（GET /verify-server/kaptcha/generate）
2. 识别验证码（调用OCR服务）
3. 执行登录（POST /sso-server/wmh/Internal/users）
4. 保存token到配置文件

**登录成功返回：**

```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "sso_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": "8054ce387f0b4472",
  "message": "登录成功"
}
```

## 工单服务

### 查询待办工单数量（未完成工单数）

```bash
python scripts/task_service.py --type todo_count [--view-id <视图ID>]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --type | 查询类型：todo_count（待办数量） | todo_count |
| --view-id, --viewId | 视图ID | MY_TODO |

**示例：**
```bash
python scripts/task_service.py --type todo_count
```

**返回示例：**
```json
{
  "data": 5,
  "code": 200,
  "success": true
}
```

### 查询已办工单

```bash
python scripts/task_service.py --type handled [--view-id <视图ID>]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --type | 查询类型：handled（已办工单） | - |
| --view-id, --viewId | 视图ID | MY_HANDLER |

### 查询工单动作表

```bash
python scripts/task_service.py --type action_map
```

### 查询处理记录

```bash
python scripts/task_service.py --type history --work-order-id <工单ID> --current-node-id <节点ID> [--data-types <数据类型>]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --type | 查询类型：history（处理记录） | - |
| --work-order-id, --workOrderId | 工单ID（必填） | - |
| --current-node-id, --currentNodeId | 当前节点ID（必填） | - |
| --data-types, --dataTypes | 数据类型列表 | approve modify history counterSigned |

## API调用

yw系统API需要通过Cookie和Authentication header进行认证：

**Cookie格式：**
```
auth_token_key=<auth_token_key>; sso_token=<sso_token>; YH-TOKEN=<token>; JSESSIONID=<jsessionid>
```

**Authentication格式：**
```
Bearer <sso_token>
```

**其他必要headers：**
- `language`: zh
- `noviceGuidance`: false
- `tenant-code`: <租户编码>

## 可用API

### 查询待办工单数量

```python
from yw_base import YwBase

yw = YwBase()
yw.get_token()
result = yw.get_todo_count(view_id="MY_TODO")
```

### 查询已办工单

```python
from yw_base import YwBase

yw = YwBase()
yw.get_token()
result = yw.get_handled_workorders(view_id="MY_HANDLER")
```

### 查询工单动作表

```python
from yw_base import YwBase

yw = YwBase()
yw.get_token()
result = yw.get_action_map()
```

### 查询处理记录

```python
from yw_base import YwBase

yw = YwBase()
yw.get_token()
result = yw.get_workorder_history(
    work_order_id="59d73ef734a441fdb9c254ce74657a5e",
    current_node_id="EndEvent_1k8gkqf",
    data_types=["approve", "modify", "history", "counterSigned"]
)
```

### 查询系统清单

```python
from yw_base import YwBase

yw = YwBase()
yw.get_token()
result = yw.get_system_list()
```

## 执行要求

- 使用 Python 工具执行上述命令
- 不得修改脚本、不得跳过脚本、不得在脚本执行前后自行补充任何 API 调用
- 如果脚本输出错误并退出，直接将错误信息返回给用户，不得尝试修复或绕过

## 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 依赖未安装 | 提示用户执行 `pip install requests pycryptodome pyyaml` |
| 配置文件不存在 | 提示用户先运行登录脚本配置 |
| 用户名或密码错误 | 提示用户检查配置文件 |
| OCR服务不可达 | 提示用户检查ddddocr-fastapi服务是否启动 |
| token失效 | 自动重新登录获取新token |

## 示例

**执行登录：**
```bash
python scripts/yw_login.py --username 18208151273 --password your_password --force-login
```

**使用保存的配置登录：**
```bash
python scripts/yw_login.py
```

**强制重新登录：**
```bash
python scripts/yw_login.py --force-login
```

**查询未完成工单数：**
```bash
python scripts/task_service.py --type todo_count
```

**查询已办工单：**
```bash
python scripts/task_service.py --type handled
```

**查询工单动作表：**
```bash
python scripts/task_service.py --type action_map
```

**查询处理记录：**
```bash
python scripts/task_service.py --type history --work-order-id "59d73ef734a441fdb9c254ce74657a5e" --current-node-id "EndEvent_1k8gkqf"
```