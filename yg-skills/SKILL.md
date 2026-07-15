---
name: yg-notice-list
version: 1.0.0
description: |
  查询YG系统通知清单，支持自动登录获取token，token失效时自动重新登录。
  触发条件：当用户需要查询通知清单、公告列表时调用。
---

# YG通知清单 Skill

## 前置条件

- Python 3 已安装
- 安装所需依赖：
  ```bash
  pip install requests pycryptodome pyyaml
  ```
- 已配置 `~/.yg-skills/config.yml` 文件，包含用户名、密码等配置
- ddddocr-fastapi 服务已启动（用于验证码识别）

## 脚本说明

### notice_list.py
查询YG系统通知清单的脚本，功能包括：
- 自动登录获取token
- token失效时自动重新登录
- 查询通知清单接口
- 支持分页查询和多种通知类型

## 工作流程

### Phase 0: 检查依赖

检查Python和依赖是否已安装：
```bash
python --version
pip show requests pycryptodome pyyaml
```

### Phase 1: 查询通知清单

**强制要求：必须且只能通过以下命令执行，禁止用任何其他方式替代。**

```bash
python scripts/notice_list.py [--page-num <页码>] [--page-size <每页大小>] [--notice-type <通知类型>] [--no-token] [--force-login]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --page-num, --pageNum | 页码 | 1 |
| --page-size, --pageSize | 每页大小 | 5 |
| --notice-type, --noticeType | 通知类型：1-普通公告，2-安全情报，3-资源变化 | 1 |
| --no-token | 不使用token调用接口（noToken接口） | 否 |
| --force-login | 强制重新登录获取新token | 否 |

**执行要求：**
- 使用 Python 工具执行上述命令
- 不得修改脚本、不得跳过脚本、不得在脚本执行前后自行补充任何 API 调用
- 如果脚本输出错误并退出，直接将错误信息返回给用户，不得尝试修复或绕过

**输出：**
脚本直接输出JSON格式的API响应结果

### Phase 2: 解析输出

脚本返回以下信息：

```json
{
  "msg": "成功",
  "total": 100,
  "code": 200,
  "success": true,
  "pageSize": 5,
  "rows": [
    {
      "createBy": "admin",
      "createTime": "2026-07-15 10:00:00",
      "title": "公告标题",
      "content": "公告内容",
      "noticeType": 1
    }
  ]
}
```

### Phase 3: 展示结果

将解析后的通知列表以友好的格式展示给用户

## 配置文件

配置文件路径：`~/.yg-skills/config.yml`

```yaml
username: your_username
password: your_password
sso_url: http://172.60.142.10
app_url: http://172.60.142.10
proxy: socks5://127.0.0.1:20808
app_code: 2a06bab333f5257deb664b8b16a30f23
login_device_info: a8799d06d5e4b4bf4b8efe54b5086f7c
```

## 示例

**查询普通公告（默认参数）：**
```bash
python scripts/notice_list.py
```

**查询安全情报，每页10条：**
```bash
python scripts/notice_list.py --notice-type 2 --page-size 10
```

**强制重新登录后查询：**
```bash
python scripts/notice_list.py --force-login
```

**输出示例：**
```json
{
  "msg": "成功",
  "total": 10,
  "code": 200,
  "success": true,
  "pageSize": 5,
  "rows": [
    {
      "createBy": "system",
      "createTime": "2026-07-15 09:30:00",
      "title": "系统维护通知",
      "content": "系统将于今晚22:00进行维护升级",
      "noticeType": 1
    },
    {
      "createBy": "admin",
      "createTime": "2026-07-15 10:15:00",
      "title": "安全预警",
      "content": "发现异常登录行为，请及时修改密码",
      "noticeType": 2
    }
  ]
}
```

## 注意事项

- 首次运行时需要确保配置文件已正确配置
- 脚本会自动处理token的获取和刷新
- 当token失效时（返回401），脚本会自动重新登录获取新token
- OCR服务配置需在 `~/.dddd-ocr/config.yml` 中配置

## 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 依赖未安装 | 提示用户执行 `pip install requests pycryptodome pyyaml` |
| 配置文件不存在 | 提示用户先运行登录脚本配置 |
| 用户名或密码错误 | 提示用户检查配置文件 |
| OCR服务不可达 | 提示用户检查ddddocr-fastapi服务是否启动 |
| token失效 | 自动重新登录获取新token |